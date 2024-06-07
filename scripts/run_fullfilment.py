import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ez_fullfilment.gui import GUI
from ez_fullfilment.file_manager import FileManager

def main():
    gui = GUI()
    specific_name, input_folder, output_folder = gui.get_user_inputs()

    if not specific_name or not input_folder or not output_folder:
        print("Eingaben nicht vollständig. Abbruch.")
        return

    weight_map = {1: 0.1, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.2, 6: 0.3, 7: 0.3, 8: 0.3, 9: 0.3, 10: 0.4, 11: 0.4, 12: 0.5, 13: 0.5, 14: 0.5, 15: 0.5, 16: 0.6, 17: 0.7, 18: 0.7, 19: 0.7, 20: 0.7, 21: 0.8, 22: 0.8, 23: 0.8, 24: 0.8}

    file_manager = FileManager(input_folder, output_folder, weight_map)
    file_manager.process_files(specific_name)

if __name__ == "__main__":
    main()