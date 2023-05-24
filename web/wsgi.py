from flask import Flask, render_template, request, redirect, url_for
import requests as req
from pydub import AudioSegment
import os
from flask_navigation import Navigation
import collections
try:
    from collections import abc
    collections.MutableMapping = abc.MutableMapping
except:
    pass
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

nav = Navigation(app)

nav.Bar('top', [
    nav.Item('Record', 'hello3'),
    nav.Item('Validate', 'hello2'),
    nav.Item('Label', 'hello'),
    
])

def save_trimed_clip(link, StrtTime, EndTime):
    if (StrtTime == "" or EndTime == ""):
        aaa = print("skiping because limit not selected")
        return aaa
    StrtTime = int(StrtTime)
    EndTime = int(EndTime)
    sumin = EndTime + StrtTime
    print(sumin)
    
    if (sumin > 3):
        name_to_Load = "../fastapi/" + link.replace("https://api.uneduashqiperine.com/", "")
        print("this is where we see the type: ", type(EndTime), " : ", EndTime)
        sound = AudioSegment.from_wav(name_to_Load)
        extract = sound[StrtTime:EndTime]
        extract.export(name_to_Load, format="wav")
    else:
        print("skipped")

def delete_reco():
    clip_id = req.get("https://api.uneduashqiperine.com/clip_ID/")
    url = f'https://api.uneduashqiperine.com/video/delete/{clip_id.text}'
    x = req.post(url)
    print(x.text)

def delete_reco_validated():
    clip_id = validation_data()["Id"]
    url = f'https://api.uneduashqiperine.com/audio/delete/validated/{clip_id}'
    x = req.post(url)
    print(x.text)

def post_label(content, start, end, link):
    print(start)
    print(end)
    save_trimed_clip(link, start, end)
    clip_id = req.get("https://api.uneduashqiperine.com/clip_ID/")
    link = f'https://api.uneduashqiperine.com/audio/label/{clip_id.text}?label_content={content}'
    print(link)
    return req.get(link)

def post_label_validated(content, start, end, link):
    print(start)
    print(end)
    save_trimed_clip(link, start, end)
    clip_id = validation_data()["Id"]
    print("this is the clip id of the validated", clip_id)
    link = f'https://api.uneduashqiperine.com/audio/label/validated/{clip_id}?label_content={content}'
    print(link)
    return req.get(link)

domain = "https://api.uneduashqiperine.com/"


def get_audio_link():
    partial_clip_path = req.get("https://api.uneduashqiperine.com/audio/getsa")
    clip_path = domain + partial_clip_path.text.replace('"', '')
    return clip_path

def convert(seconds):
    # seconds = seconds % (24 * 3600)
    # hour = seconds // 3600
    # seconds %= 3600
    # minutes = seconds // 60
    # seconds %= 60
    # seconds = 331045

    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    print("%d:%02d:%02d" % (hours, minutes, seconds))
     
    return "%d:%02d:%02d" % (hours, minutes, seconds)

def sumOfLabeled ():
    partial_clip_path = req.get("https://api.uneduashqiperine.com/sumOfLabeled/")
    clip_path = partial_clip_path.text.replace('"', '')
    return clip_path

def sumOfUnLabeled ():
    partial_clip_path = req.get("https://api.uneduashqiperine.com/sumOfUnLabeled/")
    clip_path = partial_clip_path.text.replace('"', '')
    return clip_path

def sumOfLabeledDuration ():
    partial_clip_path = req.get("https://api.uneduashqiperine.com/sumOfLabeledDuration/")
    clip_path = partial_clip_path.text.replace('"', '')
    return convert(round(float(clip_path)))

def sumOfLabeledDurationValidated ():
    partial_clip_path = req.get("https://api.uneduashqiperine.com/sumOfLabeledDuration/validated")
    clip_path = partial_clip_path.text.replace('"', '')
    return convert(round(float(clip_path)))


def sumOfUnLabeledDuration ():
    partial_clip_path = req.get("https://api.uneduashqiperine.com/sumOfUnLabeledDuration/")
    clip_path = partial_clip_path.text.replace('"', '')
    return convert(round(float(clip_path)))

def progressPercentage ():
    c = float("%.2f" % float(sumOfUnLabeled()))
    b = float("%.2f" % float(sumOfLabeled()))
    a = float(b*100)/float(c+b)
    perc = ("%.2f" % a) + "%"

    return perc

def validationaudio ():
    textt = "tis is the text"
    # print("tis is the text")
    return textt

