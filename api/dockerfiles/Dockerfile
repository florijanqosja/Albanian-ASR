# 
FROM python:3.9

# 
WORKDIR /code

# 
COPY ./dev/requirements.txt /code/requirements.txt
COPY ./dev/.env /code/.env

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

# 
COPY ./dev/api /code/app

VOLUME /code/app/mp4
VOLUME /code/app/splices
VOLUME /code/app/mp3

# 
EXPOSE 180
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "180"]