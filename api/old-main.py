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


# def add_filesize():
#     dir_of_paths = []
#     sql = text("SELECT * FROM splice_table ORDER BY ROWID ASC LIMIT 1")
#     # result = engine.splice_table.query.first()
#     results = engine.execute(sql)

#     for record in results:
#         print(record.Sp_PATH)
#         dir_of_paths.append(record.Sp_PATH)
    
#     filesize = Path('fastapi/splices/testctu/splices/gjyshja_e_gezuar/billi_137.800-139.050.wav').stat().st_size
#     print("this is the filesize", filesize)

# def predict_word(f_path):

#     frame_length = 256
#     frame_step = 160
#     fft_length = 384
#     # f_path = "/home/ubuntu/Desktop/project/fastapi/totranscribe/resampled/15_02_2023_12_41_49.wav"

#     def encode_single_sample(wav_file, label):
#         ###########################################
#         ##  Process the Audio
#         ##########################################
#         # 1. Read wav file
#         # file = tf.io.read_file(wavs_path + wav_file + ".wav")
#         file = tf.io.read_file(wav_file)
#         # 2. Decode the wav file
#         audio, _ = tf.audio.decode_wav(file)
#         audio = tf.squeeze(audio, axis=-1)
#         # 3. Change type to float
#         audio = tf.cast(audio, tf.float32)
#         # 4. Get the spectrogram
#         spectrogram = tf.signal.stft(
#             audio, frame_length=frame_length, frame_step=frame_step, fft_length=fft_length
#         )
#         # 5. We only need the magnitude, which can be derived by applying tf.abs
#         spectrogram = tf.abs(spectrogram)
#         spectrogram = tf.math.pow(spectrogram, 0.5)
#         # 6. normalisation
#         means = tf.math.reduce_mean(spectrogram, 1, keepdims=True)
#         stddevs = tf.math.reduce_std(spectrogram, 1, keepdims=True)
#         spectrogram = (spectrogram - means) / (stddevs + 1e-10)
#         ###########################################
#         ##  Process the label
#         ##########################################
#         # 7. Convert label to Lower case
#         label = tf.strings.lower(label)
#         # 8. Split the label
#         label = tf.strings.unicode_split(label, input_encoding="UTF-8")
#         # 9. Map the characters in label to numbers
#         label = char_to_num(label)
#         # 10. Return a dict as our model is expecting two inputs
#         return spectrogram, label

#     def CTCLoss(y_true, y_pred):
#         # Compute the training-time loss value
#         batch_len = tf.cast(tf.shape(y_true)[0], dtype="int64")
#         input_length = tf.cast(tf.shape(y_pred)[1], dtype="int64")
#         label_length = tf.cast(tf.shape(y_true)[1], dtype="int64")

#         input_length = input_length * tf.ones(shape=(batch_len, 1), dtype="int64")
#         label_length = label_length * tf.ones(shape=(batch_len, 1), dtype="int64")

#         loss = keras.backend.ctc_batch_cost(y_true, y_pred, input_length, label_length)
#         return loss

#     model = keras.models.load_model('/home/ubuntu/Desktop/project/fastapi/models/finetune-saved-model-10-31.60.h5', custom_objects={'CTCLoss':                   
#     CTCLoss})

#     characters = ["a", "b", "c", "ç", "d", "dh", "e", "ë", "f", "g", "gj", "h", "i", "j", "k", "l", "ll", "m", "n", "nj", "o", "p", "q", "r", "rr", "s", "sh", "t", "th", "u", "v", "x", "xh", "y", "z", "zh", "'", "?", "!", " ", "-"]
#     char_to_num = keras.layers.StringLookup(vocabulary=characters, oov_token="")

#     num_to_char = keras.layers.StringLookup(
#         vocabulary=char_to_num.get_vocabulary(), oov_token="", invert=True
#     )
#     def decode_batch_predictions(pred):
#         input_len = np.ones(pred.shape[0]) * pred.shape[1]
#         # Use greedy search. For complex tasks, you can use beam search
#         results = keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0]
#         # Iterate over the results and get back the text
#         output_text = []
#         for result in results:
#             result = tf.strings.reduce_join(num_to_char(result)).numpy().decode("utf-8")
#             output_text.append(result)
#         return output_text


#     f_path_old = []
#     f_trans_old = []
#     for x in range(1):
#         f_path_old.append(f_path)
#         f_trans_old.append("florii")
                
#     llist = {"file_name": f_path_old, "normalized_transcription": f_trans_old}

