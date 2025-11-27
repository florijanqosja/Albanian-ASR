from pytube import Playlist, Channel

rl = "https://www.youtube.com/@GazetaDita2012/videos"

playlist = Channel(rl)

for video in playlist:
    print(video)
    # video.streams.\
    #     filter(type='video', progressive=True, file_extension='mp4').\
    #     order_by('resolution').\
    #     desc().\
    #     first().\
    #     download(cur_dir)