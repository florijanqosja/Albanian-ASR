import asyncio
import datetime as _dt
import io
import json
import logging
import math
import os
import uuid
import fcntl
from contextlib import asynccontextmanager
from typing import Optional, Tuple, Union

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    Request,
)
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from sqlalchemy.orm import Session
from sqlalchemy import func, select
import sqlalchemy as _sql

from .database import schemas as _schemas
from .database import services as _services
from .database import models as _models
from .database.enums import MediaProcessingStatus
from .routers import auth, users, support, consents
from .services import segmentation as _segmentation
from .utils.paths import (
    BASE_DIR,
    IS_PRODUCTION,
    SPLICES_DIR,
    SPLICES_DIR_ABS,
    UPLOAD_DIR_MP3,
    UPLOAD_DIR_MP3_ABS,
    UPLOAD_DIR_MP4,
    UPLOAD_DIR_MP4_ABS,
    get_public_path,
)
from .docs import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    CONTACT_INFO,
    LICENSE_INFO,
    TAGS_METADATA,
    TERMS_OF_SERVICE,
    configure_documentation,
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants - Use absolute paths in production (Docker), relative in development
API_ROOT_PATH = os.getenv("API_ROOT_PATH", "")
DEFAULT_TEXT_SPLICE_PROMPTS = [f"sample{i}" for i in range(1, 11)]
DEFAULT_CONSENT_VERSION = os.getenv("DEFAULT_CONSENT_VERSION", "2025-12-19")
DEFAULT_CONSENT_EFFECTIVE_DATE = os.getenv("DEFAULT_CONSENT_EFFECTIVE_DATE", "2025-12-19")
DEFAULT_PRIVACY_CONTENT = os.getenv(
    "DEFAULT_PRIVACY_CONTENT",
    "Initial privacy notice snapshot for DibraSpeaks (see /privacy for full text).",
)
DEFAULT_TERMS_CONTENT = os.getenv(
    "DEFAULT_TERMS_CONTENT",
    "Initial terms snapshot for DibraSpeaks (see /termsandservices for full text).",
)

SAMPLE_FILE_PATH = "sample_audio_njerez_dhe_fate_e2.mp3"
DOCKER_SAMPLE_PATH = "/code/sample_audio_njerez_dhe_fate_e2.mp3"

# Bound how many media files a single worker processes at once. Segmentation is CPU-bound
# and each job commits a batch of splices (a DB connection), so unbounded concurrency
# exhausted the SQLAlchemy pool under upload bursts. This limit is PER WORKER PROCESS, so
# the effective global limit is PROCESSING_CONCURRENCY * (uvicorn --workers). Keep it <=
# the engine pool_size (see api/database/database.py) so processing never forces overflow.
# Clamp to >= 1: a value of 0 would make Semaphore.acquire() block forever, and a
# non-numeric value would crash-loop the worker at import.
try:
    PROCESSING_CONCURRENCY = max(1, int(os.getenv("PROCESSING_CONCURRENCY", "2")))
except ValueError:
    PROCESSING_CONCURRENCY = 2

# The limiter is built lazily on first use, inside the running event loop, on purpose:
# on Python 3.9 an asyncio.Semaphore binds to its event loop at construction time, so
# building it at import (no running loop) would bind to the wrong loop and raise
# "got Future attached to a different loop" the instant the limit is first hit under load.
# We also remember which loop it was built on and rebuild it if the running loop changes,
# so a process that runs more than one event-loop lifecycle (e.g. tests spinning the app
# up repeatedly) never awaits a semaphore bound to a dead loop.
_processing_limiter: Optional["asyncio.Semaphore"] = None
_processing_limiter_loop: Optional["asyncio.AbstractEventLoop"] = None


def _get_processing_limiter() -> "asyncio.Semaphore":
    """Return the per-worker media-processing concurrency limiter, creating it on first
    use (and re-creating it if the running event loop has changed) so it always binds to
    the live serving loop rather than an import-time or torn-down loop. Safe under
    asyncio's single-threaded scheduling: the check-and-set has no await, so it cannot
    race."""
    global _processing_limiter, _processing_limiter_loop
    loop = asyncio.get_running_loop()
    if _processing_limiter is None or _processing_limiter_loop is not loop:
        _processing_limiter = asyncio.Semaphore(PROCESSING_CONCURRENCY)
        _processing_limiter_loop = loop
    return _processing_limiter

# In development, ensure directories exist. In production, entrypoint.sh handles this.
if not IS_PRODUCTION:
    for directory in [UPLOAD_DIR_MP4, UPLOAD_DIR_MP3, SPLICES_DIR]:
        os.makedirs(directory, exist_ok=True)

logger.info(f"Running in {'production' if IS_PRODUCTION else 'development'} mode")
logger.info(f"Static file directories: mp4={UPLOAD_DIR_MP4_ABS}, mp3={UPLOAD_DIR_MP3_ABS}, splices={SPLICES_DIR_ABS}")


def _normalize_video_name(video_name: str) -> str:
    """
    Normalize a user-provided media name for use as a directory component.
    
    Parameters:
    	video_name (str): Media name to normalize.
    
    Returns:
    	str: A sanitized, non-empty directory name with reserved recording names prefixed by "v_".
    """
    normalized_name = str(video_name).replace(" ", "_")
    normalized_name = "".join(x for x in normalized_name if x.isalnum() or x in "._-")
    normalized_name = normalized_name.strip("._-")
    if not normalized_name:
        normalized_name = f"upload_{uuid.uuid4().hex[:12]}"
    if normalized_name.startswith("recordings_"):
        normalized_name = f"v_{normalized_name}"
    return normalized_name


