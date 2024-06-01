import tkinter as tk
from tkinter import simpledialog, filedialog

class GUI:
    def __init__(self):
        self.specific_name = ""
        self.input_folder = ""
        self.output_folder = ""

    def select_input_folder(self):
        folder = filedialog.askdirectory(title="Wählen Sie den Eingabeordner")
        if folder:
            self.input_folder_var.set(folder)
            self.input_folder = folder
            self.check_ready()

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Wählen Sie den Ausgabeordner")
        if folder:
            self.output_folder_var.set(folder)
            self.output_folder = folder
            self.check_ready()

    def check_ready(self):
        if self.specific_name_var.get() and self.input_folder and self.output_folder:
            self.submit_button.config(state=tk.NORMAL)
        else:
            self.submit_button.config(state=tk.DISABLED)

    def submit(self):
        self.specific_name = self.specific_name_var.get()
        self.root.destroy()

    def get_user_inputs(self):
        self.root = tk.Tk()
        self.root.title("Eingaben für die Dateiverarbeitung")
        
        tk.Label(self.root, text="Bitte geben Sie den Dateinamen ein:").pack(pady=5)
        self.specific_name_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.specific_name_var).pack(pady=5)
        
        tk.Label(self.root, text="Wählen Sie den Eingabeordner:").pack(pady=5)
        self.input_folder_var = tk.StringVar()
        tk.Button(self.root, text="Ordner wählen", command=self.select_input_folder).pack(pady=5)
        tk.Label(self.root, textvariable=self.input_folder_var).pack(pady=5)
        
        tk.Label(self.root, text="Wählen Sie den Ausgabeordner:").pack(pady=5)
        self.output_folder_var = tk.StringVar()
        tk.Button(self.root, text="Ordner wählen", command=self.select_output_folder).pack(pady=5)
        tk.Label(self.root, textvariable=self.output_folder_var).pack(pady=5)

        self.submit_button = tk.Button(self.root, text="Eingaben abschließen", command=self.submit, state=tk.DISABLED)
        self.submit_button.pack(pady=20)

        self.root.mainloop()

        return self.specific_name, self.input_folder, self.output_folder
