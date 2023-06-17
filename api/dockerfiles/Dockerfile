FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY api /app/api