from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import json
import os
import shutil
import tempfile
import zipfile
import uuid
from datetime import timedelta
from typing import List, Optional

import google.auth
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request
from google.cloud import storage
from werkzeug.utils import secure_filename
from scripts.run_fullfilment import main



app = Flask(__name__)
RESULT_FOLDER = "results"
STATS_FILE = os.path.join(RESULT_FOLDER, "stats.json")
os.makedirs(RESULT_FOLDER, exist_ok=True)
DEFAULT_STATS = {
    "upload_order_count": 0,
    "processed_order_count": 0,
    "upload_delivery_notes_page_count": 0,
    "upload_delivery_notes_order_count": 0,
    "processed_delivery_notes_page_count": 0,
    "processed_delivery_notes_order_count": 0,
    "upload_shipping_labels_count": 0,
    "processed_shipping_labels_count": 0,
}

GCS_UPLOAD_BUCKET = os.environ.get("GCS_UPLOAD_BUCKET")
GCS_RESULTS_BUCKET = os.environ.get("GCS_RESULTS_BUCKET", GCS_UPLOAD_BUCKET)
SIGNED_URL_EXPIRATION_SECONDS = int(os.environ.get("SIGNED_URL_EXPIRATION_SECONDS", "3600"))
SIGNING_SERVICE_ACCOUNT = os.environ.get("SIGNING_SERVICE_ACCOUNT")
STORAGE_CLIENT = storage.Client() if GCS_UPLOAD_BUCKET else None


def _gcs_enabled():
    return bool(GCS_UPLOAD_BUCKET)


def _gcs_blob(bucket_name: str, object_name: str):
    if not STORAGE_CLIENT or not bucket_name:
        raise RuntimeError("GCS ist nicht konfiguriert. Bitte GCS_UPLOAD_BUCKET setzen.")
    return STORAGE_CLIENT.bucket(bucket_name).blob(object_name)



def _signing_context():
    """
    Besorgt Credentials + Service-Account-Email zum Signieren über IAM
    (funktioniert ohne privaten Schlüssel in Cloud Run).
    """
    if not STORAGE_CLIENT:
        raise RuntimeError("GCS ist nicht konfiguriert.")

    # Basis-Credentials (in Cloud Run: Service Account der Cloud-Run-Instanz)
    base_creds, _ = google.auth.default()
    if base_creds and getattr(base_creds, "expired", False):
        base_creds.refresh(Request())

    sa_email = None

    # 1) Versuch: E-Mail direkt aus den Basis-Credentials (Cloud Run SA)
    if hasattr(base_creds, "service_account_email"):
        sa_email = base_creds.service_account_email

    # 2) Versuch: SIGNING_SERVICE_ACCOUNT nur verwenden, wenn es wie eine Mail aussieht
    if (not sa_email or sa_email == "default") and SIGNING_SERVICE_ACCOUNT:
        if "@" in SIGNING_SERVICE_ACCOUNT:
            sa_email = SIGNING_SERVICE_ACCOUNT

    # 3) Versuch: Service-Account-Mail des Storage-Clients holen
    if (not sa_email or sa_email == "default"):
        try:
            sa_email = STORAGE_CLIENT.get_service_account_email()
        except Exception:
            pass

    # Wenn wir hier immer noch keine brauchbare Mail haben → harter Fehler
    if not sa_email or sa_email == "default":
        raise RuntimeError(
            "Service Account für Signed URLs nicht gefunden oder ungültig. "
            "Bitte SIGNING_SERVICE_ACCOUNT als gültige Service-Account-E-Mail setzen "
            "oder den Cloud-Run-Service-Account korrekt konfigurieren."
        )

    # Credentials, die intern die IAM Credentials API (signBytes) nutzen
    signing_creds = impersonated_credentials.Credentials(
        source_credentials=base_creds,
        target_principal=sa_email,
        target_scopes=["https://www.googleapis.com/auth/devstorage.read_write"],
        lifetime=300,
    )

    return signing_creds, sa_email




def _generate_signed_upload_url(bucket_name: str, object_name: str, content_type: str):
    blob = _gcs_blob(bucket_name, object_name)
    signing_creds, sa_email = _signing_context()
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(seconds=SIGNED_URL_EXPIRATION_SECONDS),
        method="PUT",
        content_type=content_type or "application/octet-stream",
        service_account_email=sa_email,
        credentials=signing_creds,
    )

