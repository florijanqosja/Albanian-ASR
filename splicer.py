import glob, os
from databases import Database
database = Database("sqlite:///datab.db")
import asyncio
import librosa


# mp3path = "mp3/juli_tu_fol_shqip/juli.mp3"
# mp4filename = "mp4/juli_tu_fol_shqip/juli.mp4"

# async def func():
#     query = f"UPDATE video_table SET mp3_path = '{mp3path}' WHERE Vid_PATH = '{mp4filename}'" 
#     await database.execute(query=query)
# # os.system("python3 /home/ubuntu/.local/lib/python3.10/site-packages/pyAudioAnalysis/audioAnalysis.py silenceRemoval -i mp3/s1e2.mp3 --smoothing 0.2 --weight 0.1")

# asyncio.run(func())

mypath = "splices/juli/"

from os import walk




def populate_splice_table(mp3path, path):
    values = [
    ]
    f = []
    for (dirpath, dirnames, filenames) in walk(mypath):
        f.extend(filenames)
        break
    for filename in f:
        Sp_NAME = filename.replace(".wav", "")
        Sp_PATH = path + filename
        Sp_ORIGIN = mp3path
        # Sp_DURATION = librosa.get_duration(filename= mypath + filename )
        Sp_DURATION = librosa.get_duration(filename= path + filename)
        Sp_VALIDATION = "0"
        val = f"('{Sp_NAME}', '{Sp_PATH}', '{Sp_ORIGIN}', '{Sp_DURATION}', '{Sp_VALIDATION}')"
        values.append(val)
    values = tuple(values)
    values = str(values)
    values = values.replace('("', '')
    values = values.replace('")', '')
    values = values.replace('"', '')
    
    print(values)
    return values


# populate_splice_table("mp3/jjuu/juli.mp3", mypath)
async def funcc(ins):
    query = f"INSERT INTO splice_table (Sp_NAME, Sp_PATH, Sp_ORIGIN, Sp_DURATION, Sp_VALIDATION) VALUES {ins}"
    await database.execute(query=query)

asyncio.run(funcc(populate_splice_table("mp3/juli/irijuli.mp3", mypath)))