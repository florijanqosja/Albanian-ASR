# link of the video to be downloaded 
link="https://www.youtube.com/watch?v=7BBdVIEaQ-8&ab_channel=MiraKazhani"

  
from pytube import YouTube
import os
from databases import Database
from datetime import datetime
from moviepy.editor import *
from os import walk
from os import walk
import librosa
import sqlite3
import sys

# save the first argument (second position in argv list) to a variable
database_name = sys.argv[1]
# save the second argument to a variable
txt_file = sys.argv[2]
# print out the argument values
print('Arg 1:', database_name)
print('Arg 2:', txt_file)

database = sqlite3.connect(database_name)

def clean_name(name):
    chars = "qwertyuiopasdfghjklzxcvbnm 1234567890_"
    word = ""
    new_word = []
    for a in name:
        if a not in chars:
            print("found: ", a)
        else: new_word.append(a)
    for s in new_word:
        word = word + s
    return word

def Download(link):
    if link == "":
        print("no morte videos left")
    else:
        path = "vids/"
        youtubeObject = YouTube(link)

        youtubeObject = youtubeObject.streams.get_lowest_resolution()
        try:
            filename = youtubeObject.title
            filename = filename.lower()
            filename = filename.replace(" ", "_").replace("ç", "c").replace("ë", "e")
            filename = clean_name(filename)
            no_ext_filename = filename
            raw_filename = filename + ".mp4"
            filename = path + filename + ".mp4"
            os.system(f"mkdir ../fastapi/mp4/{no_ext_filename}")
            file_location = f"../fastapi/mp4/{no_ext_filename}/{raw_filename}"

            youtubeObject.download(filename = file_location)
        except:
            print("An error has occurred")
        print("Download is completed successfully")
        return raw_filename

# Download(link)
def get_next_link():
    infile = open(txt_file, 'r')
    firstLine = infile.readline().strip('\n')
    return firstLine


def delete_first_line():
    with open(txt_file, 'r+') as fp:
        # read an store all lines into list
        lines = fp.readlines()
        # move file pointer to the beginning of a file
        fp.seek(0)
        # truncate the file
        fp.truncate()
        # start writing lines except the first line
        # lines[1:] from line 2 to last line
        fp.writelines(lines[1:])




# delete_first_line()


def populate_splice_table(mp3path, path):
    values = []
    f = []
    for (dirpath, dirnames, filenames) in walk(path):
        f.extend(filenames)
        break
    for filename in f:
        Sp_NAME = filename.replace(".wav", "")
        Sp_PATH = path + filename
        Sp_PATH = Sp_PATH.replace("../fastapi/", "")
        Sp_ORIGIN = mp3path.replace("../fastapi/", "")
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
    os.system(f"mkdir ../fastapi/splices/{video_name}")  
    os.system("python3 /home/ubuntu/.local/lib/python3.10/site-packages/pyAudioAnalysis/audioAnalysis.py silenceRemoval -i " + filein + " --smoothing 0.2 --weight 0.1")
    os.system(f"mv ../fastapi/mp3/{video_name}/*.wav ../fastapi/splices/{video_name}")

 
def mp4tomp3(mp4filename, video_name, mp4filepath, mp3path):
    video = VideoFileClip(os.path.join(mp4filepath))
    
    print("ctu jemi tu e mar vijon:", os.path.join(mp4filepath))
    video.audio.write_audiofile(os.path.join(mp3path));
    splicer(mp3path, video_name)
 

def getime():
    now = str(datetime.now())
    return now

def fetch_data(video_name, video_category, video_file):
    video_name = str(video_name)
    print(video_name)
    os.system(f"mkdir ../fastapi/mp3/{video_name}")
    file_location = f"../fastapi/mp4/{video_name}/{video_file}"
    mp4filepath = "../fastapi/mp4/"  + video_name  + "/" + video_file
    mp3path = "../fastapi/mp3/" + video_name  + "/" + video_file.replace(".mp4", ".mp3" )
    original_video_name = video_name.replace("../fastapi/", "")
    original_file_location = file_location.replace("../fastapi/", "")
    original_mp3path = mp3path.replace("../fastapi/", "")
    original_mp4filepath = mp4filepath.replace("../fastapi/", "")
    
    query = f"INSERT INTO video_table (Vid_NAME, Vid_PATH, Vid_CATEGORY, Vid_UPLOAD_TIME, Vid_TO_MP3_STATUS, Vid_SPLICE_STATUS) VALUES ('{original_video_name}', '{original_file_location}', '{video_category}', '{getime()}', 'false', 'false')"
    database.execute(query)
    mp4tomp3(video_file, video_name, mp4filepath, mp3path)
    splicesDir = f"../fastapi/splices/{video_name}/"
    query = f"INSERT INTO splice_table (Sp_NAME, Sp_PATH, Sp_ORIGIN, Sp_DURATION, Sp_VALIDATION) VALUES {populate_splice_table(mp3path, splicesDir)}"
    database.execute(query)
    query = f"UPDATE video_table SET mp3_path = '{original_mp3path}', Vid_TO_MP3_STATUS = 'true' WHERE Vid_PATH = '{original_mp4filepath}'" 
    database.execute(query)
    database.commit()


while True:

    filename_video_link = Download(get_next_link())
    filename_video = filename_video_link.replace(".mp4", "")
    fetch_data(filename_video, "youtube_podcast", filename_video_link)
    delete_first_line()