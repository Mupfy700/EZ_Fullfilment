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
        specific_name = request.form["specific_name"].strip()
        csv_file = request.files.get("csv_file")
        packing_slip_files = request.files.getlist("packing_slips")
        shipping_label_files = request.files.getlist("shipping_labels")

        if not csv_file:
            error = "Bitte eine CSV-Datei hochladen."
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
            csv_path = os.path.join(temp_dir, csv_file.filename)
            csv_file.save(csv_path)

            packing_paths = []
            for file in packing_slip_files:
                if file.filename:
                    path = os.path.join(temp_dir, file.filename)
                    file.save(path)
                    packing_paths.append(path)

            label_paths = []
            for file in shipping_label_files:
                if file.filename:
                    path = os.path.join(temp_dir, file.filename)
                    file.save(path)
                    label_paths.append(path)

            # Hauptverarbeitungsfunktion aufrufen
            main(specific_name, temp_dir, RESULT_FOLDER, packing_paths, label_paths)
            return redirect(url_for("results"))

        except Exception as e:
            error = f"Ein Fehler ist aufgetreten: {str(e)}"

    return render_template("index.html", error=error)


@app.route("/results", methods=["GET"])
def results():
    result_files = os.listdir(RESULT_FOLDER)

    category_outputs = {
        "Marmor": {"slug": "marmor", "packing": None, "labels": None},
        "Schwarzer Marmor": {"slug": "schwarzer_marmor", "packing": None, "labels": None},
        "Rest": {"slug": "rest", "packing": None, "labels": None},
    }

    matched_files = set()
    for file in result_files:
        lower = file.lower()
        for name, meta in category_outputs.items():
            slug = meta["slug"]
            if "lieferscheine" in lower and slug in lower:
                category_outputs[name]["packing"] = file
                matched_files.add(file)
            if "versandlabel" in lower and slug in lower:
                category_outputs[name]["labels"] = file
                matched_files.add(file)

    other_files = [file for file in result_files if file not in matched_files]

    return render_template(
        "results.html",
        result_files=result_files,
        category_outputs=category_outputs,
        other_files=other_files,
    )


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

