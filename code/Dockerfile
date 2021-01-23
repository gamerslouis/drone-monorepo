FROM python:3.9-slim

COPY requirements.txt main.py VERSION /app/

RUN pip install -r /app/requirements.txt

ENTRYPOINT ["python", "/app/main.py"]