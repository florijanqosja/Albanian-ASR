from typing import TYPE_CHECKING, List
import fastapi as _fastapi
import sqlalchemy.orm as _orm
import sqlalchemy as _sql
from moviepy.editor import VideoFileClip
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from datetime import datetime
from sqlalchemy.orm import Session
import os
import librosa
import wave
from sqlalchemy import func, select
from fastapi.staticfiles import StaticFiles
from flask import send_from_directory
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from pydub import AudioSegment
from pydub.silence import split_on_silence


from .database import schemas as _schemas
from .database import services as _services
from .database import models as _models

app = FastAPI()

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

app = _fastapi.FastAPI()

_services._add_tables()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(f"splices", exist_ok=True)
app.mount("/splices", StaticFiles(directory="splices"), name="splices")

def splicer(filein, video_name, min_silence_len=500, silence_thresh=-30):
    os.makedirs(f"splices/{video_name}", exist_ok=True)
    audio = AudioSegment.from_file(filein)
    chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_len,  # minimum length of silence to be considered a split point in ms
        silence_thresh=silence_thresh  # silence threshold in dB
    )
    chunk_start = 0
    for i, chunk in enumerate(chunks):
        chunk_end = chunk_start + len(chunk)
        chunk.export(
            f"splices/{video_name}/videoplaybackmp4_{chunk_start/1000}-{chunk_end/1000}.wav",
            format="wav"
        )
        chunk_start = chunk_end


def mp4tomp3(mp4filename, video_name, mp4filepath, mp3path):
    video = VideoFileClip(os.path.join(mp4filepath))
    print("ctu jemi tu e mar vijon:", os.path.join(mp4filepath))
    video.audio.write_audiofile(os.path.join(mp3path))

def get_wav_duration(wav_location):
    with wave.open(wav_location, 'rb') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
    print("duration is: ", duration)
    return duration

@app.post("/video/add")
async def create_video(
    video_name: str,
    video_category: str,
    video_file: UploadFile = File(...),
    db: Session = Depends(_services.get_db),
):
    video_name = str(video_name)
    print(video_name)
    if video_file.content_type != "video/mp4":
        raise HTTPException(400, detail="Invalid document type")
    os.makedirs(f"mp4/{video_name}", exist_ok=True)
    os.makedirs(f"mp3/{video_name}", exist_ok=True)

    video_file_name = "".join(x for x in video_file.filename if x.isalnum()) + ".mp4"
    file_location = f"mp4/{video_name}/{video_file_name}"
    mp4filepath = f"mp4/{video_name}/{video_file_name}"
    mp3path = f"mp3/{video_name}/{video_file_name.replace('.mp4', '.mp3')}"
    with open(file_location, "wb+") as file_object:
        file_object.write(video_file.file.read())

    create_video_data = {
        "Vid_NAME": video_name,
        "Vid_PATH": file_location,
        "Vid_CATEGORY": video_category,
        "Vid_TO_MP3_STATUS": False,
        "Vid_SPLICE_STATUS": False,
    }
    await _services.create_video(video=create_video_data, db=db)

    mp4tomp3(mp4filename=video_file_name, video_name=video_name, mp4filepath=mp4filepath, mp3path=mp3path)

    splicer(filein=mp3path, video_name=video_name)

    splices_dir = f"splices/{video_name}"
    splice_files = os.listdir(splices_dir)
    splices_duration = []
    for splice_file in splice_files:
        splice_path = os.path.join(splices_dir, splice_file)
        duration = get_wav_duration(splice_path)  # Implement a function to calculate the duration of each splice

        create_splice_data = {
            "Sp_NAME": video_name,
            "Sp_PATH": splice_path,
            "Sp_ORIGIN": video_file_name,
            "Sp_DURATION": duration,
            "Sp_VALIDATION": 0,
            "Sp_LABEL": "",
        }
        await _services.create_splice(splice=create_splice_data, db=db)

    update_video_data = {
        "mp3_path": mp3path,
        "Vid_TO_MP3_STATUS": True,
        "Vid_SPLICE_STATUS": True,
    }
    updated_video = await _services.update_video(video_path=mp4filepath, update_data=update_video_data, db=db)

    return updated_video

