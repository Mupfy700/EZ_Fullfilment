from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import tempfile
import zipfile
from scripts.run_fullfilment import main

app = Flask(__name__)
RESULT_FOLDER = "results"
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        specific_name = request.form["specific_name"]
        uploaded_files = request.files.getlist("input_files")

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

        try:
            # Dateien speichern
            for file in uploaded_files:
                file.save(os.path.join(temp_dir, file.filename))

            # Hauptverarbeitungsfunktion aufrufen
            main(specific_name, temp_dir, RESULT_FOLDER)
            return redirect(url_for("results"))

        except Exception as e:
            error = f"Ein Fehler ist aufgetreten: {str(e)}"

    return render_template("index.html", error=error)


@app.route("/results", methods=["GET"])
def results():
    result_files = os.listdir(RESULT_FOLDER)
    return render_template("results.html", result_files=result_files)


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

