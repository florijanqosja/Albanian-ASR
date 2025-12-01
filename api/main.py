import logging
import os
import wave
from contextlib import asynccontextmanager
from typing import Optional, Tuple

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.silence import split_on_silence
from sqlalchemy.orm import Session
from sqlalchemy import func, select
import sqlalchemy as _sql

from .database import schemas as _schemas
from .database import services as _services
from .database import models as _models
from .routers import auth, users
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
IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"
BASE_DIR = "/code" if IS_PRODUCTION else "."
API_ROOT_PATH = os.getenv("API_ROOT_PATH", "")

UPLOAD_DIR_MP4 = os.path.join(BASE_DIR, "mp4")
UPLOAD_DIR_MP3 = os.path.join(BASE_DIR, "mp3")
SPLICES_DIR = os.path.join(BASE_DIR, "splices")

UPLOAD_DIR_MP4_ABS = os.path.abspath(UPLOAD_DIR_MP4)
UPLOAD_DIR_MP3_ABS = os.path.abspath(UPLOAD_DIR_MP3)
SPLICES_DIR_ABS = os.path.abspath(SPLICES_DIR)
SAMPLE_FILE_PATH = "sample_perrala.mp3"
DOCKER_SAMPLE_PATH = "/code/sample_perrala.mp3"

# In development, ensure directories exist. In production, entrypoint.sh handles this.
if not IS_PRODUCTION:
    for directory in [UPLOAD_DIR_MP4, UPLOAD_DIR_MP3, SPLICES_DIR]:
        os.makedirs(directory, exist_ok=True)

logger.info(f"Running in {'production' if IS_PRODUCTION else 'development'} mode")
logger.info(f"Static file directories: mp4={UPLOAD_DIR_MP4}, mp3={UPLOAD_DIR_MP3}, splices={SPLICES_DIR}")

def _get_wav_duration(wav_path: str) -> float:
    """Calculates the duration of a WAV file in seconds."""
    try:
        with wave.open(wav_path, 'rb') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            return frames / float(rate)
    except Exception as e:
        logger.error(f"Error calculating duration for {wav_path}: {e}")
        return 0.0

def _convert_mp4_to_mp3(mp4_path: str, mp3_path: str) -> None:
    """Converts an MP4 video file to an MP3 audio file."""
    try:
        logger.info(f"Converting {mp4_path} to {mp3_path}")
        video = VideoFileClip(mp4_path)
        # logger=None suppresses moviepy's stdout progress bar
        video.audio.write_audiofile(mp3_path, logger=None)
        video.close()
    except Exception as e:
        logger.error(f"Error converting mp4 to mp3: {e}")
        raise HTTPException(status_code=500, detail=f"Audio conversion failed: {str(e)}")

def _splice_audio(file_path: str, video_name: str, min_silence_len: int = 500, silence_thresh: int = -30) -> None:
    """Splits audio into chunks based on silence."""
    try:
        logger.info(f"Splicing audio for {video_name}")
        output_dir = os.path.join(SPLICES_DIR, video_name)
        os.makedirs(output_dir, exist_ok=True)
        
        audio = AudioSegment.from_file(file_path)
        chunks = split_on_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh
        )
        
        chunk_start = 0
        for chunk in chunks:
            chunk_end = chunk_start + len(chunk)
            # Format: videoplaybackmp4_START-END.wav (START/END in seconds)
            chunk_filename = f"videoplaybackmp4_{chunk_start/1000}-{chunk_end/1000}.wav"
            chunk_path = os.path.join(output_dir, chunk_filename)
            chunk.export(chunk_path, format="wav")
            chunk_start = chunk_end
            
    except Exception as e:
        logger.error(f"Error splicing audio: {e}")
        raise HTTPException(status_code=500, detail=f"Audio splicing failed: {str(e)}")