@app.get("/audio/to_label")
async def getNextSpliceLink(db: Session = Depends(_services.get_db)):
    first_splice = await _services.get_first_splice(db)
    if first_splice is None:
        return None

    # Create a record in Splice_beeing_processed_table
    splice_being_processed_data = _schemas.CreateSpliceBeingProcessed(
        Sp_ID=first_splice.Sp_ID,
        Sp_NAME=first_splice.Sp_NAME,
        Sp_PATH=first_splice.Sp_PATH,
        Sp_LABEL=first_splice.Sp_LABEL,
        Sp_ORIGIN=first_splice.Sp_ORIGIN,
        Sp_DURATION=first_splice.Sp_DURATION,
        Sp_VALIDATION=first_splice.Sp_VALIDATION,
        Sp_STATUS='un_labeled',

    )
    processed_splice = await _services.create_splice_being_processed(splice_being_processed_data, db)

    # Delete the record from Labeled_splice_table
    await _services.delete_splice(first_splice.Sp_ID, db)

    return processed_splice

@app.get("/audio/to_validate")
async def getNextSpliceLink(db: _services.get_db = Depends()):
    first_splice = await _services.get_first_labeled_splice(db)
    if first_splice is None:
        return None

    # Create a record in Splice_beeing_processed_table
    splice_being_processed_data = _schemas.CreateSpliceBeingProcessed(
        Sp_ID=first_splice.Sp_ID,
        Sp_NAME=first_splice.Sp_NAME,
        Sp_PATH=first_splice.Sp_PATH,
        Sp_LABEL=first_splice.Sp_LABEL,
        Sp_ORIGIN=first_splice.Sp_ORIGIN,
        Sp_DURATION=first_splice.Sp_DURATION,
        Sp_VALIDATION=first_splice.Sp_VALIDATION,
        Sp_STATUS='labeled',
    )
    processed_splice = await _services.create_splice_being_processed(splice_being_processed_data, db)

    # Delete the record from Labeled_splice_table
    await _services.delete_labeled_splice(first_splice.Sp_ID, db)

    return processed_splice

@app.put("/audio/label")
async def label_splice(label_splice: _schemas.LabelSplice, db: Session = Depends(_services.get_db)):
    try:
        splice_being_processed = await _services.get_splice_being_processed(label_splice.Sp_ID, db)
        if splice_being_processed is None or splice_being_processed.Sp_STATUS != 'un_labeled':
            raise HTTPException(status_code=404, detail="Splice not found")
        
        update_splice_being_processed_data = {
            "Sp_ID": label_splice.Sp_ID,
            "Sp_LABEL": label_splice.Sp_LABEL,
            "Sp_VALIDATION": label_splice.Sp_VALIDATION or '0.95',
        }
        await _services.update_splice_being_processed(Sp_ID=label_splice.Sp_ID, data=update_splice_being_processed_data, db=db)

        labeled_splice_data = _schemas.CreateLabeledSplice(
            Sp_ID=splice_being_processed.Sp_ID,
            Sp_NAME=splice_being_processed.Sp_NAME,
            Sp_PATH=splice_being_processed.Sp_PATH,
            Sp_LABEL=splice_being_processed.Sp_LABEL,
            Sp_ORIGIN=splice_being_processed.Sp_ORIGIN,
            Sp_DURATION=splice_being_processed.Sp_DURATION,
            Sp_VALIDATION=splice_being_processed.Sp_VALIDATION,
        )
        await _services.create_labeled_splice(labeled_splice_data, db)

        await _services.delete_splice_being_processed(splice_being_processed, db)

        return {"message": "Splice labeled and moved successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/audio/validate")