#     df = pd.DataFrame(data=llist)

#     wsws = tf.data.Dataset.from_tensor_slices(
#         (list(df["file_name"]), list(df["normalized_transcription"]))
#     )
#     wsws = (
#         wsws.map(encode_single_sample, num_parallel_calls=tf.data.AUTOTUNE)
#         .padded_batch(1)
#         .prefetch(buffer_size=tf.data.AUTOTUNE)
#     )

#     predictions = []
#     for batch in wsws:
#         X , y = batch
#         batch_predictions = model.predict(X)
#         batch_predictions = decode_batch_predictions(batch_predictions)
#         predictions.extend(batch_predictions)
#     print(f"Prediction: {predictions[0]}")
#     return {predictions[0]}



# add_filesize()
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
    os.system(f"mkdir mp4/{video_name}")
    os.system(f"mkdir mp3/{video_name}")
    
    video_file_name = "".join(x for x in video_file.filename if x.isalnum()) + ".mp4"
    file_location = f"mp4/{video_name}/{video_file_name}"
    mp4filepath = "mp4/"  + video_name  + "/" + video_file_name
    mp3path = "mp3/" + video_name  + "/" + video_file_name.replace(".mp4", ".mp3" )
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


@app.post("/audio/add")
async def fetch_data(video_name, video_category, video_file: UploadFile = File(...)):
    video_name = str(video_name)
    print(video_name)
    # if video_file.content_type != "audio/mp3":
    #     raise HTTPException(400, detail="Invalid document type")
    # os.system(f"mkdir mp4/{video_name}")
    os.system(f"mkdir mp3/{video_name}")
    file_location = f"mp4/{video_name}/{video_file.filename}"
    mp4filepath = "mp4/"  + video_name  + "/" + video_file.filename
    mp3path = "mp3/" + video_name  + "/" + video_file.filename.replace(".mp4", ".mp3" )
    # with open(file_location, "wb+") as file_object:
    #     file_object.write(video_file.file.read())
    # query = f"INSERT INTO video_table (Vid_NAME, Vid_PATH, Vid_CATEGORY, Vid_UPLOAD_TIME, Vid_TO_MP3_STATUS, Vid_SPLICE_STATUS) VALUES ('{video_name}', '{file_location}', '{video_category}', '{getime()}', 'false', 'false')"
    # results = await database.execute(query=query)
    mp4tomp3(video_file.filename, video_name, mp4filepath, mp3path)
    splicesDir = f"splices/{video_name}/"
    query = f"INSERT INTO splice_table (Sp_NAME, Sp_PATH, Sp_ORIGIN, Sp_DURATION, Sp_VALIDATION) VALUES {populate_splice_table(mp3path, splicesDir)}"
    await database.execute(query=query)
    query = f"UPDATE video_table SET mp3_path = '{mp3path}', Vid_TO_MP3_STATUS = 'true' WHERE Vid_PATH = '{mp4filepath}'" 
    results = await database.execute(query=query)
    return results


file_path = "large-video-file.mp4"
randomId = random.randint(1,100)

# app.mount("/home/flori/Desktop/fypfloo/fastapi/splices", StaticFiles(directory="splices"), name="splices")
@app.get("/audio/getsa")
async def emer():
    sql = text("SELECT * FROM splice_table ORDER BY ROWID ASC LIMIT 1")
    # result = engine.splice_table.query.first()
    results = engine.execute(sql)

    for record in results:
        lista = []
        print(record.Sp_PATH)
        lista.append(record.Sp_PATH)

        # downloadlink =  FileResponse(path=record.Sp_PATH, filename=record, media_type='text/wav')
        # print(downloadlink)
    return lista[0]

    # query = "SELECT * FROM splice_table ORDER BY ROWID ASC LIMIT 1"
    # results = await database.fetch_one(query=query)

    return results

@app.get("/audio/get_splice_length")
async def emer():
    sql = text("SELECT * FROM splice_table ORDER BY ROWID ASC LIMIT 1")
    # result = engine.splice_table.query.first()
    results = engine.execute(sql)

    for record in results:
        lista = []
        print(record.Sp_DURATION)
        lista.append(record.Sp_DURATION)

        # downloadlink =  FileResponse(path=record.Sp_PATH, filename=record, media_type='text/wav')
        # print(downloadlink)
    return lista[0]

    # query = "SELECT * FROM splice_table ORDER BY ROWID ASC LIMIT 1"
    # results = await database.fetch_one(query=query)

    return results

