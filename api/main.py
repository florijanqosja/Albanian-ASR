import logging
import os
import wave
from contextlib import asynccontextmanager
from typing import Optional

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

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
UPLOAD_DIR_MP4 = "mp4"
UPLOAD_DIR_MP3 = "mp3"
SPLICES_DIR = "splices"
SAMPLE_FILE_PATH = "sample_perrala.mp3"
DOCKER_SAMPLE_PATH = "/code/sample_perrala.mp3"

# Ensure directories exist
for directory in [UPLOAD_DIR_MP4, UPLOAD_DIR_MP3, SPLICES_DIR]:
    os.makedirs(directory, exist_ok=True)

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
                user_id=user_id
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
        # Seed Users
        import uuid
        system_user = _services.get_user_by_email(db, "system@albaniansr.com")
        if not system_user:
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

        anon_user = _services.get_user_by_email(db, "anonymous@albaniansr.com")
        if not anon_user:
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

        # Seed database if empty
        existing_video = db.query(_models.Video).first()
        if not existing_video:
            logger.info("Database is empty. Attempting to seed...")
            
            seed_file_path = None
            if os.path.exists(DOCKER_SAMPLE_PATH):
                seed_file_path = DOCKER_SAMPLE_PATH
            elif os.path.exists(SAMPLE_FILE_PATH):
                seed_file_path = SAMPLE_FILE_PATH
            
            if seed_file_path:
                try:
                    with open(seed_file_path, "rb") as f:
                        file_content = f.read()
                    
                    # We use the processing function to ensure the seed data is fully functional
                    await _process_video_upload(
                        video_name="Sample Perrala",
                        video_category="Story",
                        file_content=file_content,
                        filename="sample_perrala.mp3",
                        db=db,
                        user_id=system_user.id
                    )
                    logger.info("Successfully seeded database with sample video.")
                except Exception as e:
                    logger.error(f"Failed to seed database: {e}")
            else:
                logger.warning("Sample file not found. Skipping seed.")
    except Exception as e:
        logger.error(f"Error during startup seeding: {e}")
    finally:
        db.close()
    yield

app = FastAPI(
    title="Albanian ASR API",
    description="Backend API for Albanian Automatic Speech Recognition dataset collection.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/splices", StaticFiles(directory=SPLICES_DIR), name="splices")

app.include_router(auth.router)
app.include_router(users.router)

@app.post("/video/add", response_model=_schemas.ResponseModel)
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

@app.get("/audio/to_label", response_model=_schemas.ResponseModel)
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
            user_id=first_splice.user_id
        )
        processed_splice = await _services.create_splice_being_processed(splice_being_processed_data, db)
        await _services.delete_splice(first_splice.id, db)

        return _schemas.ResponseModel(
            status="success",
            data=processed_splice,
            message="Audio retrieved for labeling"
        )
    except Exception as e:
        logger.error(f"Error retrieving audio to label: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audio for labeling")

@app.get("/audio/to_validate", response_model=_schemas.ResponseModel)
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
            user_id=first_splice.user_id,
            labeler_id=first_splice.user_id
        )
        processed_splice = await _services.create_splice_being_processed(splice_being_processed_data, db)
        await _services.delete_labeled_splice(first_splice.id, db)

        return _schemas.ResponseModel(
            status="success",
            data=processed_splice,
            message="Audio retrieved for validation"
        )
    except Exception as e:
        logger.error(f"Error retrieving audio to validate: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audio for validation")

async def _label_splice_logic(label_splice: _schemas.LabelSplice, db: Session, user_id: str):
    if label_splice.start is not None and label_splice.end is not None:
        logger.info(f"Cutting audio from {label_splice.start} to {label_splice.end}")
        
    splice_being_processed = await _services.get_splice_being_processed(label_splice.id, db)
    if not splice_being_processed or splice_being_processed.status != 'un_labeled':
        raise HTTPException(status_code=404, detail="Splice not found or invalid status")
    
    update_data = {
        "id": label_splice.id,
        "label": label_splice.label,
        "validation": label_splice.validation or '0.95',
    }
    await _services.update_splice_being_processed(splice_id=label_splice.id, data=update_data, db=db)

    labeled_splice_data = _schemas.LabeledSpliceCreate(
        name=splice_being_processed.name,
        path=splice_being_processed.path,
        label=label_splice.label,
        origin=splice_being_processed.origin,
        duration=splice_being_processed.duration,
        validation=label_splice.validation or '0.95',
        user_id=user_id
    )
    await _services.create_labeled_splice(labeled_splice_data, db)
    await _services.delete_splice_being_processed(splice_being_processed, db)

    return _schemas.ResponseModel(status="success", message="Splice labeled and moved successfully")

