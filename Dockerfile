# Dockerfile
FROM python:3.10-slim


COPY find_duplicates.py /find_duplicates.py
COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

ENTRYPOINT ["python", "/find_duplicates.py"]