def _generate_signed_download_url(bucket_name: str, object_name: str):
    blob = _gcs_blob(bucket_name, object_name)
    signing_creds, sa_email = _signing_context()
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(seconds=SIGNED_URL_EXPIRATION_SECONDS),
        method="GET",
        service_account_email=sa_email,
        credentials=signing_creds,
    )


def _upload_file_to_gcs(local_path: str, bucket_name: str, object_name: str, content_type: Optional[str] = None):
    blob = _gcs_blob(bucket_name, object_name)
    blob.upload_from_filename(local_path, content_type=content_type)
    return f"gs://{bucket_name}/{object_name}"


def _download_objects(object_paths: List[str], bucket_name: str, destination_dir: str) -> List[str]:
    os.makedirs(destination_dir, exist_ok=True)
    local_files: List[str] = []
    for object_path in object_paths:
        filename = os.path.basename(object_path)
        local_path = os.path.join(destination_dir, filename)
        blob = _gcs_blob(bucket_name, object_path)
        blob.download_to_filename(local_path)
        local_files.append(local_path)
    return local_files


def _list_result_files(session_id: str):
    """Listet die Dateien in GCS für einen Lauf auf und liefert Name -> signed URL."""
    if not _gcs_enabled():
        return {}, []

    prefix = f"results/{session_id}/"
    bucket = STORAGE_CLIENT.bucket(GCS_RESULTS_BUCKET)
    files = {}
    ordered_names = []
    for blob in bucket.list_blobs(prefix=prefix):
        if blob.name.endswith("/") or blob.name.endswith("stats.json"):
            continue
        filename = os.path.basename(blob.name)
        files[filename] = _generate_signed_download_url(GCS_RESULTS_BUCKET, blob.name)
        ordered_names.append(filename)
    return files, ordered_names


def _load_stats_from_gcs(session_id: str):
    if not _gcs_enabled():
        return DEFAULT_STATS.copy()
    try:
        stats_blob = _gcs_blob(GCS_RESULTS_BUCKET, f"results/{session_id}/stats.json")
        if not stats_blob.exists():
            return DEFAULT_STATS.copy()
        content = stats_blob.download_as_text()
        return json.loads(content)
    except Exception as exc:
        print(f"Statistiken aus GCS konnten nicht geladen werden: {exc}")
        return DEFAULT_STATS.copy()


def _guess_content_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".csv"):
        return "text/csv"
    if name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith(".zip"):
        return "application/zip"
    if name.endswith(".json"):
        return "application/json"
    return "application/octet-stream"

def _save_stats(stats: dict):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f)
    except OSError as exc:
        print(f"Statistiken konnten nicht gespeichert werden: {exc}")


