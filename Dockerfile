FROM python:3.9

# Arbeitsverzeichnis im Container setzen
WORKDIR /app

# Kopiere alle notwendigen Dateien in den Container
COPY . .

ENV PYTHONPATH=/app

# Installiere die Abhängigkeiten (inklusive Flask und Gunicorn)
RUN pip install --no-cache-dir -r requirements.txt

# Exponiere Port 8080 (Google Cloud Run erwartet, dass die App auf diesem Port läuft)
EXPOSE 8080

# Verwende Gunicorn, um die Flask-App zu starten
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "900", "app:app"]

