import pandas as pd
import re

def read_csv(file_path):
    """ Einlesen der CSV-Datei """
    try:
        data = pd.read_csv(file_path)
        print("Datei erfolgreich eingelesen!")
        return data
    except Exception as e:
        print(f"Es gab ein Problem beim Einlesen der Datei: {e}")

def remove_unnecessary_columns(data, columns_to_remove):
    """ Entfernen nicht benötigter Spalten """
    data = data.drop(columns=columns_to_remove, errors='ignore')
    print("Unnötige Spalten entfernt.")
    return data

def remove_duplicates(data):
    """ Entfernen von Duplikaten basierend auf der Spalte 'Name' """
    data = data.drop_duplicates(subset='Name')
    print("Duplikate entfernt.")
    return data

def filter_by_country(data, country_code):
    """ Filtern der Daten nach Land """
    filtered_data = data[data['Shipping Country'] == country_code]
    print(f"Daten für {country_code} gefiltert.")
    return filtered_data

def add_weight_column(data, weight_map):
    """ Hinzufügen einer Gewichtsspalte basierend auf der Anzahl der bestellten Untersetzer """
    
    def calculate_weight(row):
        """ 
        Berechnet das Gewicht basierend auf der Anzahl der bestellten Untersetzer.
        Falls die Anzahl der Untersetzer nicht im weight_map enthalten ist, wird die Anzahl der Untersetzer zurückgegeben.
        """
        quantity = row['Lineitem quantity']  # Anzahl der bestellten Untersetzer in der aktuellen Zeile
        return weight_map.get(quantity, quantity)  # Gewicht aus der weight_map holen oder die Anzahl der Untersetzer zurückgeben, falls nicht vorhanden
    
    # Wendet die calculate_weight Funktion auf jede Zeile des DataFrames an und erstellt die 'Weight'-Spalte
    data['Weight'] = data.apply(calculate_weight, axis=1)
    print("Gewichtsspalte hinzugefügt.")
    return data

def split_shipping_street_de(data):
    """ Spalte 'Shipping Street' aufteilen und 'Shipping Supplement' hinzufügen für DE """
    # Initialisieren der 'Shipping Supplement' Spalte
    data.insert(data.columns.get_loc('Shipping Street') + 1, 'Shipping Supplement', '')

    return data


def split_shipping_street_at(data):
    """ Spalte 'Shipping Street' aufteilen und 'Shipping Supplement', 'Stiege', 'Top' hinzufügen für AT """
    # Initialisieren der 'Shipping Supplement', 'Stiege' und 'Top' Spalten
    street_index = data.columns.get_loc('Shipping Street')
    data.insert(street_index + 1, 'Shipping Supplement', '')
    data.insert(street_index + 2, 'Stiege', '')
    data.insert(street_index + 3, 'Top', '')
    
    return data


def save_to_csv(data, filename):
    """ Speichern der Daten in einer CSV-Datei """
    data.to_csv(filename, index=False)
    print(f"Daten gespeichert in {filename}")

# Pfad zur CSV-Datei
file_path = '/Users/danielgackle/Movies/EZ Originalz/Fullfilment Automatisierung/Test/orders_export-2024-04-28T182242_145.csv'

# Lesen der Datei
order_data = read_csv(file_path)

# Unnötige Spalten entfernen
columns_to_remove = ["Financial Status", "Paid at", "Fulfillment Status", "Fulfilled at", "Accepts Marketing", "Currency",
                     "Subtotal", "Shipping", "Taxes", "Total", "Discount Code", "Discount Amount", "Created at", 
                     "Lineitem price", "Lineitem compare at price", "Lineitem requires shipping", "Lineitem taxable", 
                     "Lineitem fulfillment status", "Billing Name", "Billing Street", "Billing Address1", "Billing Address2", 
                     "Billing Company", "Billing City", "Billing Zip", "Billing Province", "Billing Country", "Billing Phone", 
                     "Shipping Address1", "Shipping Address2", "Shipping Province", "Shipping Phone", "Cancelled at", 
                     "Payment Method", "Payment Reference", "Refunded Amount", "Id", "Tags", "Risk Level", "Source", 
                     "Lineitem discount", "Tax 1 Name", "Tax 1 Value", "Tax 2 Name", "Tax 2 Value", "Tax 3 Name", 
                     "Tax 3 Value", "Tax 4 Name", "Tax 4 Value", "Tax 5 Name", "Tax 5 Value", "Phone", "Receipt Number", 
                     "Duties", "Billing Province Name", "Shipping Province Name", "Payment Terms Name", "Next Payment Due At", 
                     "Payment ID", "Payment References", "Shipping Method", "Lineitem sku", "Notes", "Note Attributes", "Vendor"]
cleaned_data = remove_unnecessary_columns(order_data, columns_to_remove)

# Duplikate entfernen
cleaned_data = remove_duplicates(cleaned_data)

# Filtern und separate Dateien erstellen
dhl_de_data = filter_by_country(cleaned_data, 'DE')
dhl_at_data = filter_by_country(cleaned_data, 'AT')

# Gewicht hinzufügen
weight_map = {1: 0.1, 2: 0.2, 3: 0.2, 4: 0.2, 6: 0.3, 8: 0.3, 9: 0.4, 10: 0.4, 11: 0.4, 12: 0.4, 13: 0.4, 14: 0.4, 15: 0.4, 16: 0.5, 17: 0.7, 18: 0.7, 19: 0.7, 20: 0.7}
dhl_at_data = add_weight_column(dhl_at_data, weight_map)

# Shipping Street aufteilen und Spalten hinzufügen
dhl_de_data = split_shipping_street_de(dhl_de_data)
dhl_at_data = split_shipping_street_at(dhl_at_data)

# Dateien speichern
save_to_csv(dhl_de_data, 'DHL_DE.csv')
save_to_csv(dhl_at_data, 'DHL_AT.csv')

# Reguläre CSV-Datei erstellen
regular_data = add_weight_column(cleaned_data, weight_map)
save_to_csv(regular_data, 'Regular.csv')