def _persist_media_file(
    video_name: str,
    filename: str,
    file_content: bytes,
) -> Tuple[str, str, str, str, str, Optional[str]]:
    """
    Persist an MP4 or MP3 upload and determine its related media paths.
    
    Parameters:
    	video_name (str): Name used to derive the media directory.
    	filename (str): Original uploaded filename.
    	file_content (bytes): Media data to write to disk.
    
    Returns:
    	Tuple[str, str, str, str, str, Optional[str]]: Normalized name, sanitized filename, extension, stored file path, MP3 path, and MP4 path.
    
    Raises:
    	HTTPException: If the filename extension is not `.mp4` or `.mp3`.
    """

    normalized_name = _normalize_video_name(video_name)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".mp4", ".mp3"]:
        raise HTTPException(status_code=400, detail="Invalid document type. Only .mp4 and .mp3 are supported.")

    safe_filename = "".join(x for x in filename if x.isalnum() or x in "._-")
    mp4_path: Optional[str] = None
    mp3_path: Optional[str] = None

    if ext == ".mp4":
        mp4_dir = os.path.join(UPLOAD_DIR_MP4, normalized_name)
        os.makedirs(mp4_dir, exist_ok=True)
        file_location = os.path.join(mp4_dir, safe_filename)
        mp4_path = file_location

        mp3_dir = os.path.join(UPLOAD_DIR_MP3, normalized_name)
        os.makedirs(mp3_dir, exist_ok=True)
        mp3_path = os.path.join(mp3_dir, safe_filename.replace(".mp4", ".mp3"))
    else:
        mp3_dir = os.path.join(UPLOAD_DIR_MP3, normalized_name)
        os.makedirs(mp3_dir, exist_ok=True)
        file_location = os.path.join(mp3_dir, safe_filename)
        mp3_path = file_location

    with open(file_location, "wb+") as destination:
        destination.write(file_content)

    return normalized_name, safe_filename, ext, file_location, mp3_path, mp4_path

def _convert_mp4_to_mp3(mp4_path: str, mp3_path: str) -> None:
    """
    Convert an MP4 video file to an MP3 audio file.
    
    Raises:
        HTTPException: If conversion fails, with status code 500 and error details.
    """
    try:
        logger.info(f"Converting {mp4_path} to {mp3_path}")
        video = VideoFileClip(mp4_path)
        # logger=None suppresses moviepy's stdout progress bar
        video.audio.write_audiofile(mp3_path, logger=None)
        video.close()
    except Exception as e:
        logger.error(f"Error converting mp4 to mp3: {e}")
        raise HTTPException(status_code=500, detail=f"Audio conversion failed: {str(e)}")


