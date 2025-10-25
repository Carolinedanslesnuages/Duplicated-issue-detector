# Dockerfile
FROM python:3.10-slim

# Copie les fichiers DEPUIS la racine du dépôt VERS la racine de l'image
COPY find_duplicates.py /find_duplicates.py
COPY requirements.txt /requirements.txt # <-- Il cherche 'requirements.txt' ici

# Installe les dépendances DANS l'image
RUN pip install --no-cache-dir -r /requirements.txt

ENTRYPOINT ["python", "/find_duplicates.py"]