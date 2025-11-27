from pytube import Playlist, Channel


# playlist = Playlist('https://youtube.com/playlist?list=PLM8BAxfZddjzGLVM379Cswo0j8G3FFuYO')
playlist = Playlist('https://youtube.com/playlist?list=PLKoaE_gtE1r28tt6QmIBlqyNesoaGgreC')
# print(playlist.video_urls)

for a in playlist.video_urls:
    print(a)