@app.get("/audio/get_validation_audio_link_plus")
async def emer():
    sql = text("SELECT * FROM labeled_splice_table ORDER BY ROWID ASC LIMIT 2")
    results = engine.execute(sql)
    lista_path = []
    inde = 0
    for record in results:
        inde = inde + 1
        if inde == 2:
            print(record.Sp_PATH)
            lista_path.append("https://api.uneduashqiperine.com/" + record.Sp_PATH)
            lista_path.append(record.Sp_LABEL)
            lista_path.append(record.Sp_ID)
    ret_obj = {
        "Path": lista_path[0],
        "Label": lista_path[1],
        "Id": lista_path[2]

    }
    return ret_obj

@app.post("/uploadfile") 
async def create_upload_file(file: UploadFile = File(...)):
    name = file.filename
    typez = file.content_type
    print(name, typez)

@app.post("/uploadfile2") 
async def create_upload_file(dats):
    # name = file.filename
    # typez = file.content_type
    print(dats)
    return dats

# @app.post("/secondtry")
# async def create_file(file: bytes = File()):
#     print("file_size", len(file))

#     with open("mp4/", "wb+") as file_object:
#         file_object.write(file.filename.file.read())
#         print("saving the file here")
#     return {"file_size": len(file)}

@app.post("/secondtry")
async def create_file(file: bytes = File):
    print("file_size", len(file))

    with open("mp4/", "wb+") as file_object:
        file_object.write(file.filename.file.read())
        print("saving the file here")
    return {"file_size": len(file)}



def transcribe():
    pass


@app.post("/thirdtry")
async def create_upload_file(file_wav: UploadFile = File(...)):
    from datetime import datetime
    now = datetime.now()
    file_name = now.strftime("%d_%m_%Y_%H_%M_%S")
    path_to_save_original = f"totranscribe/original/{file_name}.wav"
    with open(path_to_save_original, "wb+") as file_object:
        file_object.write(file_wav.file.read())
    path_to_resampled = path_to_save_original.replace("original", "resampled")
    os.system(f"sox {path_to_save_original} -r 16000 {path_to_resampled}") 
    toreturn = predict_word(path_to_resampled)

    return toreturn


@app.post("/upload_model")
async def create_upload_file(mdoel_file: UploadFile = File(...)):
    filename_in = mdoel_file.filename
    path_to_save_original = f"models/{filename_in}"
    print(path_to_save_original)
    with open(path_to_save_original, "wb+") as file_object:
            file_object.write(mdoel_file.file.read())
    return path_to_save_original



@app.get("/audio/get_validation_audio_link")
async def emer():
    sql = text("SELECT * FROM labeled_splice_table ORDER BY ROWID ASC LIMIT 1")
    results = engine.execute(sql)
    lista_path = []
    for record in results:
        print(record.Sp_PATH)
        lista_path.append("https://api.uneduashqiperine.com/" + record.Sp_PATH)
        lista_path.append(record.Sp_LABEL)
        lista_path.append(record.Sp_ID)
    ret_obj = {
        "Path": lista_path[0],
        "Label": lista_path[1],
        "Id": lista_path[2]

    }
    return ret_obj


@app.get("/audio/label/validated/{clip_id}")
async def label_data(clip_id, label_content):
    query = f"SELECT * FROM labeled_splice_table WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query)
    print(result)
    query = f"UPDATE labeled_splice_table SET Sp_VALIDATION = '1' WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query)
    query = f"UPDATE labeled_splice_table SET Sp_LABEL = '{label_content}' WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query)
    query = f"INSERT INTO high_quality_labeled_splice_table SELECT * FROM labeled_splice_table WHERE Sp_ID = '{clip_id}'"
    await database.execute(query=query)
    query2 = f"DELETE FROM labeled_splice_table WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query2)
    return results


@app.get("/audio/label/{clip_id}")
async def label_data(clip_id, label_content, validation: Union[float, None] = None):
    query = f"SELECT * FROM splice_table WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query)
    print(result)
    if validation != "" :
        query = f"UPDATE splice_table SET Sp_VALIDATION = '{validation}' WHERE Sp_ID = '{clip_id}'"
        results = await database.execute(query=query)
    query = f"UPDATE splice_table SET Sp_LABEL = '{label_content}' WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query)
    query = f"INSERT INTO labeled_splice_table SELECT * FROM splice_table WHERE Sp_ID = '{clip_id}'"
    await database.execute(query=query)
    query2 = f"DELETE FROM splice_table WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query2)
    
    return results