def _store_recorded_audio(user_id: Union[uuid.UUID, str], audio_bytes: bytes) -> Tuple[str, str, float]:
    """
    Store an uploaded audio blob as a WAV file in the user's splice directory.
    
    Parameters:
        user_id (uuid.UUID | str): Identifier of the user; used to create/locate the user's splice directory.
        audio_bytes (bytes): Raw audio file bytes (any format supported by pydub/ffmpeg).
    
    Returns:
        tuple: (file_path, filename, duration_seconds)
            file_path (str): Full filesystem path to the exported WAV file.
            filename (str): Filename of the exported WAV file (e.g., "recording_<token>.wav").
            duration_seconds (float): Duration of the stored audio in seconds.
    
    Raises:
        ValueError: If the provided audio payload is empty.
        ValueError: If the audio format is unsupported or cannot be decoded.
    """
    if not audio_bytes:
        raise ValueError("Audio payload is empty")

    user_dir = os.path.join(SPLICES_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
    except Exception as exc:  # pragma: no cover - depends on ffmpeg codecs
        raise ValueError("Unsupported audio format") from exc

    duration_seconds = len(audio_segment) / 1000.0
    file_token = uuid.uuid4().hex
    filename = f"recording_{file_token}.wav"
    file_path = os.path.join(user_dir, filename)
    audio_segment.export(file_path, format="wav")

    return file_path, filename, duration_seconds

async def _process_video_file(
    video_id: uuid.UUID,
    video_name: str,
    safe_filename: str,
    ext: str,
    original_path: str,
    mp3_path: str,
    owner_id: Union[uuid.UUID, str],
    upload_record_id: Optional[uuid.UUID] = None,
    db_session: Optional[Session] = None,
) -> None:
    """
    Process a stored media asset, create audio splice records, and update processing statuses.
    
    Parameters:
        owner_id (Union[uuid.UUID, str]): Identifier of the user who owns the created splice records.
        upload_record_id (Optional[uuid.UUID]): Upload record whose status should be updated when processing completes or fails.
        db_session (Optional[Session]): Database session to use; a session is created and closed when omitted.
    
    Raises:
        Exception: Re-raises processing failures after recording the error status.
    """

    db = db_session or _services.SessionLocal()
    owns_session = db_session is None
    # Track the splice files we write this run so the error path can report orphans left
    # behind (defined here so it is always bound, even if we fail before segmenting).
    segments = []

    # Acquire the concurrency slot immediately before the try so the finally's
    # release() is always paired with this acquire() (no line in between can raise).
    limiter = _get_processing_limiter()
    await limiter.acquire()

    try:
        if ext == ".mp4":
            await run_in_threadpool(_convert_mp4_to_mp3, original_path, mp3_path)

        splices_output_dir = os.path.join(SPLICES_DIR, video_name)
        segments = await run_in_threadpool(
            _segmentation.segment_audio_file,
            mp3_path,
            splices_output_dir,
            video_name,
        )
        if not segments:
            # No speech -> nothing to label. Don't silently report success: a COMPLETED
            # video with zero splices is indistinguishable from a real success in the
            # upload-history stats. Route it through the ERROR path with a clear message.
            raise ValueError(f"No usable speech detected in {mp3_path}")

        splice_payloads = [
            _schemas.SpliceCreate(
                name=video_name,
                path=segment.path,
                origin=safe_filename,
                duration=str(round(segment.duration_s, 3)),
                validation="0",
                label="",
                owner_id=owner_id,
            )
            for segment in segments
        ]
        # Persist the splices AND the COMPLETED statuses in one transaction (see
        # persist_processing_success): all-or-nothing, so a failure can never leave orphan
        # splices under an ERROR video nor flip a COMPLETED video. This also replaced the
        # per-splice commits (one connection checkout/commit per segment, up to ~190) that
        # were the source of the QueuePool exhaustion under concurrent uploads.
        await _services.persist_processing_success(
            db,
            video_id=video_id,
            video_update={
                "mp3_path": mp3_path,
                "to_mp3_status": "True",
                "splice_status": "True",
                "processing_status": MediaProcessingStatus.COMPLETED,
                "processing_error": None,
            },
            splices=splice_payloads,
            upload_record_id=upload_record_id,
        )
    except Exception as exc:
        logger.error(f"Video processing failed for video_id={video_id}: {exc}", exc_info=True)
        # A failed commit leaves the session in a pending-rollback state; clear it so the
        # ERROR-status write below can run. Guard the rollback itself: if it raises (e.g.
        # the DB connection is gone, the very thing most likely to have caused the failure)
        # it must not mask `exc` or skip the ERROR write and leave the video IN_PROGRESS.
        try:
            db.rollback()
        except Exception:
            logger.error(f"Rollback failed for video_id={video_id}", exc_info=True)
        # The splice .wav files written before the failed commit are now DB-less orphans.
        # We deliberately do NOT delete them here: splice files live in the non-unique
        # SPLICES_DIR/<video_name>/ dir under deterministic names ({name}_{startms}-{endms}.wav),
        # so a concurrent or retried same-named upload can legitimately own the identical
        # path — deleting by path could destroy another upload's *committed* audio. The
        # orphans are harmless (no Splice row references them, so they never join into
        # upload-history stats); reclaim them out-of-band with a GC that removes only files
        # that no Splice row points to.
        if segments:
            logger.warning(
                "Left %d orphan splice file(s) on disk for video_id=%s after failure; "
                "reclaim via offline GC (see SPLICES_DIR/%s)",
                len(segments), video_id, video_name,
            )
        try:
            await _services.persist_processing_error(
                db,
                video_id=video_id,
                error=str(exc),
                upload_record_id=upload_record_id,
            )
        except Exception:
            logger.error(
                f"Failed to persist ERROR status for video_id={video_id}", exc_info=True
            )
        raise
    finally:
        limiter.release()
        if owns_session:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Run application startup and shutdown lifecycle tasks.
    
    On startup, attempts to acquire an exclusive filesystem lock to serialize initialization across workers, ensures database tables exist, seeds a default policy consent (with safe fallback), creates system and anonymous users (linking them to the seeded consent), seeds default text prompts, and conditionally seeds a bundled sample media asset and its derived splices when missing. Handles common race conditions (retries, rollbacks, idempotent get-or-create patterns) and logs warnings/errors without preventing other workers from proceeding. Always closes the database session and releases the initialization lock before yielding control to the application runtime.
    """
    
    # Create a lock file to coordinate initialization across workers
    lock_file_path = os.path.join("/tmp", "app_init.lock")
    lock_file = open(lock_file_path, "w")
    
    try:
        # Try to acquire an exclusive, non-blocking lock
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        logger.info("Acquired initialization lock. Starting database setup...")
        
        # Initialize DB tables
        try:
            _services._add_tables()
            logger.info("Database tables created/verified.")
        except Exception as e:
            # Ignore errors if tables/types already exist (race condition safety)
            logger.warning(f"Database table creation warning (safe to ignore if concurrent): {e}")
        
        db = _services.SessionLocal()
        try:
            try:
                effective_date = _dt.date.fromisoformat(DEFAULT_CONSENT_EFFECTIVE_DATE)
            except ValueError:
                effective_date = _dt.date.today()
                logger.warning(
                    "DEFAULT_CONSENT_EFFECTIVE_DATE is not a valid ISO date. Falling back to today's date.")

            try:
                default_consent = _services.ensure_policy_consent(
                    db,
                    version=DEFAULT_CONSENT_VERSION,
                    effective_date=effective_date,
                    privacy_content=DEFAULT_PRIVACY_CONTENT,
                    terms_content=DEFAULT_TERMS_CONTENT,
                )
                logger.info(
                    "Policy consent version ready: %s (effective %s)",
                    default_consent.version,
                    default_consent.effective_date,
                )
            except Exception as consent_seed_error:
                logger.error(f"Failed to seed default consent version: {consent_seed_error}", exc_info=True)
                default_consent = _services.get_latest_policy_consent_model(db)

            if default_consent is None:
                raise RuntimeError("No policy consent version found; cannot continue initialization.")

            # Seed Users - use get_or_create pattern to handle race conditions
            system_user = _services.get_user_by_email(db, "system@albaniansr.com")
            if not system_user:
                try:
                    system_user_create = _schemas.UserCreate(
                        email="system@albaniansr.com",
                        name="System",
                        surname="Admin",
                        password="password",
                        provider="system",
                        consent_id=default_consent.id,
                    )
                    system_hash = auth.get_password_hash("password")
                    system_user = _services.create_user(db, system_user_create, hashed_password=system_hash)
                    logger.info("Seeded System User")
                except Exception as e:
                    db.rollback()
                    # Another worker might have created it, try to get it again
                    system_user = _services.get_user_by_email(db, "system@albaniansr.com")
                    if system_user:
                        logger.info("System User already exists (created by another worker)")
                    else:
                        logger.error(f"Failed to seed System User: {e}")

            anon_user = _services.get_user_by_email(db, "anonymous@albaniansr.com")
            if not anon_user:
                try:
                    anon_user_create = _schemas.UserCreate(
                        email="anonymous@albaniansr.com",
                        name="Anonymous",
                        surname="User",
                        password="password",
                        provider="system",
                        consent_id=default_consent.id,
                    )
                    anon_hash = auth.get_password_hash("password")
                    _services.create_user(db, anon_user_create, hashed_password=anon_hash)
                    logger.info("Seeded Anonymous User")
                except Exception as e:
                    db.rollback()
                    # Another worker might have created it
                    anon_user = _services.get_user_by_email(db, "anonymous@albaniansr.com")
                    if anon_user:
                        logger.info("Anonymous User already exists (created by another worker)")
                    else:
                        logger.error(f"Failed to seed Anonymous User: {e}")

            try:
                inserted_prompt_count = _services.seed_text_splices(db, DEFAULT_TEXT_SPLICE_PROMPTS)
                if inserted_prompt_count:
                    logger.info(f"Seeded {inserted_prompt_count} default text splices")
            except Exception as text_seed_error:
                logger.error(f"Failed to seed default text splices: {text_seed_error}", exc_info=True)

            # Seed database if empty OR if splice files are missing
            # Check specifically for the sample video
            sample_video_name = "Sample_Audio_Njerez_Dhe_Fate_E2"
            # Normalized name used in DB
            normalized_sample_name = sample_video_name.replace(" ", "_") 
            
            existing_video = db.query(_models.Video).filter(_models.Video.name == normalized_sample_name).first()
            splice_dir = os.path.join(SPLICES_DIR, normalized_sample_name)
            splice_files_exist = os.path.exists(splice_dir) and len(os.listdir(splice_dir)) > 0
            
            if existing_video and splice_files_exist:
                logger.info(f"Sample video '{existing_video.name}' and splice files exist. Skipping seed.")
            else:
                if existing_video and not splice_files_exist:
                    logger.warning(f"Database has sample video record but splice files are missing at {splice_dir}. Re-seeding files...")
                    # Delete ONLY the sample video records so we can recreate it
                    try:
                        # Delete splices associated with this video
                        db.query(_models.Splice).filter(_models.Splice.name == existing_video.name).delete()
                        # Delete the video itself
                        db.delete(existing_video)
                        db.commit()
                        logger.info("Cleared orphaned sample video records.")
                        # Reset existing_video to None so we proceed to seed
                        existing_video = None
                    except Exception as e:
                        db.rollback()
                        logger.error(f"Failed to clear orphaned records: {e}")
                
                if not existing_video:
                    logger.info("Sample video missing. Attempting to seed...")
                
                    seed_file_path = None
                    logger.info(f"Checking for sample file at: {DOCKER_SAMPLE_PATH}")
                    if os.path.exists(DOCKER_SAMPLE_PATH):
                        seed_file_path = DOCKER_SAMPLE_PATH
                        logger.info(f"Found sample file at: {DOCKER_SAMPLE_PATH}")
                    elif os.path.exists(SAMPLE_FILE_PATH):
                        seed_file_path = SAMPLE_FILE_PATH
                        logger.info(f"Found sample file at: {SAMPLE_FILE_PATH}")
                    
                    if seed_file_path:
                        try:
                            logger.info(f"Reading sample file from: {seed_file_path}")
                            with open(seed_file_path, "rb") as f:
                                file_content = f.read()
                            logger.info(f"Sample file size: {len(file_content)} bytes")
                            
                            logger.info("Starting video processing...")
                            (
                                normalized_name,
                                safe_filename,
                                ext,
                                file_location,
                                mp3_path,
                                _,
                            ) = _persist_media_file(
                                video_name="Sample Audio Njerez Dhe Fate E2",
                                filename="sample_audio_njerez_dhe_fate_e2.mp3",
                                file_content=file_content,
                            )

                            create_video_data = _schemas.VideoCreate(
                                name=normalized_name,
                                path=file_location,
                                category="Story",
                                to_mp3_status="False",
                                splice_status="False",
                                mp3_path=mp3_path,
                                uploader_id=system_user.id if system_user else "system",
                                processing_status=MediaProcessingStatus.IN_PROGRESS,
                            )
                            video_record = await _services.create_video(video=create_video_data, db=db)

                            await _process_video_file(
                                video_id=video_record.id,
                                video_name=normalized_name,
                                safe_filename=safe_filename,
                                ext=ext,
                                original_path=file_location,
                                mp3_path=mp3_path,
                                owner_id=system_user.id if system_user else "system",
                                db_session=db,
                            )
                            logger.info("Successfully seeded database with sample video.")
                            
                            # Verify splices were created
                            splice_dir = os.path.join(SPLICES_DIR, normalized_name)
                            if os.path.exists(splice_dir):
                                splice_files = os.listdir(splice_dir)
                                logger.info(f"Created {len(splice_files)} splice files in {splice_dir}")
                            else:
                                logger.warning(f"Splice directory not found: {splice_dir}")
                        except Exception as e:
                            logger.error(f"Failed to seed database: {e}", exc_info=True)
                    else:
                        logger.warning(f"Sample file not found at {DOCKER_SAMPLE_PATH} or {SAMPLE_FILE_PATH}. Skipping seed.")
        except Exception as e:
            logger.error(f"Error during startup seeding: {e}", exc_info=True)
        finally:
            db.close()
            
    except IOError:
        logger.info("Another worker is initializing the application. Skipping initialization steps.")
    finally:
        # Keep the lock file open but release the lock? 
        # Actually, closing the file releases the lock.
        # But we want to hold it until we are done.
        # The 'finally' block here runs after the try block finishes (success or exception).
        # So we just close the file.
        lock_file.close()
        
    yield

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    openapi_url='/openapi.json',
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    contact=CONTACT_INFO,
    license_info=LICENSE_INFO,
    terms_of_service=TERMS_OF_SERVICE,
    openapi_tags=TAGS_METADATA,
)

# Routers
app.include_router(auth.router)
app.include_router(consents.router)
app.include_router(users.router)
app.include_router(support.router)

configure_documentation(app, base_path=API_ROOT_PATH)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/splices", StaticFiles(directory=SPLICES_DIR_ABS), name="splices")
app.mount("/mp3", StaticFiles(directory=UPLOAD_DIR_MP3_ABS), name="mp3")
app.mount("/mp4", StaticFiles(directory=UPLOAD_DIR_MP4_ABS), name="mp4")

@app.post(
    "/video/add",
    response_model=_schemas.ResponseModel,
    tags=["Video Intake"],
    summary="Upload and preprocess a new media asset",
    description=(
        "Accepts MP4 or MP3 files, stores the raw asset, and schedules background processing "
        "(conversion + splicing) so the client receives an immediate acknowledgement."
    ),
)
async def create_video(
    background_tasks: BackgroundTasks,
    video_name: str = Form(...),
    video_category: str = Form(...),
    consent: bool = Form(True),
    video_file: UploadFile = File(...),
    current_user: _models.User = Depends(auth.get_current_user),
    db: Session = Depends(_services.get_db),
):
    """
    Handle an uploaded video or audio file: persist the file, create corresponding Video and UploadRecord entries, and schedule background processing.
    
    Parameters:
        video_name (str): Display name provided for the media.
        video_category (str): Category label for the media.
        consent (bool): Whether the uploader has given consent; upload is rejected if False.
    
    Returns:
        ResponseModel: Success response containing `video_id`, `upload_id`, and `status` indicating the upload processing state.
    
    Raises:
        HTTPException: If consent is not given, if no server consent version is configured, if the uploaded file lacks a filename, if the file extension is unsupported (only `.mp4` and `.mp3`), or on other processing failures.
    """
    if not consent:
        raise HTTPException(status_code=400, detail="Consent is required to upload media.")

    latest_consent = _services.get_latest_policy_consent(db)
    if latest_consent is None:
        raise HTTPException(status_code=500, detail="No consent version configured on the server.")

    filename = video_file.filename
    if filename is None:
        raise HTTPException(status_code=400, detail="Filename is required.")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".mp4", ".mp3"]:
        raise HTTPException(status_code=400, detail="Invalid document type. Only .mp4 and .mp3 are supported.")

    try:
        file_content = await video_file.read()
        (
            normalized_name,
            safe_filename,
            ext,
            file_location,
            mp3_path,
            _,
        ) = _persist_media_file(video_name, filename, file_content)

        create_video_data = _schemas.VideoCreate(
            name=normalized_name,
            path=file_location,
            category=video_category,
            to_mp3_status="False",
            splice_status="False",
            mp3_path=mp3_path,
            uploader_id=current_user.id,
            processing_status=MediaProcessingStatus.IN_PROGRESS,
        )
        video_record = await _services.create_video(video=create_video_data, db=db)

        upload_record = await _services.create_upload_record(
            upload=_schemas.UploadRecordCreate(
                user_id=current_user.id,
                video_id=video_record.id,
                original_filename=filename,
                display_name=normalized_name,
                category=video_category,
                consent_version=latest_consent.version,
                consent_given=True,
                status=MediaProcessingStatus.IN_PROGRESS,
            ),
            db=db,
        )

        background_tasks.add_task(
            _process_video_file,
            video_record.id,
            normalized_name,
            safe_filename,
            ext,
            file_location,
            mp3_path,
            current_user.id,
            upload_record.id,
        )

        return _schemas.ResponseModel(
            status="success",
            data={
                "video_id": video_record.id,
                "upload_id": upload_record.id,
                "status": upload_record.status.value,
            },
            message="Upload received. Processing has been scheduled.",
        )
    except Exception as e:
        logger.error(f"Error creating video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/uploads/history",
    response_model=_schemas.ResponseModel,
    tags=["Video Intake"],
    summary="List recently uploaded media",
    description="Returns the authenticated user's most recent uploads with their processing state.",
)
async def list_upload_history(
    current_user: _models.User = Depends(auth.get_current_user),
    db: Session = Depends(_services.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    total, records = _services.get_user_upload_records(db, current_user.id, page, page_size)
    names = [record.display_name for record in records if record.display_name]
    stats_map = _services.get_splice_stats_for_video_names(db, current_user.id, names)

    items = []
    for record in records:
        schema_record = _schemas.UploadRecord.model_validate(record)
        stats_payload = stats_map.get(record.display_name)
        if stats_payload:
            schema_record = schema_record.model_copy(
                update={"stats": _schemas.UploadStats(**stats_payload)}
            )
        items.append(schema_record.model_dump())

    total_pages = math.ceil(total / page_size) if total else 0
    return _schemas.ResponseModel(
        status="success",
        data={
            "items": items,
            "meta": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        },
        message="Upload history retrieved",
    )

def _prepare_trim_window(start: Optional[float], end: Optional[float]) -> Optional[Tuple[float, float]]:
    """Validates and orders trimming boundaries."""
    if start is None and end is None:
        return None
    if start is None or end is None:
        raise HTTPException(status_code=400, detail="Both start and end times are required when trimming")
    if start < 0 or end < 0:
        raise HTTPException(status_code=400, detail="Start and end times must be non-negative")
    if start == end:
        return None
    ordered_start = min(start, end)
    ordered_end = max(start, end)
    return ordered_start, ordered_end


def _trim_audio_segment(file_path: str, start: float, end: float) -> Optional[float]:
    """Trims the provided audio file in-place and returns the new duration in seconds."""
    if start == end:
        logger.info("Start and end times are identical; skipping trim for %s", file_path)
        return None

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file for splice not found")

    try:
        audio = AudioSegment.from_file(file_path)
        audio_length_ms = len(audio)
        start_ms = max(0, int(start * 1000))
        end_ms = min(audio_length_ms, int(end * 1000))

        if start_ms >= end_ms:
            logger.info("Computed trim window is empty for %s; skipping trim", file_path)
            return None

        trimmed_segment = audio[start_ms:end_ms]
        audio_format = os.path.splitext(file_path)[1].lstrip('.').lower() or 'wav'
        trimmed_segment.export(file_path, format=audio_format)
        new_duration = len(trimmed_segment) / 1000.0
        logger.info(
            "Trimmed %s from %.3fs-%.3fs; new duration %.3fs",
            file_path,
            start_ms / 1000.0,
            end_ms / 1000.0,
            new_duration,
        )
        return new_duration
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to trim audio file %s: %s", file_path, exc)
        raise HTTPException(status_code=500, detail="Failed to trim audio file")

@app.get(
    "/audio/to_label",
    response_model=_schemas.ResponseModel,
    tags=["Labeling Queue"],
    summary="Reserve the next splice for labeling",
    description=(
        "Moves the oldest unfinished splice into the processing bucket, converts the filesystem path into "
        "a public `/splices` URL, and returns the payload ready for transcription clients."
    ),
)
async def get_audio_to_label(db: Session = Depends(_services.get_db)):
    first_splice = await _services.get_first_splice(db)
    if not first_splice:
        return _schemas.ResponseModel(status="success", message="No audio to label")

    # Transactional logic: Create processing record -> Delete original
    try:
        splice_being_processed_data = _schemas.SpliceBeingProcessedCreate(
            name=first_splice.name,
            path=first_splice.path,
            label=first_splice.label,
            origin=first_splice.origin,
            duration=first_splice.duration,
            validation=first_splice.validation,
            status='un_labeled',
            owner_id=first_splice.owner_id
        )
        processed_splice = await _services.create_splice_being_processed(splice_being_processed_data, db)
        await _services.delete_splice(first_splice.id, db)

        response_data = processed_splice.model_copy(update={
            "path": get_public_path(processed_splice.path)
        })

        return _schemas.ResponseModel(
            status="success",
            data=response_data,
            message="Audio retrieved for labeling"
        )
    except Exception as e:
        logger.error(f"Error retrieving audio to label: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audio for labeling")

@app.get(
    "/audio/to_validate",
    response_model=_schemas.ResponseModel,
    tags=["Labeling Queue"],
    summary="Reserve the next splice for validation",
    description=(
        "Transitions the next labeled splice into the processing table, ensuring validators always receive "
        "cache-busted media URLs and up-to-date metadata."
    ),
)
async def get_audio_to_validate(db: Session = Depends(_services.get_db)):
    first_splice = await _services.get_first_labeled_splice(db)
    if not first_splice:
        return _schemas.ResponseModel(status="success", message="No audio to validate")

    try:
        splice_being_processed_data = _schemas.SpliceBeingProcessedCreate(
            name=first_splice.name,
            path=first_splice.path,
            label=first_splice.label,
            origin=first_splice.origin,
            duration=first_splice.duration,
            validation=first_splice.validation,
            status='labeled',
            owner_id=first_splice.owner_id,
            labeler_id=first_splice.labeler_id
        )
        processed_splice = await _services.create_splice_being_processed(splice_being_processed_data, db)
        await _services.delete_labeled_splice(first_splice.id, db)

        response_data = processed_splice.model_copy(update={
            "path": get_public_path(processed_splice.path)
        })

        return _schemas.ResponseModel(
            status="success",
            data=response_data,
            message="Audio retrieved for validation"
        )
    except Exception as e:
        logger.error(f"Error retrieving audio to validate: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audio for validation")

async def _label_splice_logic(label_splice: _schemas.LabelSplice, db: Session, user_id: str):
    splice_being_processed = await _services.get_splice_being_processed(label_splice.id, db)
    if not splice_being_processed or splice_being_processed.status != 'un_labeled':
        raise HTTPException(status_code=404, detail="Splice not found or invalid status")
    
    trim_window = _prepare_trim_window(label_splice.start, label_splice.end)
    new_duration = None
    if trim_window:
        new_duration = _trim_audio_segment(splice_being_processed.path, *trim_window)
    
    update_data = {
        "id": label_splice.id,
        "label": label_splice.label,
        "validation": label_splice.validation or '0.95',
        "labeler_id": user_id,
    }
    if new_duration is not None:
        update_data["duration"] = str(round(new_duration, 3))
    updated_splice = await _services.update_splice_being_processed(splice_id=label_splice.id, data=update_data, db=db)

    labeled_splice_data = _schemas.LabeledSpliceCreate(
        name=updated_splice.name,
        path=updated_splice.path,
        label=label_splice.label,
        origin=updated_splice.origin,
        duration=updated_splice.duration,
        validation=label_splice.validation or '0.95',
        owner_id=updated_splice.owner_id,
        labeler_id=user_id
    )
    await _services.create_labeled_splice(labeled_splice_data, db)
    await _services.delete_splice_being_processed(splice_being_processed, db)

    return _schemas.ResponseModel(status="success", message="Splice labeled and moved successfully")

@app.put(
    "/audio/label",
    response_model=_schemas.ResponseModel,
    tags=["Labeling Actions"],
    summary="Submit a labeled splice as an authenticated contributor",
    description=(
        "Applies optional trimming, persists the transcript, stamps the labeler ID, and promotes the clip "
        "to the labeled queue while clearing the processing lock."
    ),
)
async def label_splice(
    label_splice: _schemas.LabelSplice, 
    db: Session = Depends(_services.get_db),
    current_user: _schemas.User = Depends(auth.get_current_user)
):
    try:
        return await _label_splice_logic(label_splice, db, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error labeling splice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put(
    "/audio/label/anonymous",
    response_model=_schemas.ResponseModel,
    tags=["Labeling Actions"],
    summary="Submit a labeled splice without authentication",
    description="Identical to `/audio/label` but automatically attributes the work to the anonymous user.",
)
async def label_splice_anonymous(
    label_splice: _schemas.LabelSplice, 
    db: Session = Depends(_services.get_db)
):
    try:
        anon_user = _services.get_user_by_email(db, "anonymous@albaniansr.com")
        if not anon_user:
             raise HTTPException(status_code=500, detail="Anonymous user not found")
        return await _label_splice_logic(label_splice, db, anon_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error labeling splice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _validate_splice_logic(
    validate_splice: _schemas.ValidateSplice,
    db: Session,
    fallback_validator_id: Optional[str],
):
    splice_being_processed = await _services.get_splice_being_processed(validate_splice.id, db)
    if not splice_being_processed or splice_being_processed.status != 'labeled':
        raise HTTPException(status_code=404, detail="Splice not found or invalid status")
    validator_id = validate_splice.validator_id or fallback_validator_id
    if not validator_id:
        raise HTTPException(status_code=400, detail="Validator id is required to finalize a splice")
    
    trim_window = _prepare_trim_window(validate_splice.start, validate_splice.end)
    new_duration = None
    if trim_window:
        new_duration = _trim_audio_segment(splice_being_processed.path, *trim_window)
    
    update_data = {
        "id": validate_splice.id,
        "label": validate_splice.label,
        "validation": validate_splice.validation or '1.0',
        "validator_id": validator_id,
    }
    if new_duration is not None:
        update_data["duration"] = str(round(new_duration, 3))

    updated_splice = await _services.update_splice_being_processed(
        splice_id=validate_splice.id,
        data=update_data,
        db=db
    )

    hq_splice_data = _schemas.HighQualityLabeledSpliceCreate(
        name=updated_splice.name,
        path=updated_splice.path,
        label=validate_splice.label,
        origin=updated_splice.origin,
        duration=updated_splice.duration,
        validation=validate_splice.validation or '1.0',
        owner_id=updated_splice.owner_id,
        validator_id=validator_id,
        labeler_id=updated_splice.labeler_id
    )
    await _services.create_high_quality_labeled_splice(hq_splice_data, db)
    await _services.delete_splice_being_processed(splice_being_processed, db)

    return _schemas.ResponseModel(status="success", message="Splice validated and moved successfully")

@app.put(
    "/audio/validate",
    response_model=_schemas.ResponseModel,
    tags=["Validation Actions"],
    summary="Approve a labeled splice as an authenticated validator",
    description=(
        "Confirms the transcript, optionally trims audio, persists validator identity, and upgrades the clip "
        "into the high-quality dataset."
    ),
)
async def validate_splice(
    validate_splice: _schemas.ValidateSplice, 
    db: Session = Depends(_services.get_db),
    current_user: _schemas.User = Depends(auth.get_current_user)
):
    try:
        if validate_splice.validator_id and validate_splice.validator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Validator mismatch")
        payload = validate_splice.model_copy(update={"validator_id": current_user.id})
        return await _validate_splice_logic(payload, db, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating splice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put(
    "/audio/validate/anonymous",
    response_model=_schemas.ResponseModel,
    tags=["Validation Actions"],
    summary="Approve a labeled splice without authentication",
    description="Anonymous reviewers can finalize splices when authenticated validators are not required.",
)
async def validate_splice_anonymous(
    validate_splice: _schemas.ValidateSplice, 
    db: Session = Depends(_services.get_db)
):
    try:
        anon_user = _services.get_user_by_email(db, "anonymous@albaniansr.com")
        if not anon_user:
             raise HTTPException(status_code=500, detail="Anonymous user not found")
        payload = validate_splice.model_copy(update={"validator_id": anon_user.id})
        return await _validate_splice_logic(payload, db, anon_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating splice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete(
    "/audio",
    response_model=_schemas.ResponseModel,
    tags=["Operational Utilities"],
    summary="Remove a splice from the processing queue",
    description="Moves the clip into the deleted archive and frees up the processing slot for the next task.",
)
async def delete_splice(delete_splice: _schemas.DeleteSplice, db: Session = Depends(_services.get_db)):
    try:
        splice_being_processed = await _services.get_splice_being_processed(delete_splice.id, db)
        if not splice_being_processed:
            raise HTTPException(status_code=404, detail="Splice not found")

        # Move to DeletedSplice
        deleted_splice_data = _schemas.DeletedSpliceCreate(
            name=splice_being_processed.name,
            path=splice_being_processed.path,
            label=splice_being_processed.label or "",
            origin=splice_being_processed.origin,
            duration=splice_being_processed.duration,
            validation=splice_being_processed.validation or "0",
            owner_id=splice_being_processed.owner_id,
            labeler_id=splice_being_processed.labeler_id,
            validator_id=splice_being_processed.validator_id
        )
        await _services.create_deleted_splice(deleted_splice_data, db)

        await _services.delete_splice_being_processed(splice_being_processed, db)

        return _schemas.ResponseModel(
            status="success",
            message="Splice deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting splice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/audio/getsa",
    response_model=_schemas.ResponseModel,
    tags=["Operational Utilities"],
    summary="Fetch a sample splice path",
    description="Returns the oldest splice path for health checks or preview players.",
)
async def get_audio_sample(db: Session = Depends(_services.get_db)):
    # Optimized query using ORM
    path = db.query(_models.Splice.path).order_by(_models.Splice.id).scalar()
    if not path:
        return _schemas.ResponseModel(status="success", data=[], message="No audio sample found")
    return _schemas.ResponseModel(status="success", data=path, message="Audio sample retrieved")

@app.get(
    "/audio/get_validation_audio_link",
    response_model=_schemas.ResponseModel,
    tags=["Operational Utilities"],
    summary="Peek at the next labeled splice",
    description="Returns the next labeled splice without reserving it, primarily for monitoring tools.",
)
async def next_validation_data(db: Session = Depends(_services.get_db)):
    first_splice = db.query(_models.LabeledSplice).order_by(_models.LabeledSplice.id).first()
    if not first_splice:
        return _schemas.ResponseModel(status="success", message="No validation audio found")
    return _schemas.ResponseModel(status="success", data=first_splice, message="Validation audio retrieved")

@app.get(
    "/audio/get_clip_id/",
    response_model=_schemas.ResponseModel,
    tags=["Operational Utilities"],
    summary="Fetch the next splice identifier",
    description="Provides the ID of the first pending splice to aid lightweight dashboards.",
)
async def get_clip_id(db: Session = Depends(_services.get_db)):
    first_splice_id = db.query(_models.Splice.id).order_by(_models.Splice.id).scalar()
    if not first_splice_id:
        return _schemas.ResponseModel(status="success", message="No clip ID found")
    return _schemas.ResponseModel(status="success", data=first_splice_id, message="Clip ID retrieved")

@app.get(
    "/audio/get_validation_audio_link_plus",
    response_model=_schemas.ResponseModel,
    tags=["Operational Utilities"],
    summary="Fetch the next unlabeled splice path",
    description="Returns only the media path for consumers that need minimal payloads.",
)
async def get_validation_audio_link_plus(db: Session = Depends(_services.get_db)):
    first_splice_path = db.query(_models.Splice.path).order_by(_models.Splice.id).scalar()
    if not first_splice_path:
        return _schemas.ResponseModel(status="success", data=[], message="No validation audio link found")
    return _schemas.ResponseModel(status="success", data=first_splice_path, message="Validation audio link retrieved")


@app.get(
    "/record/text",
    response_model=_schemas.ResponseModel,
    tags=["Recording"],
    summary="Reserve a text prompt for recording",
    description=(
        "Returns the contributor's active prompt if it is already reserved or fetches the next available "
        "text snippet so they can record fresh speech directly into the labeled queue."
    ),
)
async def get_record_prompt(
    current_user: _models.User = Depends(auth.get_current_user),
    db: Session = Depends(_services.get_db),
):
    existing_prompt = _services.get_reserved_text_splice_for_user(db, current_user.id)
    if existing_prompt:
        return _schemas.ResponseModel(
            status="success",
            data=existing_prompt.model_dump(),
            message="Prompt already reserved",
        )

    next_prompt = _services.get_next_available_text_splice(db)
    if not next_prompt:
        return _schemas.ResponseModel(
            status="success",
            data=None,
            message="No text prompts available right now.",
        )

    reserved_prompt = await _services.reserve_text_splice(next_prompt.id, current_user.id, db)
    return _schemas.ResponseModel(
        status="success",
        data=reserved_prompt.model_dump(),
        message="Recording prompt reserved",
    )


@app.post(
    "/record/upload",
    response_model=_schemas.ResponseModel,
    tags=["Recording"],
    summary="Submit a recorded clip",
    description=(
        "Accepts raw microphone audio plus the prompted text, persists the file under the contributor's splice "
        "directory, and promotes it straight into the labeled queue so validators can pick it up next."
    ),
)
async def submit_recording(
    text_splice_id: uuid.UUID = Form(...),
    spoken_text: str = Form(...),
    audio_file: UploadFile = File(...),
    current_user: _models.User = Depends(auth.get_current_user),
    db: Session = Depends(_services.get_db),
):
    """
    Accepts a user's recorded audio and transcript for a text prompt, stores the audio as a labeled splice, and marks the prompt completed.
    
    Parameters:
        text_splice_id (uuid.UUID): ID of the text prompt being recorded.
        spoken_text (str): Transcript provided by the contributor.
        audio_file (UploadFile): Uploaded audio file containing the recording.
        current_user (_models.User): Authenticated user submitting the recording.
        db (Session): Database session for persistence operations.
    
    Returns:
        _schemas.ResponseModel: Success response containing:
            - recorded_splice_id: ID of the created labeled splice.
            - audio_path: Public URL path to the stored audio file.
            - duration: Duration of the stored audio (seconds as a string).
            - text_splice: The updated text splice record.
    
    Raises:
        HTTPException 404: If the text prompt is not found.
        HTTPException 403: If the text prompt is reserved by another contributor.
        HTTPException 409: If the text prompt has already been recorded.
        HTTPException 400: If the transcript is empty or the uploaded audio is empty, or if the audio cannot be decoded.
    """
    text_splice = _services.get_text_splice_by_id(db, text_splice_id)
    if not text_splice:
        raise HTTPException(status_code=404, detail="Text prompt not found")

    if text_splice.reserved_by and text_splice.reserved_by != current_user.id:
        raise HTTPException(status_code=403, detail="This prompt is reserved by another contributor")

    if text_splice.status == "completed":
        raise HTTPException(status_code=409, detail="This prompt has already been recorded")

    if text_splice.status == "pending":
        text_splice = await _services.reserve_text_splice(text_splice.id, current_user.id, db)

    transcript = spoken_text.strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript text is required")

    file_bytes = await audio_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty")

    try:
        audio_path, safe_filename, duration_seconds = await run_in_threadpool(
            _store_recorded_audio,
            current_user.id,
            file_bytes,
        )
    except ValueError as exc:
        logger.error("Failed to decode recorded audio", exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    duration_str = str(round(duration_seconds, 3))
    recording_name = f"recordings_{current_user.id}"

    labeled_splice_payload = _schemas.LabeledSpliceCreate(
        name=recording_name,
        path=audio_path,
        label=transcript,
        origin=safe_filename,
        duration=duration_str,
        validation="0.95",
        owner_id=current_user.id,
        labeler_id=current_user.id,
    )
    recorded_splice = await _services.create_labeled_splice(labeled_splice_payload, db)

    snapshot_payload = _schemas.TextSpliceRecordingCreate(
        text_splice_id=text_splice.id,
        recorded_splice_id=recorded_splice.id,
        name=recorded_splice.name,
        path=recorded_splice.path,
        label=recorded_splice.label,
        origin=recorded_splice.origin,
        duration=recorded_splice.duration,
        validation=recorded_splice.validation,
        owner_id=recorded_splice.owner_id,
        labeler_id=recorded_splice.labeler_id,
    )
    await _services.create_text_splice_recording(snapshot_payload, db)

    completed_prompt = await _services.complete_text_splice(
        text_splice_id=text_splice.id,
        recorded_splice_id=recorded_splice.id,
        db=db,
    )

    return _schemas.ResponseModel(
        status="success",
        data={
            "recorded_splice_id": recorded_splice.id,
            "audio_path": get_public_path(recorded_splice.path),
            "duration": duration_str,
            "text_splice": completed_prompt.model_dump(),
        },
        message="Recording submitted successfully",
    )

@app.get(
    "/dataset_insight_info",
    response_model=_schemas.ResponseModel,
    tags=["Dataset Insights"],
    summary="Aggregate dataset progress metrics",
    description="Returns durations and record counts for unlabeled, labeled, and validated corpora.",
)
async def get_summary(db: Session = Depends(_services.get_db)):
    # Use a single query or parallel execution if possible, but SQLAlchemy session is synchronous usually.
    # We can just execute them.
    
    # Helper to handle None result from sum
    """
    Summarize dataset duration and record counts by labeling stage.
    
    Returns:
        _schemas.ResponseModel: A response containing total durations and record counts
            for labeled, validated, and unlabeled audio.
    """
    def get_sum(model, col):
        return db.query(func.sum(col.cast(_sql.Float))).scalar() or 0.0
    
    def get_count(model):
        return db.query(func.count(model.id)).scalar() or 0

    data = {
        "total_duration_labeled": get_sum(_models.LabeledSplice, _models.LabeledSplice.duration),
        "total_duration_validated": get_sum(_models.HighQualityLabeledSplice, _models.HighQualityLabeledSplice.duration),
        "total_duration_unlabeled": get_sum(_models.Splice, _models.Splice.duration),
        "total_labeled": get_count(_models.LabeledSplice),
        "total_validated": get_count(_models.HighQualityLabeledSplice),
        "total_unlabeled": get_count(_models.Splice),
    }

    return _schemas.ResponseModel(
        status="success",
        data=data,
        message="Dataset summary retrieved"
    )


@app.get(
    "/dataset/export",
    tags=["Dataset Insights"],
    summary="Export the labeled corpus as a training manifest",
    description=(
        "Streams the labeled or validated corpus as a training-ready manifest. "
        "`format=jsonl` emits one NeMo-style JSON object per line "
        "(`audio_filepath`, `duration`, `text`); `format=csv` emits LJSpeech-style "
        "pipe-separated rows (`file_name|transcription|normalized_transcription`, "
        "no header, file_name without extension) as consumed by the training notebooks."
    ),
)
async def export_dataset(
    stage: str = Query("validated", pattern="^(validated|labeled)$"),
    format: str = Query("jsonl", pattern="^(jsonl|csv)$"),
    db: Session = Depends(_services.get_db),
):
    """
    Stream a labeled or validated dataset manifest in JSONL or CSV format.
    
    Parameters:
        stage (str): Dataset stage to export: ``"validated"`` or ``"labeled"``.
        format (str): Manifest format: ``"jsonl"`` or ``"csv"``.
    
    Returns:
        StreamingResponse: A downloadable manifest containing audio paths and transcript labels.
    """
    model = (
        _models.HighQualityLabeledSplice if stage == "validated" else _models.LabeledSplice
    )
    rows = db.query(model).order_by(model.created_at).all()

    def iter_lines():
        """
        Generate dataset manifest lines for the selected export format.
        
        Yields:
            str: A JSONL or pipe-separated manifest line for each row with a non-empty
                label.
        """
        for row in rows:
            label = " ".join((row.label or "").split())
            if not label:
                continue
            if format == "jsonl":
                try:
                    duration = round(float(row.duration), 3)
                except (TypeError, ValueError):
                    duration = None
                yield json.dumps(
                    {
                        "audio_filepath": get_public_path(row.path, include_version=False),
                        "duration": duration,
                        "text": label,
                    },
                    ensure_ascii=False,
                ) + "\n"
            else:
                file_name = os.path.splitext(os.path.basename(row.path or ""))[0]
                clean = label.replace("|", " ")
                yield f"{file_name}|{clean}|{clean.lower()}\n"

    extension = "jsonl" if format == "jsonl" else "csv"
    media_type = "application/x-ndjson" if format == "jsonl" else "text/csv"
    return StreamingResponse(
        iter_lines(),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=dataset_{stage}.{extension}"},
    )