def validation_data():
    from google.protobuf.json_format import MessageToDict
    aresponse = req.get("https://api.uneduashqiperine.com/audio/get_validation_audio_link")
    response = aresponse.json()
    return response

def validation_data_plus():
    from google.protobuf.json_format import MessageToDict
    aresponse = req.get("https://api.uneduashqiperine.com/audio/get_validation_audio_link_plus")
    response = aresponse.json()
    return response



@app.route('/', methods=["POST", "GET"])
def hello():
    if request.method == "POST":
        if request.form['submit_button'] == 'submit':
            print(request.form["input_content"])
            label = request.form["input_content"]
            val_start = request.form["input_val1"]
            val_end = request.form["input_val2"]
            post_label(label, val_start, val_end, get_audio_link())
            return render_template("index.html", progressPercentage = progressPercentage(), audio_link = get_audio_link(), sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())
        elif request.form['submit_button'] == 'delete':
            delete_reco()
            return render_template("index.html", progressPercentage = progressPercentage(), audio_link = get_audio_link(), sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())
    else: 
        return render_template("index.html", progressPercentage = progressPercentage(), audio_link = get_audio_link(), sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())

@app.route('/validate', methods=["POST", "GET"])
def hello2():
    if request.method == "POST":
        if request.form['submit_button_validation'] == 'submit':
            print(request.form["input_content"])
            label = request.form["input_content"]
            val_start = request.form["input_val1"]
            val_end = request.form["input_val2"]
            post_label_validated(label, val_start, val_end, validation_data()["Path"])
            return render_template("finalvalidate.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())
        elif request.form['submit_button_validation'] == 'delete':
            delete_reco_validated()
            return render_template("finalvalidate.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())
    else: 
        return render_template("finalvalidate.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())

# @app.route('/test', methods=["POST", "GET"])
# def hello3():
#     if request.method == "POST":
#         if request.form['submit_button_validation'] == 'submit':
#             print("is is the vaue of input: ", request.form["asinput_val1"])

#             # print(request.form["input_content"])
#             # label = request.form["input_content"]
#             # val_start = request.form["input_val1"]
#             # val_end = request.form["input_val2"]
#             # post_label_validated(label, val_start, val_end, validation_data()["Path"])
#             return render_template("record.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())
#         elif request.form['stop_button_valid'] == 'submit':
#             print("is is the vaue of input: ", request.form["asinput_val1"])
#             # delete_reco_validated()
#             return render_template("record.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())
#     else: 
#         return render_template("record.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())

def wav_wdown ():

    import urllib.request
    urllib.request.urlretrieve("http://www.example.com/songs/mp3.mp3", "mp3.mp3")


@app.route('/test', methods=["POST", "GET"])
def hello3():
    if request.method == "POST":
        if request.form['submit_button_validation'] == 'submit':
            print("this is what is comming from the input hidden box", request.form["input_val1"])
            label = request.form["input_content"]
            val_start = request.form["input_val1"]
            val_end = request.form["input_val2"]
            # post_label_validated(label, val_start, val_end, validation_data()["Path"])
            return render_template("finalrecord.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())
        elif request.form['submit_button_validation'] == 'delete':
            print("this is what is comming from the input hidden box", request.form["input_val1"])
            return render_template("finalrecord.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())
    else: 
        return render_template("finalrecord.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())


@app.route('/newindex', methods=["POST", "GET"])
def hello4():
    if request.method == "POST":
        if request.form['submit_button_validation'] == 'submit':
            print("this is what is comming from the input hidden box", request.form["input_val1"])
            label = request.form["input_content"]
            val_start = request.form["input_val1"]
            val_end = request.form["input_val2"]
            # post_label_validated(label, val_start, val_end, validation_data()["Path"])
            return render_template("newindex.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())
        elif request.form['submit_button_validation'] == 'delete':
            print("this is what is comming from the input hidden box", request.form["input_val1"])
            return render_template("newindex.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())
    else: 
        return render_template("newindex.html", sumofLabeledDurationValidated = sumOfLabeledDurationValidated(), validationaudio = validation_data()["Label"], progressPercentage = progressPercentage(), audio_link = validation_data()["Path"], sumofLabeled = sumOfLabeled(), sumofUnLabeled = sumOfUnLabeled() , sumofLabeledDuration = sumOfLabeledDuration(), sumofUnLabeledDuration = sumOfUnLabeledDuration())
   


if __name__ == '__main__':
          app.run(host='0.0.0.0')