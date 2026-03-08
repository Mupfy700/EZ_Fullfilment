# EZ_Fullfilment
Fulfilment Automation for EZ Originals Online Shop

## 🧾 Lieferscheine verarbeiten
- Auf der Startseite kannst du zusätzlich zu den CSVs auch PDF-Lieferscheine hochladen (eine oder mehrere Dateien, mehrseitig möglich).
- Die Lieferscheine werden anhand der Bestellnummer (#) getrennt, nach der Reihenfolge in der erzeugten `_EZ_Originalz.csv` sortiert und als zusammenhängende PDF (`<Name>_Lieferscheine.pdf`) im `results/`-Ordner ausgegeben.
- Zusätzlich werden zehn PDFs erzeugt, sortiert nach LED-Design (SKUs aus `Lineitem sku`) plus `Personalisiert`: Personalisiert (`Tags` enthält `Product_Personalizer` oder Produktname enthält `Eigenes Design`), Marmor Warmweiß (`01010103W`), Marmor (Restfarben, `01010103*`), Schwarzer Marmor Warmweiß (`01010105W`), Schwarzer Marmor (Restfarben, `01010105*`), Kristall (`01010106`), Universum (`01010104`), Anthrazit (`10010105`), Schwarz (`10010104`), Rest (alles andere oder gemischt). Zubehör-SKUs (`9999999998`, `9999999999`, `G00000001`, `20269998`) werden ignoriert.
- Optional können auch Versandlabel-PDFs hochgeladen werden. Jede Seite ist ein Label mit Bestellnummer; sie werden identisch zu den Lieferscheinen nach Kategorien sortiert (`<Name>_Versandlabels_*.pdf`) und gelistet.

## 🚀 Deployment zur Google Cloud Run

Wenn du Änderungen am Code vorgenommen hast und diese live auf Google Cloud Run bereitstellen möchtest, folge dieser Anleitung:

### 🔧 Voraussetzungen

- [Docker](https://www.docker.com/) ist installiert.
- [Google Cloud SDK](https://cloud.google.com/sdk) ist installiert und eingerichtet (`gcloud init`).
- Du bist in deinem Google Cloud-Projekt angemeldet (z. B. `ez-fullfilment`).
- Das Projekt enthält ein gültiges `Dockerfile`.

---

### ✅ Schritt-für-Schritt Anleitung

#### 1. In das Projektverzeichnis wechseln

```bash
cd /Pfad/zum/Projekt/EZ_Fullfilment

2. Docker-Image mit korrekter Architektur bauen (für Cloud Run amd64)
docker build --platform=linux/amd64 -t ez_fullfilment .

3. Docker-Image für die Google Container Registry taggen
docker tag ez_fullfilment gcr.io/ez-fullfilment/ez_fullfilment

4. Image in die Google Container Registry pushen
docker push gcr.io/ez-fullfilment/ez_fullfilment

5. Deployment zur Google Cloud Run starten
gcloud run deploy ez-fullfilment \
  --image gcr.io/ez-fullfilment/ez_fullfilment \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated

--------------------------- Komplettes Command-Set: ---------------------------
gcloud config set project ez-fullfilment
gcloud auth application-default set-quota-project ez-fullfilment
docker build --platform=linux/amd64 -t ez_fullfilment .
docker tag ez_fullfilment gcr.io/ez-fullfilment/ez_fullfilment
docker push gcr.io/ez-fullfilment/ez_fullfilment
gcloud run deploy ez-fullfilment \
  --image gcr.io/ez-fullfilment/ez_fullfilment \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --service-account 412176435385-compute@developer.gserviceaccount.com \
  --set-env-vars GCS_UPLOAD_BUCKET=ez-fullfilment-uploads-412176435385,\
GCS_RESULTS_BUCKET=ez-fullfilment-results-412176435385,\
SIGNED_URL_EXPIRATION_SECONDS=3600,\
SIGNING_SERVICE_ACCOUNT=412176435385-compute@developer.gserviceaccount.com
-------------------------------------------------------------------------------



💡 Hinweise
Wichtig: Verwende --platform=linux/amd64, wenn du auf einem Apple Silicon (M1/M2) Mac arbeitest.
Bei jedem Deployment wird automatisch eine neue Revision erstellt.
Stelle sicher, dass deine Flask-App auf Port 8080 lauscht:
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
Wenn du gunicorn verwendest, sollte dein Dockerfile mit folgendem Befehl enden:
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]


--

## ☁️ Cloud-Upload (GCS, große Dateien, Datenschutz)

Um die 32 MB Request-Grenze zu umgehen, können die Dateien direkt in einen privaten Google Cloud Storage Bucket hochgeladen werden. Die App erzeugt signierte (kurzlebige) Upload-URLs; die Daten gehen nur in den Bucket und werden nach der Verarbeitung auf Wunsch wieder gelöscht.

1. Bucket vorbereiten  
   - Lege einen **privaten** Bucket an (keine Public Access).  
   - Verwende ein Service Account mit mind. `storage.objects.create`, `storage.objects.get`, `storage.objects.delete` auf dem Bucket.
2. Env-Variablen setzen (z. B. in Cloud Run):  
   - `UPLOAD_MODE=cloud`  
   - `GCS_BUCKET=<dein-bucket-name>`  
   - optional `SIGNED_URL_EXPIRATION=900` (Sekunden, Default 900/15 Min)  
   - optional `DELETE_UPLOADS_AFTER_PROCESSING=true` (Uploads nach dem Download aus GCS löschen)
3. Frontend-Flow  
   - Die Startseite zeigt „Cloud-Modus“.  
   - Beim Klick auf „Verarbeitung starten“ werden signierte URLs angefordert und die Dateien direkt in den Bucket hochgeladen.  
   - Danach lädt der Server die Dateien aus GCS, verarbeitet sie wie gewohnt und speichert die Ergebnisse in `results/`.
4. Datenschutz  
   - Bucket bleibt privat; signierte URLs laufen nach wenigen Minuten ab.  
   - Empfohlen: Cloud Run nur für authentifizierte Nutzer betreiben (IAM/IAP), damit niemand unberechtigt Upload-Links anfordern kann.

Im lokalen Modus (Standard, `UPLOAD_MODE=local`) bleibt das Verhalten unverändert.

## 🖥️ Lokales Testen des Skripts

Wenn du Änderungen am Code vorgenommen hast und diese lokal testen möchtest, bevor du sie auf Google Cloud Run deployst, folge dieser Anleitung:

### 🔧 Voraussetzungen

- [Docker](https://www.docker.com/) ist installiert.
- Dein Projekt enthält ein gültiges `Dockerfile`.

---

### ✅ Schritt-für-Schritt Anleitung

#### 1. Docker-Image lokal bauen

Baue das Docker-Image mit einem spezifischen Tag für die lokale Entwicklung:
docker build -t ez_fullfilment:dev .

#### 2. Docker-Container lokal starten
Starte das Docker-Image in einem Container und mappe den Port 8080:
docker run -p 8080:8080 ez_fullfilment:dev

- Der Parameter `-p 8080:8080` sorgt dafür, dass der Container auf deinem lokalen Port 8080 erreichbar ist.


--------------------------- Komplettes Command-Set: ---------------------------
docker build -t ez_fullfilment:dev .
docker run -p 8080:8080 ez_fullfilment:dev
-------------------------------------------------------------------------------

#### 3. Anwendung im Browser testen

Öffne [http://localhost:8080](http://localhost:8080) in deinem Browser, um die Anwendung zu testen.


💡 **Hinweise:**
- Stelle sicher, dass deine Flask-App auf Port 8080 lauscht:
  ```python
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
  ```
- Falls du `gunicorn` verwendest, sollte dein Dockerfile mit folgendem Befehl enden:
  ```dockerfile
  CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
  ```

Mit dieser Anleitung kannst du dein Skript lokal testen und sicherstellen, dass es fehlerfrei funktioniert, bevor du es auf Google Cloud Run deployst.
