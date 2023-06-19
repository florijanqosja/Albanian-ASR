from email.policy import default
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from databases import Database
from typing import Union
# from tensorflow import keras
# import tensorflow as tf
import numpy as np
# import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import FileResponse
import glob, os
from moviepy.editor import *
import asyncio
from os import walk
import librosa
import random
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from pathlib import Path
import json
import csv
import ast
import os
os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"
import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Numeric, Integer, VARCHAR
from sqlalchemy.engine import result

  
# establish connections
engine = create_engine("sqlite:///datab.db")
  
# initialize the Metadata Object
meta = MetaData(bind=engine)
MetaData.reflect(meta)

database = Database("sqlite:///datab.db")

def populate_splice_table(mp3path, path):
    values = []
    f = []
    for (dirpath, dirnames, filenames) in walk(path):
        f.extend(filenames)
        break
    for filename in f:
        Sp_NAME = filename.replace(".wav", "")
        Sp_PATH = path + filename
        Sp_ORIGIN = mp3path
        Sp_DURATION = librosa.get_duration(filename= path + filename)
        Sp_VALIDATION = "0"
        # Sp_FILESIZE = Path(Sp_PATH).stat().st_size
        val = f"('{Sp_NAME}', '{Sp_PATH}', '{Sp_ORIGIN}', '{Sp_DURATION}', '{Sp_VALIDATION}')"
        values = list(values)
        values.append(val)
    values = tuple(values)
    values = str(values)
    values = values.replace('("', '')
    values = values.replace('")', '')
    values = values.replace('"', '')
    return values


def splicer(filein, video_name):
    os.system(f"mkdir splices/{video_name}")
    os.system("python3 /home/flori/.local/lib/python3.10/site-packages/pyAudioAnalysis/audioAnalysis.py silenceRemoval -i " + filein + " --smoothing 0.2 --weight 0.1")
    os.system(f"mv mp3/{video_name}/*.wav splices/{video_name}")

 
def mp4tomp3(mp4filename, video_name, mp4filepath, mp3path):
    video = VideoFileClip(os.path.join(mp4filepath))
    
    print("ctu jemi tu e mar vijon:", os.path.join(mp4filepath))
    video.audio.write_audiofile(os.path.join(mp3path));
    splicer(mp3path, video_name)
 

def getime():
    now = str(datetime.now())
    return now

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def database_connect():
    await database.connect()

@app.on_event("shutdown")
async def database_disconnect():
    await database.disconnect()

@app.post("/video/add")
async def fetch_data(video_name, video_category, video_file: UploadFile = File(...)):
    video_name = str(video_name)
    print(video_name)
    if video_file.content_type != "video/mp4":
        raise HTTPException(400, detail="Invalid document type")
    os.system(f"mkdir app/mp4/{video_name}")
    os.system(f"mkdir app/mp3/{video_name}")
    print(os.system('ls -l'))
    
    video_file_name = "".join(x for x in video_file.filename if x.isalnum()) + ".mp4"
    file_location = f"app/mp4/{video_name}/{video_file_name}"
    mp4filepath = "app/mp4/"  + video_name  + "/" + video_file_name
    mp3path = "app/mp3/" + video_name  + "/" + video_file_name.replace(".mp4", ".mp3" )
    with open(file_location, "wb+") as file_object:
        file_object.write(video_file.file.read())
    query = f"INSERT INTO video_table (Vid_NAME, Vid_PATH, Vid_CATEGORY, Vid_UPLOAD_TIME, Vid_TO_MP3_STATUS, Vid_SPLICE_STATUS) VALUES ('{video_name}', '{file_location}', '{video_category}', '{getime()}', 'false', 'false')"
    results = await database.execute(query=query)
    mp4tomp3(video_file_name, video_name, mp4filepath, mp3path)
    splicesDir = f"splices/{video_name}/"
    query = f"INSERT INTO splice_table (Sp_NAME, Sp_PATH, Sp_ORIGIN, Sp_DURATION, Sp_VALIDATION) VALUES {populate_splice_table(mp3path, splicesDir)}"
    await database.execute(query=query)
    query = f"UPDATE video_table SET mp3_path = '{mp3path}', Vid_TO_MP3_STATUS = 'true' WHERE Vid_PATH = '{mp4filepath}'" 
    await database.execute(query=query)
    return results

