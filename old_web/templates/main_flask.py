from flask import Flask, render_template, request, redirect, url_for
import requests as req
app = Flask(__name__)

def delete_reco():
    clip_id = req.get("http://127.0.0.1:8000/clip_ID/")
    url = f'http://127.0.0.1:8000/video/delete/{clip_id.text}'
    x = req.post(url)
    print(x.text)

def post_label(content):
    clip_id = req.get("http://127.0.0.1:8000/clip_ID/")
    link = f'http://127.0.0.1:8000/audio/label/{clip_id.text}?label_content={content}'
    return req.put(link)

domain = "http://127.0.0.1:8000/"
# clip_id = req.get("http://127.0.0.1:8000/clip_ID/")
# partial_clip_path = req.get("http://127.0.0.1:8000/audio/getsa")
# clip_path = domain + partial_clip_path.text.replace('"', '')


@app.route('/', methods=["POST", "GET"])
def hello():
    partial_clip_path = req.get("http://127.0.0.1:8000/audio/getsa")
    clip_path = domain + partial_clip_path.text.replace('"', '')
    if request.method == "POST":
        if request.form['submit_button'] == 'submit':
            print(request.form["input_content"])
            label = request.form["input_content"]
            post_label(label)
            return render_template("index.html", audio_link = clip_path)
        elif request.form['submit_button'] == 'delete':
            delete_reco()
            return render_template("index.html", audio_link = clip_path)
    else: 
        return render_template("index.html", audio_link = clip_path)




if __name__ == "__name__":
    app.run(debug=True)