@app.get("/audio/label/v2/{clip_id}/{label_content}")
async def label_data(clip_id, label_content, validation: Union[float, None] = None):
    query = f"SELECT * FROM splice_table WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query)
    print(result)
    if validation != "" :
        query = f"UPDATE splice_table SET Sp_VALIDATION = '{validation}' WHERE Sp_ID = '{clip_id}'"
        results = await database.execute(query=query)
    query = f"UPDATE splice_table SET Sp_LABEL = '{label_content}' WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query)
    query = f"INSERT INTO labeled_splice_table SELECT * FROM splice_table WHERE Sp_ID = '{clip_id}'"
    await database.execute(query=query)
    query2 = f"DELETE FROM splice_table WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query2)
    
    return results

    

@app.post("/video/delete/{clip_id}")
async def delete_clip(clip_id):
    query = f"INSERT INTO deleted_splice_table SELECT * FROM splice_table WHERE Sp_ID = '{clip_id}'"
    await database.execute(query=query)
    query2 = f"DELETE FROM splice_table WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query2)
    # results = 2
    return results


@app.post("/audio/delete/validated/{clip_id}")
async def delete_clip(clip_id):
    query = f"INSERT INTO deleted_splice_table SELECT * FROM labeled_splice_table WHERE Sp_ID = '{clip_id}'"
    await database.execute(query=query)
    query2 = f"DELETE FROM labeled_splice_table WHERE Sp_ID = '{clip_id}'"
    results = await database.execute(query=query2)
    # results = 2
    return results


@app.get("/clip_ID/")
async def get_clip_id():
    sql = text("SELECT * FROM splice_table ORDER BY ROWID ASC LIMIT 1")
    results = engine.execute(sql)
    for record in results:
        return record.Sp_ID


@app.get("/sumOfLabeledDuration/")
async def get_clip_id():
    sql = text("SELECT SUM(Sp_DURATION) FROM labeled_splice_table;")
    results = engine.execute(sql)
    print(result)
    for record in results:
        print(result)
        return record["SUM(Sp_DURATION)"]

@app.get("/sumOfLabeledDuration/validated")
async def get_clip_id():
    sql = text("SELECT SUM(Sp_DURATION) FROM high_quality_labeled_splice_table;")
    results = engine.execute(sql)
    print(result)
    for record in results:
        print(result)
        return record["SUM(Sp_DURATION)"]

@app.get("/sumOfUnLabeledDuration/")
async def get_clip_id():
    sql = text("SELECT SUM(Sp_DURATION) FROM splice_table;")
    results = engine.execute(sql)
    print(result)
    for record in results:
        print(result)
        return record["SUM(Sp_DURATION)"]

@app.get("/sumOfLabeled/")
async def get_clip_id():
    sql = text("SELECT COUNT(*) FROM labeled_splice_table;")
    results = engine.execute(sql)
    for record in results:
        return record["COUNT(*)"]

@app.get("/sumOfUnLabeled/")
async def get_clip_id():
    sql = text("SELECT COUNT(*) FROM splice_table;")
    results = engine.execute(sql)
    for record in results:
        return record["COUNT(*)"]


@app.get("/add_training_data/{datas}")
async def post_datas(datas):
    datas = str(datas).replace("'", '"')
    print(datas)
    datas = str(datas).replace("'", '"')
    print(datas)
    print(type(datas))
    
    a = json.loads("r" + datas)
    # a = ast.literal_eval(a)
    f = open('training_datas.csv', 'a', newline='')
    writer = csv.writer(f)
    lline = list(a.items())
    index_minus_1 = int(len(a)-1)
    if a["publish_type"] == 0:
        print("doing 1")
        writer.writerow(["----------------"])
        writer.writerow(["---------New Model Training-------"])
        writer.writerow(["----------------"])
        writer.writerow(lline[-index_minus_1:])
    if a["publish_type"] == 1:
        print("doing 2")
        writer.writerow(["----------------"])
        writer.writerow(["---------More Epoch-------"])
        writer.writerow(lline[-index_minus_1:])
    if a["publish_type"] == 2:
        print("doing 3")
        writer.writerow(lline[-index_minus_1:])
    if a["publish_type"] == 3:
        print("doing 4")
        print("this is what comes: ", lline[-1])
        # writer.writerow(lline[-index_minus_1:])
    f.close()
    return index_minus_1