@app.put("/audio/label", response_model=_schemas.ResponseModel)
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

@app.put("/audio/label/anonymous", response_model=_schemas.ResponseModel)
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

async def _validate_splice_logic(validate_splice: _schemas.LabelSplice, db: Session, user_id: str):
    if validate_splice.start is not None and validate_splice.end is not None:
        logger.info(f"Cutting audio from {validate_splice.start} to {validate_splice.end}")

    splice_being_processed = await _services.get_splice_being_processed(validate_splice.id, db)
    if not splice_being_processed or splice_being_processed.status != 'labeled':
        raise HTTPException(status_code=404, detail="Splice not found or invalid status")
    
    update_data = {
        "id": validate_splice.id,
        "label": validate_splice.label,
        "validation": validate_splice.validation or '1.0',
    }
    await _services.update_splice_being_processed(splice_id=validate_splice.id, data=update_data, db=db)

    hq_splice_data = _schemas.HighQualityLabeledSpliceCreate(
        name=splice_being_processed.name,
        path=splice_being_processed.path,
        label=validate_splice.label,
        origin=splice_being_processed.origin,
        duration=splice_being_processed.duration,
        validation=validate_splice.validation or '1.0',
        user_id=user_id,
        labeler_id=splice_being_processed.labeler_id
    )
    await _services.create_high_quality_labeled_splice(hq_splice_data, db)
    await _services.delete_splice_being_processed(splice_being_processed, db)

    return _schemas.ResponseModel(status="success", message="Splice validated and moved successfully")

@app.put("/audio/validate", response_model=_schemas.ResponseModel)
async def validate_splice(
    validate_splice: _schemas.LabelSplice, 
    db: Session = Depends(_services.get_db),
    current_user: _schemas.User = Depends(auth.get_current_user)
):
    try:
        return await _validate_splice_logic(validate_splice, db, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating splice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/audio/validate/anonymous", response_model=_schemas.ResponseModel)
async def validate_splice_anonymous(
    validate_splice: _schemas.LabelSplice, 
    db: Session = Depends(_services.get_db)
):
    try:
        anon_user = _services.get_user_by_email(db, "anonymous@albaniansr.com")
        if not anon_user:
             raise HTTPException(status_code=500, detail="Anonymous user not found")
        return await _validate_splice_logic(validate_splice, db, anon_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating splice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/audio", response_model=_schemas.ResponseModel)
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
            user_id=splice_being_processed.user_id
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

@app.get("/audio/getsa", response_model=_schemas.ResponseModel)
async def get_audio_sample(db: Session = Depends(_services.get_db)):
    # Optimized query using ORM
    path = db.query(_models.Splice.path).order_by(_models.Splice.id).scalar()
    if not path:
        return _schemas.ResponseModel(status="success", data=[], message="No audio sample found")
    return _schemas.ResponseModel(status="success", data=path, message="Audio sample retrieved")

@app.get("/audio/get_validation_audio_link", response_model=_schemas.ResponseModel)
async def next_validation_data(db: Session = Depends(_services.get_db)):
    first_splice = db.query(_models.LabeledSplice).order_by(_models.LabeledSplice.id).first()
    if not first_splice:
        return _schemas.ResponseModel(status="success", message="No validation audio found")
    return _schemas.ResponseModel(status="success", data=first_splice, message="Validation audio retrieved")

@app.get("/audio/get_clip_id/", response_model=_schemas.ResponseModel)
async def get_clip_id(db: Session = Depends(_services.get_db)):
    first_splice_id = db.query(_models.Splice.id).order_by(_models.Splice.id).scalar()
    if not first_splice_id:
        return _schemas.ResponseModel(status="success", message="No clip ID found")
    return _schemas.ResponseModel(status="success", data=first_splice_id, message="Clip ID retrieved")

@app.get("/audio/get_validation_audio_link_plus", response_model=_schemas.ResponseModel)
async def get_validation_audio_link_plus(db: Session = Depends(_services.get_db)):
    first_splice_path = db.query(_models.Splice.path).order_by(_models.Splice.id).scalar()
    if not first_splice_path:
        return _schemas.ResponseModel(status="success", data=[], message="No validation audio link found")
    return _schemas.ResponseModel(status="success", data=first_splice_path, message="Validation audio link retrieved")

@app.get("/dataset_insight_info", response_model=_schemas.ResponseModel)
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



