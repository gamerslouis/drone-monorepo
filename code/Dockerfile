FROM arm64v8/python

COPY requirements.txt main.py VERSION /app/

RUN pip install -r /app/requirements.txt

ENTRYPOINT ["python", "/app/main.py"]