def _load_stats():
    if not os.path.isfile(STATS_FILE):
        return DEFAULT_STATS.copy()
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "upload_order_count": int(data.get("upload_order_count", 0) or 0),
                "processed_order_count": int(data.get("processed_order_count", 0) or 0),
                "upload_delivery_notes_page_count": int(data.get("upload_delivery_notes_page_count", 0) or 0),
                "upload_delivery_notes_order_count": int(data.get("upload_delivery_notes_order_count", 0) or 0),
                "processed_delivery_notes_page_count": int(data.get("processed_delivery_notes_page_count", 0) or 0),
                "processed_delivery_notes_order_count": int(data.get("processed_delivery_notes_order_count", 0) or 0),
                "upload_shipping_labels_count": int(data.get("upload_shipping_labels_count", 0) or 0),
                "processed_shipping_labels_count": int(data.get("processed_shipping_labels_count", 0) or 0),
            }
    except Exception as exc:
        print(f"Statistiken konnten nicht geladen werden: {exc}")
        return DEFAULT_STATS.copy()

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    session_id = str(uuid.uuid4())

    if _gcs_enabled():
        # Bei GCS-Uploads läuft die Verarbeitung über die API-Endpunkte (signed URLs + /api/process).
        return render_template("index.html", error=None, session_id=session_id, gcs_enabled=True)

    if request.method == "POST":
        specific_name = request.form["specific_name"]
        uploaded_files = request.files.getlist("input_files")
        delivery_note_files = request.files.getlist("delivery_notes")
        shipping_label_files = request.files.getlist("shipping_labels")

        if not uploaded_files or len(uploaded_files) == 0:
            error = "Bitte mindestens eine Datei hochladen."
            return render_template("index.html", error=error, session_id=session_id, gcs_enabled=False)

        # Ergebnisordner leeren
        for file in os.listdir(RESULT_FOLDER):
            file_path = os.path.join(RESULT_FOLDER, file)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)
            except Exception as e:
                error = f"Fehler beim Löschen der alten Ergebnisse: {str(e)}"
                return render_template("index.html", error=error, session_id=session_id, gcs_enabled=False)

        # Temporäres Verzeichnis für die Dateien erstellen
        temp_dir = tempfile.mkdtemp()
        csv_dir = os.path.join(temp_dir, "csv")
        pdf_dir = os.path.join(temp_dir, "delivery_notes")
        os.makedirs(csv_dir, exist_ok=True)
        os.makedirs(pdf_dir, exist_ok=True)
        shipping_dir = os.path.join(temp_dir, "shipping_labels")
        os.makedirs(shipping_dir, exist_ok=True)

        try:
            # Dateien speichern
            for file in uploaded_files:
                file.save(os.path.join(csv_dir, file.filename))

            delivery_note_paths = []
            for file in delivery_note_files:
                if not file.filename:
                    continue
                pdf_path = os.path.join(pdf_dir, file.filename)
                file.save(pdf_path)
                delivery_note_paths.append(pdf_path)

            shipping_label_paths = []
            for file in shipping_label_files:
                if not file.filename:
                    continue
                pdf_path = os.path.join(shipping_dir, file.filename)
                file.save(pdf_path)
                shipping_label_paths.append(pdf_path)

            # Hauptverarbeitungsfunktion aufrufen
            run_stats = main(specific_name, csv_dir, RESULT_FOLDER, delivery_note_paths, shipping_label_paths)
            if isinstance(run_stats, dict):
                stats_to_store = DEFAULT_STATS.copy()
                for key in stats_to_store.keys():
                    stats_to_store[key] = int(run_stats.get(key, 0) or 0)
            else:
                stats_to_store = DEFAULT_STATS.copy()

            _save_stats(stats_to_store)
            return redirect(url_for("results"))

        except Exception as e:
            error = f"Ein Fehler ist aufgetreten: {str(e)}"

    return render_template("index.html", error=error, session_id=session_id, gcs_enabled=False)


@app.route("/api/sign-url", methods=["POST"])
def sign_url():
    if not _gcs_enabled():
        return jsonify({"error": "GCS ist nicht aktiviert. Bitte GCS_UPLOAD_BUCKET setzen."}), 400

    payload = request.get_json(force=True, silent=True) or {}
    filename = secure_filename(payload.get("filename", ""))
    content_type = payload.get("content_type") or "application/octet-stream"
    session_id = payload.get("session_id")
    file_type = payload.get("file_type", "csv")

    if not filename or not session_id:
        return jsonify({"error": "filename und session_id sind erforderlich"}), 400
    if file_type not in {"csv", "delivery", "shipping"}:
        return jsonify({"error": "file_type muss csv, delivery oder shipping sein"}), 400

    object_path = f"uploads/{session_id}/{file_type}/{filename}"
    try:
        upload_url = _generate_signed_upload_url(GCS_UPLOAD_BUCKET, object_path, content_type)
    except Exception as exc:
        return jsonify({"error": f"Signed URL konnte nicht erzeugt werden: {exc}"}), 500

    return jsonify({"uploadUrl": upload_url, "objectPath": object_path})


