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