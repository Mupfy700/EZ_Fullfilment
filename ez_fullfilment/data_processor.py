import pandas as pd
import math

class DataProcessor:
    def __init__(self, led_coaster_weight_map):
        self.led_coaster_weight_map = led_coaster_weight_map


    def read_csv(self, file_path):
        """ Einlesen der CSV-Datei und Erzwingen der richtigen Datentypen """
        try:
            data = pd.read_csv(file_path, dtype={'Shipping Zip': str})
            print(f"Datei {file_path} erfolgreich eingelesen!")
            return data
        except Exception as e:
            print(f"Es gab ein Problem beim Einlesen der Datei {file_path}: {e}")

    # def calculate_total_quantity_per_order(self, data):
    #     """ Berechnet die Gesamtanzahl der bestellten Untersetzer pro Bestellung """
    #     # Gruppieren nach der Spalte 'Name' und summieren der Spalte 'Lineitem quantity'
    #     total_quantity = data.groupby('Name')['Lineitem quantity'].sum().reset_index()
    #     total_quantity.columns = ['Name', 'Total Lineitem Quantity']
    
    #     # Zusammenführen der berechneten Gesamtanzahl mit dem ursprünglichen DataFrame
    #     data = pd.merge(data, total_quantity, on='Name', how='left')
    #     print("Gesamtanzahl der bestellten Untersetzer pro Bestellung berechnet und hinzugefügt.")
    #     return data
    
    def calculate_total_quantities_by_item_type_per_order(self, data):
        """
        Berechnet die Gesamtanzahl der bestellten LED-Untersetzer und Glas-Trinkhalme pro Bestellung
        und fügt zwei neue Spalten 'Total LED Untersetzer' und 'Total Glas Trinkhalme' hinzu.
        """

        # Eventuelle überflüssige Leerzeichen entfernen, damit Vergleiche sauber funktionieren
        data['Lineitem name'] = data['Lineitem name'].str.strip()

        # Summation für LED-Untersetzer
        # (Hier wird angenommen, dass "LED-Untersetzer" im 'Lineitem name' enthalten ist.)
        led_mask = data['Lineitem name'].str.contains("LED-Untersetzer", case=False, na=False)
        led_sums = (
            data[led_mask]
            .groupby('Name')['Lineitem quantity']
            .sum()
            .reset_index(name='Total LED Untersetzer')
        )

        # Summation für Glas-Trinkhalme
        # (Hier wird angenommen, dass "Glas-Trinkhalme" im 'Lineitem name' enthalten ist.)
        glas_mask = data['Lineitem name'].str.contains("Glas-Trinkhalme", case=False, na=False)
        glas_sums = (
            data[glas_mask]
            .groupby('Name')['Lineitem quantity']
            .sum()
            .reset_index(name='Total Glas Trinkhalme')
        )

        # Zusammenführen der berechneten Werte mit dem ursprünglichen DataFrame
        data = pd.merge(data, led_sums, on='Name', how='left')
        data = pd.merge(data, glas_sums, on='Name', how='left')

        # Fehlende Werte (z. B. wenn keine Untersetzer oder Trinkhalme enthalten sind) auf 0 setzen
        data['Total LED Untersetzer'] = data['Total LED Untersetzer'].fillna(0).astype(int)
        data['Total Glas Trinkhalme']  = data['Total Glas Trinkhalme'].fillna(0).astype(int)

        print("Gesamtanzahl der bestellten LED-Untersetzer und Glas-Trinkhalme pro Bestellung berechnet und hinzugefügt.")
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
    
    # def add_weight_column(self, data):
