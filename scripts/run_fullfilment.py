import os
from ez_fullfilment.file_manager import FileManager

def main(specific_name, input_folder, output_folder):
    if not specific_name or not input_folder or not output_folder:
        print("Eingaben nicht vollständig. Abbruch.")
        return

    # Gewichtskarte (du kannst diese nach Bedarf erweitern)
    led_coaster_weight_map = {
        1: 0.1, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.2, 6: 0.3, 7: 0.3, 8: 0.3, 9: 0.3,
        10: 0.4, 11: 0.4, 12: 0.5, 13: 0.5, 14: 0.5, 15: 0.5, 16: 0.6, 17: 0.7,
        18: 0.7, 19: 0.7, 20: 0.7, 21: 0.8, 22: 0.8, 23: 0.8, 24: 0.8, 25: 0.9,
        26: 0.9, 27: 0.9, 28: 0.9
    }

    # Verarbeite die Dateien mit dem FileManager
    file_manager = FileManager(input_folder, output_folder, led_coaster_weight_map)
    file_manager.process_files(specific_name)
    print("Verarbeitung abgeschlossen.")

if __name__ == "__main__":
    # Beispielwerte für lokale Tests, diese werden durch die Flask-App überschrieben
    specific_name = "example_file"
    input_folder = "uploads"
    output_folder = "results"
    
    main(specific_name, input_folder, output_folder)