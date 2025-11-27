# import requests as req

# textinn = "now from py"
# llink = f"https://api.uneduashqiperine.com/audio/slurm_test/{textinn}"
# reqinn = req.get(llink)
# print(reqinn.text)


seconds = 331045

minutes, seconds = divmod(seconds, 60)
hours, minutes = divmod(minutes, 60)

print("%d:%02d:%02d" % (hours, minutes, seconds))