async def validate_splice(validate_splice: _schemas.LabelSplice, db: Session = Depends(_services.get_db)):
    try:
        splice_being_processed = await _services.get_splice_being_processed(validate_splice.Sp_ID, db)
        if splice_being_processed is None or splice_being_processed.Sp_STATUS != 'labeled':
            raise HTTPException(status_code=404, detail="Splice not found")
        
        update_splice_being_processed_data = {
            "Sp_ID": validate_splice.Sp_ID,
            "Sp_LABEL": validate_splice.Sp_LABEL,
            "Sp_VALIDATION": validate_splice.Sp_VALIDATION or '1.0',
        }
        await _services.update_splice_being_processed(Sp_ID=validate_splice.Sp_ID, data=update_splice_being_processed_data, db=db)

        labeled_splice_data = _schemas.CreateHighQualityLabeledSplice(
            Sp_ID=splice_being_processed.Sp_ID,
            Sp_NAME=splice_being_processed.Sp_NAME,
            Sp_PATH=splice_being_processed.Sp_PATH,
            Sp_LABEL=splice_being_processed.Sp_LABEL,
            Sp_ORIGIN=splice_being_processed.Sp_ORIGIN,
            Sp_DURATION=splice_being_processed.Sp_DURATION,
            Sp_VALIDATION=splice_being_processed.Sp_VALIDATION,
        )
        await _services.create_high_quality_labeled_splice(labeled_splice_data, db)

        await _services.delete_splice_being_processed(splice_being_processed, db)

        return {"message": "Splice validated and moved successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/audio")
async def delete_splice(delete_splice: _schemas.DeleteSplice, db: Session = Depends(_services.get_db)):
    try:
        splice_being_processed = await _services.get_splice_being_processed(delete_splice.Sp_ID, db)
        if splice_being_processed is None:
            raise HTTPException(status_code=404, detail="Splice not found")

        await _services.delete_splice_being_processed(splice_being_processed, db)

        return {"message": "Splice deleted sucsessfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/getsa")
async def getNextSpliceLink(db: Session = Depends(_services.get_db)):
    splice = _models.Splice_table.__table__
    query = select([splice.c.Sp_PATH]).order_by(splice.c.Sp_ID).limit(1)
    result = db.execute(query).scalar()
    if result is None:
        return []
    return result

@app.get("/audio/get_validation_audio_link")
async def next_validation_data(db: Session = Depends(_services.get_db)):
    first_splice = db.query(_models.Labeled_splice_table).order_by(_models.Labeled_splice_table.Sp_ID).first()
    if first_splice is None:
        return None
    return first_splice

@app.get("/audio/get_clip_id/")
async def get_clip_id(db: Session = Depends(_services.get_db)):
    first_splice = db.query(_models.Splice_table).order_by(_models.Splice_table.Sp_ID).first()
    if first_splice is None:
        return None
    return first_splice.Sp_ID

@app.get("/audio/get_validation_audio_link_plus")
async def getNextSpliceLink(db: Session = Depends(_services.get_db)):
    first_splice = db.query(_models.Splice_table).order_by(_models.Splice_table.Sp_ID).first()
    if first_splice is None:
        return []
    return first_splice.Sp_PATH

@app.get("/audio/get_clip_id/")
async def get_clip_id(db: Session = Depends(_services.get_db)):
    first_splice = db.query(_models.Splice_table).order_by(_models.Splice_table.Sp_ID).first()
    if first_splice is None:
        return None
    return first_splice.Sp_ID

@app.get("/dataset_insight_info")
async def get_summary(db: Session = Depends(_services.get_db)):
    total_duration_labeled = db.query(func.sum(_models.Labeled_splice_table.Sp_DURATION.cast(_sql.Float))).scalar()
    total_duration_validated = db.query(func.sum(_models.High_quality_labeled_splice_table.Sp_DURATION.cast(_sql.Float))).scalar()
    total_duration_unlabeled = db.query(func.sum(_models.Splice_table.Sp_DURATION.cast(_sql.Float))).scalar()
    total_labeled = db.query(func.count(_models.Labeled_splice_table.Sp_ID)).scalar()
    total_unlabeled = db.query(func.count(_models.Splice_table.Sp_ID)).scalar()

    return {
        "total_duration_labeled": total_duration_labeled,
        "total_duration_validated": total_duration_validated,
        "total_duration_unlabeled": total_duration_unlabeled,
        "total_labeled": total_labeled,
        "total_unlabeled": total_unlabeled,
    }

