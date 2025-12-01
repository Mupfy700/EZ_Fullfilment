from flask import Flask, render_template, request, redirect, url_for, send_file
import json
import os
import tempfile
import zipfile
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
    if request.method == "POST":
        specific_name = request.form["specific_name"]
        uploaded_files = request.files.getlist("input_files")
        delivery_note_files = request.files.getlist("delivery_notes")
        shipping_label_files = request.files.getlist("shipping_labels")

        if not uploaded_files or len(uploaded_files) == 0:
            error = "Bitte mindestens eine Datei hochladen."
            return render_template("index.html", error=error)

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
                return render_template("index.html", error=error)

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

    return render_template("index.html", error=error)


@app.route("/results", methods=["GET"])
def results():
    result_files = os.listdir(RESULT_FOLDER)
    stats = _load_stats()
    return render_template("results.html", result_files=result_files, stats=stats)


@app.route("/download_all", methods=["GET"])
def download_all():
    zip_path = os.path.join(tempfile.gettempdir(), "results.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for root, _, files in os.walk(RESULT_FOLDER):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)
    return send_file(zip_path, as_attachment=True, download_name="results.zip")


@app.route("/download/<filename>")
def download_file(filename):
    return send_file(os.path.join(RESULT_FOLDER, filename), as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