async def _process_video_upload(
    video_name: str,
    video_category: str,
    file_content: bytes,
    filename: str,
    db: Session,
    user_id: str
) -> _schemas.Video:
    """
    Handles the core logic for processing a video upload:
    1. Save file
    2. Create DB entry
    3. Convert to MP3 (if needed)
    4. Splice audio
    5. Create splice entries in DB
    6. Update video status
    """
    video_name = str(video_name).replace(" ", "_")
    ext = os.path.splitext(filename)[1].lower()
    
    # Sanitize filename
    safe_filename = "".join(x for x in filename if x.isalnum() or x in "._-")
    
    mp4_path = None
    mp3_path = None
    file_location = None

    if ext == ".mp4":
        mp4_dir = os.path.join(UPLOAD_DIR_MP4, video_name)
        os.makedirs(mp4_dir, exist_ok=True)
        file_location = os.path.join(mp4_dir, safe_filename)
        mp4_path = file_location
        
        mp3_dir = os.path.join(UPLOAD_DIR_MP3, video_name)
        os.makedirs(mp3_dir, exist_ok=True)
        mp3_path = os.path.join(mp3_dir, safe_filename.replace('.mp4', '.mp3'))
    else:
        # Assume MP3
        mp3_dir = os.path.join(UPLOAD_DIR_MP3, video_name)
        os.makedirs(mp3_dir, exist_ok=True)
        mp3_path = os.path.join(mp3_dir, safe_filename)
        file_location = mp3_path

    # Save file
    with open(file_location, "wb+") as f:
        f.write(file_content)

    # Create initial DB entry
    create_video_data = _schemas.VideoCreate(
        name=video_name,
        path=file_location,
        category=video_category,
        to_mp3_status="False",
        splice_status="False",
    )
    video_record = await _services.create_video(video=create_video_data, db=db)

    # Process Audio (Convert & Splice)
    # Run blocking operations in threadpool
    if ext == ".mp4":
        await run_in_threadpool(_convert_mp4_to_mp3, mp4_path, mp3_path)
    
    await run_in_threadpool(_splice_audio, mp3_path, video_name)

    # Create Splice Entries
    splices_output_dir = os.path.join(SPLICES_DIR, video_name)
    if os.path.exists(splices_output_dir):
        splice_files = os.listdir(splices_output_dir)
        for splice_file in splice_files:
            splice_path = os.path.join(splices_output_dir, splice_file)
            # Calculate duration (blocking I/O)
            duration = await run_in_threadpool(_get_wav_duration, splice_path)

            create_splice_data = _schemas.SpliceCreate(
                name=video_name,
                path=splice_path,
                origin=safe_filename,
                duration=str(duration),
                validation="0",
                label="",
                owner_id=user_id
            )
            await _services.create_splice(splice=create_splice_data, db=db)

    # Update Video Status
    update_video_data = {
        "mp3_path": mp3_path,
        "to_mp3_status": "True",
        "splice_status": "True",
    }
    updated_video = await _services.update_video(video_path=file_location, update_data=update_video_data, db=db)
    return updated_video

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the application."""
    # Initialize DB tables
    _services._add_tables()
    
    db = _services.SessionLocal()
    try:
        # Seed Users - use get_or_create pattern to handle race conditions
        system_user = _services.get_user_by_email(db, "system@albaniansr.com")
        if not system_user:
            try:
                system_user_create = _schemas.UserCreate(
                    email="system@albaniansr.com",
                    name="System",
                    surname="Admin",
                    password="password",
                    provider="system"
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
                    raise e

        anon_user = _services.get_user_by_email(db, "anonymous@albaniansr.com")
        if not anon_user:
            try:
                anon_user_create = _schemas.UserCreate(
                    email="anonymous@albaniansr.com",
                    name="Anonymous",
                    surname="User",
                    password="password",
                    provider="system"
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
                    raise e

        # Seed database if empty OR if splice files are missing
        existing_video = db.query(_models.Video).first()
        splice_dir = os.path.join(SPLICES_DIR, "Sample_Perrala")
        splice_files_exist = os.path.exists(splice_dir) and len(os.listdir(splice_dir)) > 0
        
        if existing_video and splice_files_exist:
            logger.info(f"Database has videos (found: {existing_video.name}) and splice files exist. Skipping seed.")
        else:
            if existing_video and not splice_files_exist:
                logger.warning(f"Database has video record but splice files are missing at {splice_dir}. Re-seeding files...")
                # Delete orphaned database records so we can recreate everything
                try:
                    db.query(_models.Splice).delete()
                    db.query(_models.Video).delete()
                    db.commit()
                    logger.info("Cleared orphaned database records.")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Failed to clear orphaned records: {e}")
            else:
                logger.info("Database is empty. Attempting to seed...")
            
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
                    
                    # We use the processing function to ensure the seed data is fully functional
                    logger.info("Starting video processing...")
                    await _process_video_upload(
                        video_name="Sample Perrala",
                        video_category="Story",
                        file_content=file_content,
                        filename="sample_perrala.mp3",
                        db=db,
                        user_id=system_user.id
                    )
                    logger.info("Successfully seeded database with sample video.")
                    
                    # Verify splices were created
                    splice_dir = os.path.join(SPLICES_DIR, "Sample_Perrala")
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
    yield

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
    root_path=API_ROOT_PATH,
    docs_url=None,
    redoc_url=None,
    contact=CONTACT_INFO,
    license_info=LICENSE_INFO,
    terms_of_service=TERMS_OF_SERVICE,
    openapi_tags=TAGS_METADATA,
)

configure_documentation(app)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/splices", StaticFiles(directory=SPLICES_DIR), name="splices")
app.mount("/mp3", StaticFiles(directory=UPLOAD_DIR_MP3), name="mp3")
app.mount("/mp4", StaticFiles(directory=UPLOAD_DIR_MP4), name="mp4")

app.include_router(auth.router)
app.include_router(users.router)

@app.post(
    "/video/add",
    response_model=_schemas.ResponseModel,
    tags=["Video Intake"],
    summary="Upload and preprocess a new media asset",
    description=(
        "Accepts MP4 or MP3 files, stores the raw asset, converts video to audio, "
        "generates splice waveforms, and seeds the labeling queue in a single transaction."
    ),
)
async def create_video(
    video_name: str,
    video_category: str,
    video_file: UploadFile = File(...),
    db: Session = Depends(_services.get_db),
):
    filename = video_file.filename
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in [".mp4", ".mp3"]:
        raise HTTPException(status_code=400, detail="Invalid document type. Only .mp4 and .mp3 are supported.")
    
    try:
        system_user = _services.get_user_by_email(db, "system@albaniansr.com")
        if not system_user:
             raise HTTPException(status_code=500, detail="System user not found")

        file_content = await video_file.read()
        updated_video = await _process_video_upload(
            video_name=video_name,
            video_category=video_category,
            file_content=file_content,
            filename=filename,
            db=db,
            user_id=system_user.id
        )
        
        return _schemas.ResponseModel(
            status="success",
            data=updated_video,
            message="Video created and processed successfully"
        )
    except Exception as e:
        logger.error(f"Error creating video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

def _get_public_path(file_path: str, include_version: bool = True) -> str:
    """Converts a filesystem path into the mounted static path and busts caches."""
    if not file_path:
        return file_path

    normalized_path = os.path.abspath(file_path)

    def _relativize(base_dir: str, mount_point: str) -> Optional[str]:
        if normalized_path.startswith(base_dir):
            relative_path = normalized_path[len(base_dir):]
            if not relative_path.startswith("/"):
                relative_path = "/" + relative_path
            return f"{mount_point}{relative_path}"
        return None

    public_path = None
    for directory, mount_point in (
        (SPLICES_DIR_ABS, "/splices"),
        (UPLOAD_DIR_MP3_ABS, "/mp3"),
        (UPLOAD_DIR_MP4_ABS, "/mp4"),
    ):
        public_path = _relativize(directory, mount_point)
        if public_path:
            break

    if not public_path:
        return normalized_path

    if include_version:
        try:
            version = int(os.path.getmtime(normalized_path))
            separator = "&" if "?" in public_path else "?"
            return f"{public_path}{separator}v={version}"
        except OSError as exc:
            logger.warning("Could not read modification time for %s: %s", normalized_path, exc)

    return public_path

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
            "path": _get_public_path(processed_splice.path)
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
            "path": _get_public_path(processed_splice.path)
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



