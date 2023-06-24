from typing import TYPE_CHECKING, List
import fastapi as _fastapi
import sqlalchemy.orm as _orm
import sqlalchemy as _sql
from moviepy.editor import VideoFileClip
import os
from pyAudioAnalysis import audioSegmentation
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from datetime import datetime
from sqlalchemy.orm import Session
import os
import librosa
import wave
from sqlalchemy import func, select

from .database import schemas as _schemas
from .database import services as _services
from .database import models as _models

app = FastAPI()

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

app = _fastapi.FastAPI()
_services._add_tables()

def splicer(filein, video_name):
    os.system(f"mkdir splices")
    os.system(f"mkdir splices/{video_name}")
    os.system("python3 /usr/local/lib/python3.9/site-packages/pyAudioAnalysis/audioAnalysis.py silenceRemoval -i " + filein + " --smoothing 0.2 --weight 0.1")
    os.system(f"mv mp3/{video_name}/*.wav splices/{video_name}")

def mp4tomp3(mp4filename, video_name, mp4filepath, mp3path):
    video = VideoFileClip(os.path.join(mp4filepath))
    
    print("ctu jemi tu e mar vijon:", os.path.join(mp4filepath))
    video.audio.write_audiofile(os.path.join(mp3path))
    # splicer(mp3path, video_name)

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


@app.get("/audio/getsa")
async def getNextSpliceLink(db: Session = Depends(_services.get_db)):
    splice = _models.Splice_table.__table__
    query = select([splice.c.Sp_PATH]).order_by(splice.c.Sp_ID).limit(1)
    result = db.execute(query).scalar()
    if result is None:
        return []
    return [result]

@app.get("/audio/get_validation_audio_link_plus")
async def getNextSpliceLink(db: Session = Depends(_services.get_db)):
    first_splice = db.query(_models.Splice_table).order_by(_models.Splice_table.Sp_ID).first()
    if first_splice is None:
        return []
    return [first_splice.Sp_PATH]

@app.get("/audio/get_clip_id/")
async def get_clip_id(db: Session = Depends(_services.get_db)):
    first_splice = db.query(_models.Splice_table).order_by(_models.Splice_table.Sp_ID).first()
    if first_splice is None:
        return None
    return first_splice.Sp_ID

@app.get("/sumOfLabeledDuration/")
async def get_sum_of_labeled_duration(db: Session = Depends(_services.get_db)):
    total_duration = db.query(func.sum(_models.Labeled_splice_table.Sp_DURATION.cast(_sql.Float))).scalar()
    return total_duration

@app.get("/sumOfLabeledDuration/validated")
async def get_sum_of_labeled_duration_validated(db: Session = Depends(_services.get_db)):
    total_duration = db.query(func.sum(_models.High_quality_labeled_splice_table.Sp_DURATION.cast(_sql.Float))).scalar()
    return total_duration

@app.get("/sumOfUnLabeledDuration/")
async def get_sum_of_unlabeled_duration(db: Session = Depends(_services.get_db)):
    total_duration = db.query(func.sum(_models.Splice_table.Sp_DURATION.cast(_sql.Float))).scalar()
    return total_duration

@app.get("/sumOfLabeled/")
async def get_sum_of_labeled(db: Session = Depends(_services.get_db)):
    count = db.query(func.count(_models.Labeled_splice_table.Sp_ID)).scalar()
    return count

@app.get("/sumOfUnLabeled/")
async def get_sum_of_unlabeled(db: Session = Depends(_services.get_db)):
    count = db.query(func.count(_models.Splice_table.Sp_ID)).scalar()
    return count
