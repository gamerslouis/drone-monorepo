FROM python:3.9-slim

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

WORKDIR /app

COPY / ./

ENTRYPOINT ["python", "main.py"]