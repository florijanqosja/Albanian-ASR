FROM tiangolo/uwsgi-nginx:python3.9

WORKDIR /code

COPY /requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg
RUN pip install --upgrade pip wheel setuptools requests

COPY ./web /code/app

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app.wsgi:app"]