@app.route("/api/process", methods=["POST"])
def process_gcs():
    if not _gcs_enabled():
        return jsonify({"error": "GCS ist nicht aktiviert. Bitte GCS_UPLOAD_BUCKET setzen."}), 400

    data = request.get_json(force=True, silent=True) or {}
    specific_name = data.get("specific_name")
    session_id = data.get("session_id")
    csv_objects = data.get("csv_files") or []
    delivery_objects = data.get("delivery_notes") or []
    shipping_objects = data.get("shipping_labels") or []

    if not specific_name:
        return jsonify({"error": "specific_name fehlt"}), 400
    if not session_id:
        return jsonify({"error": "session_id fehlt"}), 400
    if not csv_objects:
        return jsonify({"error": "Mindestens eine CSV-Datei wird benötigt"}), 400

    # Ergebnisordner leeren
    for file in os.listdir(RESULT_FOLDER):
        file_path = os.path.join(RESULT_FOLDER, file)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            return jsonify({"error": f"Fehler beim Löschen alter Ergebnisse: {str(e)}"}), 500

    temp_dir = tempfile.mkdtemp()
    csv_dir = os.path.join(temp_dir, "csv")
    delivery_dir = os.path.join(temp_dir, "delivery_notes")
    shipping_dir = os.path.join(temp_dir, "shipping_labels")
    zip_path = None

    try:
        try:
            csv_files = _download_objects(csv_objects, GCS_UPLOAD_BUCKET, csv_dir)
            delivery_note_paths = _download_objects(delivery_objects, GCS_UPLOAD_BUCKET, delivery_dir) if delivery_objects else []
            shipping_label_paths = _download_objects(shipping_objects, GCS_UPLOAD_BUCKET, shipping_dir) if shipping_objects else []
        except Exception as exc:
            return jsonify({"error": f"Upload-Dateien konnten nicht aus GCS geladen werden: {exc}"}), 500

        try:
            run_stats = main(specific_name, csv_dir, RESULT_FOLDER, delivery_note_paths, shipping_label_paths)
            if isinstance(run_stats, dict):
                stats_to_store = DEFAULT_STATS.copy()
                for key in stats_to_store.keys():
                    stats_to_store[key] = int(run_stats.get(key, 0) or 0)
            else:
                stats_to_store = DEFAULT_STATS.copy()
            _save_stats(stats_to_store)
        except Exception as exc:
            return jsonify({"error": f"Verarbeitung fehlgeschlagen: {exc}"}), 500

        # Ergebnisse in GCS hochladen
        results_prefix = f"results/{session_id}/"
        uploaded_files = []
        try:
            for root, _, files in os.walk(RESULT_FOLDER):
                for file in files:
                    local_path = os.path.join(root, file)
                    object_path = f"{results_prefix}{file}"
                    _upload_file_to_gcs(local_path, GCS_RESULTS_BUCKET, object_path, content_type=_guess_content_type(file))
                    uploaded_files.append(file)

            zip_path = os.path.join(tempfile.gettempdir(), f"{session_id}_results.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for root, _, files in os.walk(RESULT_FOLDER):
                    for file in files:
                        local_path = os.path.join(root, file)
                        zipf.write(local_path, arcname=file)
            zip_object = f"{results_prefix}results.zip"
            _upload_file_to_gcs(zip_path, GCS_RESULTS_BUCKET, zip_object, content_type="application/zip")
            uploaded_files.append("results.zip")
        except Exception as exc:
            return jsonify({"error": f"Ergebnisse konnten nicht in GCS geschrieben werden: {exc}"}), 500

        signed_urls, ordered_names = _list_result_files(session_id)
        return jsonify({
            "session_id": session_id,
            "result_files": ordered_names,
            "signed_urls": signed_urls,
        })
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)


@app.route("/results", methods=["GET"])
def results():
    if _gcs_enabled():
        session_id = request.args.get("session_id")
        if not session_id:
            return "session_id erforderlich, z.B. /results?session_id=<id>", 400
        signed_urls, result_files = _list_result_files(session_id)
        stats = _load_stats_from_gcs(session_id)
        return render_template(
            "results.html",
            result_files=result_files,
            stats=stats,
            session_id=session_id,
            gcs_enabled=True,
            signed_urls=signed_urls,
        )

    result_files = os.listdir(RESULT_FOLDER)
    stats = _load_stats()
    return render_template("results.html", result_files=result_files, stats=stats, gcs_enabled=False, signed_urls={})


@app.route("/download_all", methods=["GET"])
def download_all():
    if _gcs_enabled():
        session_id = request.args.get("session_id")
        if not session_id:
            return "session_id erforderlich, z.B. /download_all?session_id=<id>", 400
        object_path = f"results/{session_id}/results.zip"
        try:
            signed_url = _generate_signed_download_url(GCS_RESULTS_BUCKET, object_path)
        except Exception as exc:
            return f"Download-Link konnte nicht erzeugt werden: {exc}", 500
        return redirect(signed_url)

    zip_path = os.path.join(tempfile.gettempdir(), "results.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for root, _, files in os.walk(RESULT_FOLDER):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)
    return send_file(zip_path, as_attachment=True, download_name="results.zip")


@app.route("/download/<filename>")
def download_file(filename):
    if _gcs_enabled():
        session_id = request.args.get("session_id")
        if not session_id:
            return "session_id erforderlich, z.B. /download/<datei>?session_id=<id>", 400
        object_path = f"results/{session_id}/{filename}"
        try:
            signed_url = _generate_signed_download_url(GCS_RESULTS_BUCKET, object_path)
        except Exception as exc:
            return f"Download-Link konnte nicht erzeugt werden: {exc}", 500
        return redirect(signed_url)

    return send_file(os.path.join(RESULT_FOLDER, filename), as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