#         def calculate_weight(row):
#             """ Berechnet das Gewicht basierend auf der Gesamtanzahl der bestellten Untersetzer."""
#             total_quantity = int(row['Total Lineitem Quantity'])  # Gesamtanzahl der bestellten Untersetzer in der aktuellen Zeile als int
#             weight = self.led_coaster_weight_map.get(total_quantity, f"{total_quantity} Untersetzer")  # Gewicht aus der led_coaster_weight_map holen oder die Anzahl der Untersetzer als natürliche Zahl zurückgeben, falls nicht vorhanden
#             return str(weight).replace('.', ',')  # Punkt durch Komma ersetzen und in einen String umwandeln
#     
#     
#         # Konvertiert die 'Total Lineitem Quantity' Spalte zu int
#         data['Total Lineitem Quantity'] = data['Total Lineitem Quantity'].astype(int)
#     
#         # Wendet die calculate_weight Funktion auf jede Zeile des DataFrames an und erstellt die 'Weight'-Spalte
#         data['Weight'] = data.apply(lambda row: calculate_weight(row) if pd.notnull(row['Shipping Country']) and row['Shipping Country'] != 'DE' else '', axis=1)
#         print("Gewichtsspalte für alle Bestellungen außer DE hinzugefügt.")
#     
#         return data
    
    def add_weight_column(self, data):
        """
        Berechnet das Gesamtgewicht einer Bestellung basierend auf den bestellten LED-Untersetzern und Glas-Trinkhalmen.
    
        Das Gewicht der LED-Untersetzer wird dabei wie bisher über die led_coaster_weight_map ermittelt,
        basierend auf der Spalte 'Total LED Untersetzer'.
    
        Für die Glas-Trinkhalme gilt:
          - Zwei Trinkhalme werden als Doppelverpackung mit 0,13 kg versendet.
          - Ein einzelner Trinkhalm (falls die Bestellmenge ungerade ist) wird in einer Einzelverpackung mit 0,08 kg versendet.
          - Es wird so viele Doppelverpackungen wie möglich gebildet, der eventuelle Rest wird als Einzelverpackung versendet.
    
        Für Bestellungen, bei denen 'Shipping Country' nicht 'DE' ist, wird das Gesamtgewicht berechnet und als
        'Weight'-Spalte abgelegt. Bei Bestellungen innerhalb Deutschlands bleibt die Spalte leer.
        """
    
        def calculate_weight(row):
            # LED-Gewicht ermitteln: Basierend auf der Gesamtanzahl der LED-Untersetzer
            total_led = int(row['Total LED Untersetzer'])
            led_weight = self.led_coaster_weight_map.get(total_led)
            # Falls kein Eintrag in der Map vorhanden ist, kann alternativ ein Standardwert (z.B. 0) genutzt werden
            if led_weight is None:
                led_weight = 0
        
            # Glas-Trinkhalme: Anzahl der bestellten Glas-Trinkhalme
            total_glass = int(row['Total Glas Trinkhalme'])
            # Anzahl Doppelverpackungen: so viele wie möglich
            num_double = total_glass // 2
            # Restliche Trinkhalme werden als Einzelverpackung versendet
            num_single = total_glass % 2
            glass_weight = num_double * 0.13 + num_single * 0.08
        
            total_weight = led_weight + glass_weight

            # Aufrunden auf 0,1 kg-Schritte
            total_weight = math.ceil(total_weight * 10) / 10
        
            # Umwandeln in String und Punkt durch Komma ersetzen (für die CSV-Ausgabe)
            return str(total_weight).replace('.', ',')
    
        # Sicherstellen, dass die relevanten Spalten als int vorliegen
        data['Total LED Untersetzer'] = data['Total LED Untersetzer'].astype(int)
        data['Total Glas Trinkhalme'] = data['Total Glas Trinkhalme'].astype(int)
    
        # Gewichtsspalte nur für Bestellungen außerhalb von Deutschland berechnen
        data['Weight'] = data.apply(
            lambda row: calculate_weight(row)
            if pd.notnull(row['Shipping Country']) and row['Shipping Country'] != 'DE'
            else '',
            axis=1
        )
    
        print("Gewichtsspalte für alle Bestellungen außer DE basierend auf LED-Untersetzer und Glas-Trinkhalmen hinzugefügt.")
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