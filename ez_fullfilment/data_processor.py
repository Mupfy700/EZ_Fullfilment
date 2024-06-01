import pandas as pd

class DataProcessor:
    def __init__(self, weight_map):
        self.weight_map = weight_map

    def read_csv(self, file_path):
        """ Einlesen der CSV-Datei und Erzwingen der richtigen Datentypen """
        try:
            data = pd.read_csv(file_path, dtype={'Shipping Zip': str})
            print(f"Datei {file_path} erfolgreich eingelesen!")
            return data
        except Exception as e:
            print(f"Es gab ein Problem beim Einlesen der Datei {file_path}: {e}")

    def calculate_total_quantity_per_order(self, data):
        """ Berechnet die Gesamtanzahl der bestellten Untersetzer pro Bestellung """
        # Gruppieren nach der Spalte 'Name' und summieren der Spalte 'Lineitem quantity'
        total_quantity = data.groupby('Name')['Lineitem quantity'].sum().reset_index()
        total_quantity.columns = ['Name', 'Total Lineitem Quantity']
    
        # Zusammenführen der berechneten Gesamtanzahl mit dem ursprünglichen DataFrame
        data = pd.merge(data, total_quantity, on='Name', how='left')
        print("Gesamtanzahl der bestellten Untersetzer pro Bestellung berechnet und hinzugefügt.")
        return data
    
    def remove_unnecessary_columns(self, data, columns_to_remove):
        """ Entfernen nicht benötigter Spalten """
        data = data.drop(columns=columns_to_remove, errors='ignore')
        print("Unnötige Spalten entfernt.")
        return data
    
    def remove_duplicates(self, data):
        """ Entfernen von Duplikaten basierend auf der Spalte 'Name' """
        data = data.drop_duplicates(subset='Name')
        print("Duplikate entfernt.")
        return data
    
    def filter_by_country(self, data, country_code):
        """ Filtern der Daten nach Land """
        filtered_data = data[data['Shipping Country'] == country_code]
        print(f"Daten für {country_code} gefiltert.")
        return filtered_data

    def filter_not_by_country(self, data, country_code):
        """ Filtern der Daten nach Land, exklusive country_code """
        filtered_data = data[data['Shipping Country'] != country_code]
        print(f"Daten, die nicht für {country_code} sind, gefiltert.")
        return filtered_data
    
    def add_weight_column(self, data):
        def calculate_weight(row):
            """ Berechnet das Gewicht basierend auf der Gesamtanzahl der bestellten Untersetzer."""
            total_quantity = int(row['Total Lineitem Quantity'])  # Gesamtanzahl der bestellten Untersetzer in der aktuellen Zeile als int
            weight = self.weight_map.get(total_quantity, f"{total_quantity} Untersetzer")  # Gewicht aus der weight_map holen oder die Anzahl der Untersetzer als natürliche Zahl zurückgeben, falls nicht vorhanden
            return str(weight).replace('.', ',')  # Punkt durch Komma ersetzen und in einen String umwandeln
    
    
        # Konvertiert die 'Total Lineitem Quantity' Spalte zu int
        data['Total Lineitem Quantity'] = data['Total Lineitem Quantity'].astype(int)
    
        # Wendet die calculate_weight Funktion auf jede Zeile des DataFrames an und erstellt die 'Weight'-Spalte
        data['Weight'] = data.apply(lambda row: calculate_weight(row) if pd.notnull(row['Shipping Country']) and row['Shipping Country'] != 'DE' else '', axis=1)
        print("Gewichtsspalte für alle Bestellungen außer DE hinzugefügt.")
    
        return data
    
    def remove_column(self, data, column_name):
        """ Entfernt die angegebene Spalte """
        if column_name in data.columns:
            data = data.drop(columns=[column_name])
            print(f"Spalte '{column_name}' entfernt.")
        return data

    def split_shipping_street(self, data, is_germany):
        """  Spalte 'Shipping Street' aufteilen und 'Shipping Supplement'+'Stiege'+'Top' hinzufügen."""
        street_index = data.columns.get_loc('Shipping Street')
        data.insert(street_index + 1, 'Shipping Supplement', '')

        if not is_germany:
            data.insert(street_index + 2, 'Stiege', '')
            data.insert(street_index + 3, 'Top', '')

        for index, row in data.iterrows():
            street = row['Shipping Street']
            parts = street.split(',', 1)  # Split at the first comma only
            data.at[index, 'Shipping Street'] = parts[0].strip()
            if len(parts) > 1:
                data.at[index, 'Shipping Supplement'] = parts[1].strip()

        print(f"Spalte 'Shipping Street' aufgeteilt.")
        return data