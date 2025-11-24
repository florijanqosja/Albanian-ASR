import requests as req
import re


def transcribe (mp3file):
    import os
    from google.cloud import speech
    from google.protobuf.json_format import MessageToDict
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'client_service_key.json'
    speech_client = speech.SpeechClient()
    media_file_name_wav = mp3file
    with open(media_file_name_wav, 'rb') as f2:
        byte_data_wav = f2.read()
    audio_wav = speech.RecognitionAudio(content=byte_data_wav)
    config_wav = speech.RecognitionConfig( sample_rate_hertz=44100, enable_automatic_punctuation=True, language_code='sq-AL', audio_channel_count=2)
    response_standard_wav = speech_client.recognize( config=config_wav, audio=audio_wav)
    keyword_ideas_json = MessageToDict(response_standard_wav._pb)
    print(keyword_ideas_json)
    if "results" in keyword_ideas_json:
        print("still here")
        if not keyword_ideas_json["results"][0]["alternatives"][0]:
            print("retuning 0")
            return False
        transcript = keyword_ideas_json["results"][0]["alternatives"][0]["transcript"]
        print(transcript)
        accuracy = keyword_ideas_json["results"][0]["alternatives"][0]["confidence"]
        transcript = transcript.replace("'", "")
        return transcript , accuracy
    else:
        print("retuning 0")
        return False

def post_label(content, valida):
    
    clip_id = req.get("https://api.uneduashqiperine.com/clip_ID/")
    link = f'https://api.uneduashqiperine.com/audio/label/v2/{clip_id.text}/{content}?validation={valida}'
    print(link)
    return req.get(link)

def delete_reco():
    clip_id = req.get("https://api.uneduashqiperine.com/clip_ID/")
    url = f'https://api.uneduashqiperine.com/video/delete/{clip_id.text}'
    x = req.post(url)
    print(x.text)

    

def get_audio_link():
    domain = "../fastapi/"
    partial_clip_path = req.get("https://api.uneduashqiperine.com/audio/getsa")
    clip_path = domain + partial_clip_path.text.replace('"', '')
    print(clip_path)
    return clip_path

def get_splice_length():
    partial_clip_path = req.get("https://api.uneduashqiperine.com/audio/get_splice_length")
    clip_path = partial_clip_path.text.replace('"', '')
    clip_path = float(clip_path)
    print("the length of the splice is: ", clip_path)
    return clip_path

sp_length = get_splice_length()
track = 0
while True:
    if get_splice_length() > 10:
        print("skipping as splice too long", get_splice_length())
        delete_reco() 
    elif transcribe(get_audio_link()) == False:
        print("skipping as error")
        delete_reco()     
    else:
        a ,b =transcribe(get_audio_link())
        post_label(a,b)
        track = track + 1
        print(track)

# a ,b =transcribe(get_audio_link())
# # post_label(a,b)
# # track = track + 1
