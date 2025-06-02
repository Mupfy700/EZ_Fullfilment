# EZ_Fullfilment
Fulfilment Automation for EZ Originals Online Shop


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


💡 Hinweise
Wichtig: Verwende --platform=linux/amd64, wenn du auf einem Apple Silicon (M1/M2) Mac arbeitest.
Bei jedem Deployment wird automatisch eine neue Revision erstellt.
Stelle sicher, dass deine Flask-App auf Port 8080 lauscht:
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
Wenn du gunicorn verwendest, sollte dein Dockerfile mit folgendem Befehl enden:
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]


--

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