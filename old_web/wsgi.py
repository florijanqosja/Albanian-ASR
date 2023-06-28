import sys
from flask import Flask, render_template, request, redirect, url_for
import requests as req
from pydub import AudioSegment
import os
from flask_navigation import Navigation
from dotenv import dotenv_values
try:
    from collections.abc import Callable, Iterable # noqa
except ImportError:
    from collections import Callable, Iterable  # noqa
import collections 
if sys.version_info.major == 3 and sys.version_info.minor >= 10:

    from collections.abc import MutableMapping
else :
    from collections import MutableMapping

env_vars = dotenv_values()
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

nav = Navigation(app)

nav.Bar('top', [
    nav.Item('Record', 'record_page'),
    nav.Item('Validate', 'validation_page'),
    nav.Item('Label', 'main_page'),
    
])

API_DOMAIN = env_vars.get("API_DOMAIN")
FILE_ACCESS_DOMAIN = env_vars.get("FILE_ACCESS_DOMAIN")

def save_trimed_clip(link, StrtTime, EndTime):
    if (StrtTime == "" or EndTime == ""):
        aaa = print("skiping because limit not selected")
        return aaa
    StrtTime = int(StrtTime)
    EndTime = int(EndTime)
    sumin = EndTime + StrtTime
    print(sumin)
    
    if (sumin > 3):
        name_to_Load = "../fastapi/" + link.replace(API_DOMAIN, "")
        print("this is where we see the type: ", type(EndTime), " : ", EndTime)
        sound = AudioSegment.from_wav(name_to_Load)
        extract = sound[StrtTime:EndTime]
        extract.export(name_to_Load, format="wav")
    else:
        print("skipped")

def delete_reco(splice):
    endpoint = f"{API_DOMAIN}audio/"

    payload = {
        "Sp_ID": splice["Sp_ID"]
    }

    response = req.delete(endpoint, json=payload)

    if response.status_code == 200:
        data = response.json()
        message = data["message"]
        print(message)
    else:
        print("Error:", response.status_code)

def post_label(content, start, end, link):
    print(start)
    print(end)
    save_trimed_clip(link, start, end)
    url_endpoint = f"{API_DOMAIN}clip_ID/"
    clip_id = req.get(url_endpoint)
    link = f'{API_DOMAIN}audio/label/{clip_id.text}?label_content={content}'
    print(link)
    return req.get(link)

def post_label_validated(content, start, end, link):
    print(start)
    print(end)
    save_trimed_clip(link, start, end)
    clip_id = validation_data()["Id"]
    print("this is the clip id of the validated", clip_id)
    link = f'{API_DOMAIN}audio/label/validated/{clip_id}?label_content={content}'
    print(link)
    return req.get(link)

def get_audio_link():
    endpoint = f"{API_DOMAIN}audio/getsa"
    partial_clip_path = req.get(endpoint)
    clip_path = FILE_ACCESS_DOMAIN + partial_clip_path.text.replace('"', '')
    return clip_path

def get_summary_info():
    def convert(seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return "%d:%02d:%02d" % (hours, minutes, seconds)
    response = req.get(f"{API_DOMAIN}dataset_insight_info/")
    datas = response.json()
    summary_info = {
        "sumofLabeled": datas["total_labeled"] or 0,
        "sumofUnLabeled": datas["total_unlabeled"] or 0,
        "sumofLabeledDuration": convert(round(float(datas["total_duration_labeled"]))) or 0,
        "sumofLabeledDurationValidated": convert(round(float(datas["total_duration_validated"]))) or 0,
        "sumofUnLabeledDuration": convert(round(float(datas["total_duration_unlabeled"]))) or 0,
        "progressPercentage": "{:.2f}%".format((float("%.2f" % float(datas["total_labeled"])) * 100) / (float("%.2f" % float(datas["total_unlabeled"])) + float("%.2f" % float(datas["total_labeled"]))))
    }
    return summary_info

def validation_data():
    endpoint = f"{API_DOMAIN}audio/get_validation_audio_link"
    from google.protobuf.json_format import MessageToDict
    aresponse = req.get(endpoint)
    response = aresponse.json()
    return response

def validation_data_plus():
    endpoint = f"{API_DOMAIN}audio/get_validation_audio_link_plus"
    from google.protobuf.json_format import MessageToDict
    aresponse = req.get(endpoint)
    response = aresponse.json()
    return response

def get_splice_to_label():

    url = f"{API_DOMAIN}audio/to_label"
    response = req.get(url)
    if response.status_code == 200:
        data = response.json()
        if data is not None:
            return data
        else:
            return "No splice data available"
    else:
        return {"Error:": response.status_code}

def get_splice_to_validate():

    url = f"{API_DOMAIN}audio/to_validate"
    response = req.get(url)
    if response.status_code == 200:
        data = response.json()
        if data is not None:
            return data
        else:
            return "No splice data available"
    else:
        return {"Error:": response.status_code}


@app.route('/', methods=["POST", "GET"])
def main_page():
    splice = get_splice_to_label()
    if request.method == "POST":
        if request.form['submit_button'] == 'submit':
            print(request.form["input_content"])
            label = request.form["input_content"]
            val_start = request.form["input_val1"]
            val_end = request.form["input_val2"]
            post_label(label, val_start, val_end, (FILE_ACCESS_DOMAIN + splice['Sp_PATH']))
            summary_info = get_summary_info()
            return render_template("index.html", sumofLabeled=summary_info["sumofLabeled"], sumofUnLabeled=summary_info["sumofUnLabeled"], sumofLabeledDuration=summary_info["sumofLabeledDuration"], sumofLabeledDurationValidated=summary_info["sumofLabeledDurationValidated"], sumofUnLabeledDuration=summary_info["sumofUnLabeledDuration"], progressPercentage=summary_info["progressPercentage"], audio_link=get_audio_link())
        elif request.form['submit_button'] == 'delete':
            delete_reco(splice)
            summary_info = get_summary_info()
            return render_template("index.html", sumofLabeled=summary_info["sumofLabeled"], sumofUnLabeled=summary_info["sumofUnLabeled"], sumofLabeledDuration=summary_info["sumofLabeledDuration"], sumofLabeledDurationValidated=summary_info["sumofLabeledDurationValidated"], sumofUnLabeledDuration=summary_info["sumofUnLabeledDuration"], progressPercentage=summary_info["progressPercentage"], audio_link=get_audio_link())
    else:
        summary_info = get_summary_info()
        return render_template("index.html", sumofLabeled=summary_info["sumofLabeled"], sumofUnLabeled=summary_info["sumofUnLabeled"], sumofLabeledDuration=summary_info["sumofLabeledDuration"], sumofLabeledDurationValidated=summary_info["sumofLabeledDurationValidated"], sumofUnLabeledDuration=summary_info["sumofUnLabeledDuration"], progressPercentage=summary_info["progressPercentage"], audio_link=get_audio_link())



@app.route('/validate', methods=["POST", "GET"])
def validation_page():
    splice = get_splice_to_validate()   
    if request.method == "POST":
        if request.form['submit_button_validation'] == 'submit':
            print(request.form["input_content"])
            label = request.form["input_content"]
            val_start = request.form["input_val1"]
            val_end = request.form["input_val2"]
            post_label_validated(label, val_start, val_end, validation_data()["Path"])
            summary_info = get_summary_info()
            return render_template("finalvalidate.html", sumofLabeledDurationValidated=summary_info["sumofLabeledDurationValidated"], validationaudio=validation_data()["Sp_LABEL"], progressPercentage=summary_info["progressPercentage"], audio_link=validation_data()["Sp_PATH"], sumofLabeled=summary_info["sumofLabeled"], sumofUnLabeled=summary_info["sumofUnLabeled"], sumofLabeledDuration=summary_info["sumofLabeledDuration"], sumofUnLabeledDuration=summary_info["sumofUnLabeledDuration"])
        elif request.form['submit_button_validation'] == 'delete':
            delete_reco(splice)
            summary_info = get_summary_info()
            return render_template("finalvalidate.html", sumofLabeledDurationValidated=summary_info["sumofLabeledDurationValidated"], validationaudio=validation_data()["Sp_LABEL"], progressPercentage=summary_info["progressPercentage"], audio_link=validation_data()["Sp_PATH"], sumofLabeled=summary_info["sumofLabeled"], sumofUnLabeled=summary_info["sumofUnLabeled"], sumofLabeledDuration=summary_info["sumofLabeledDuration"], sumofUnLabeledDuration=summary_info["sumofUnLabeledDuration"])
    else: 
        summary_info = get_summary_info()
        return render_template("finalvalidate.html", sumofLabeledDurationValidated=summary_info["sumofLabeledDurationValidated"], validationaudio=validation_data()["Sp_LABEL"], progressPercentage=summary_info["progressPercentage"], audio_link=validation_data()["Sp_PATH"], sumofLabeled=summary_info["sumofLabeled"], sumofUnLabeled=summary_info["sumofUnLabeled"], sumofLabeledDuration=summary_info["sumofLabeledDuration"], sumofUnLabeledDuration=summary_info["sumofUnLabeledDuration"])

@app.route('/test', methods=["POST", "GET"])
def record_page():
    if request.method == "POST":
        if request.form['submit_button_validation'] == 'submit':
            print("this is what is coming from the input hidden box", request.form["input_val1"])
            label = request.form["input_content"]
            val_start = request.form["input_val1"]
            val_end = request.form["input_val2"]
            # post_label_validated(label, val_start, val_end, validation_data()["Path"])
            summary_info = get_summary_info()
            return render_template("finalrecord.html", sumofLabeledDurationValidated=summary_info["sumofLabeledDurationValidated"], validationaudio=validation_data()["Sp_LABEL"], progressPercentage=summary_info["progressPercentage"], audio_link=validation_data()["Sp_PATH"], sumofLabeled=summary_info["sumofLabeled"], sumofUnLabeled=summary_info["sumofUnLabeled"], sumofLabeledDuration=summary_info["sumofLabeledDuration"], sumofUnLabeledDuration=summary_info["sumofUnLabeledDuration"])
        elif request.form['submit_button_validation'] == 'delete':
            print("this is what is coming from the input hidden box", request.form["input_val1"])
            summary_info = get_summary_info()
            return render_template("finalrecord.html", sumofLabeledDurationValidated=summary_info["sumofLabeledDurationValidated"], validationaudio=validation_data()["Sp_LABEL"], progressPercentage=summary_info["progressPercentage"], audio_link=validation_data()["Sp_PATH"], sumofLabeled=summary_info["sumofLabeled"], sumofUnLabeled=summary_info["sumofUnLabeled"], sumofLabeledDuration=summary_info["sumofLabeledDuration"], sumofUnLabeledDuration=summary_info["sumofUnLabeledDuration"])
    else:
        summary_info = get_summary_info()
        return render_template("finalrecord.html", sumofLabeledDurationValidated=summary_info["sumofLabeledDurationValidated"], validationaudio=validation_data()["Sp_LABEL"], progressPercentage=summary_info["progressPercentage"], audio_link=validation_data()["Sp_PATH"], sumofLabeled=summary_info["sumofLabeled"], sumofUnLabeled=summary_info["sumofUnLabeled"], sumofLabeledDuration=summary_info["sumofLabeledDuration"], sumofUnLabeledDuration=summary_info["sumofUnLabeledDuration"])



if __name__ == '__main__':
          app.run(host='0.0.0.0')