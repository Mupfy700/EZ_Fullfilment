import pandas as pd
import os

def read_csv(file_path):
    """ Einlesen der CSV-Datei """
    try:
        data = pd.read_csv(file_path)
        print(f"Datei {file_path} erfolgreich eingelesen!")
        return data
    except Exception as e:
        print(f"Es gab ein Problem beim Einlesen der Datei {file_path}: {e}")


def calculate_total_quantity_per_order(data):
    """ Berechnet die Gesamtanzahl der bestellten Untersetzer pro Bestellung """
    # Gruppieren nach der Spalte 'Name' und summieren der Spalte 'Lineitem quantity'
    total_quantity = data.groupby('Name')['Lineitem quantity'].sum().reset_index()
    total_quantity.columns = ['Name', 'Total Lineitem Quantity']
    
    # Zusammenführen der berechneten Gesamtanzahl mit dem ursprünglichen DataFrame
    data = pd.merge(data, total_quantity, on='Name', how='left')
    print("Gesamtanzahl der bestellten Untersetzer pro Bestellung berechnet und hinzugefügt.")
    return data

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

def add_weight_column(data, weight_map, country_code=None):
    """ 
    Hinzufügen einer Gewichtsspalte basierend auf der Gesamtanzahl der bestellten Untersetzer.
    Falls ein country_code angegeben ist, wird die Gewichtsspalte nur für Bestellungen aus diesem Land hinzugefügt.
    """
    
    def calculate_weight(row):
        """ 
        Berechnet das Gewicht basierend auf der Gesamtanzahl der bestellten Untersetzer.
        Falls die Gesamtanzahl nicht im weight_map enthalten ist, wird die Anzahl der Untersetzer als natürliche Zahl zurückgegeben.
        """
        total_quantity = int(row['Total Lineitem Quantity'])  # Gesamtanzahl der bestellten Untersetzer in der aktuellen Zeile als int
        return weight_map.get(total_quantity, total_quantity)  # Gewicht aus der weight_map holen oder die Anzahl der Untersetzer als natürliche Zahl zurückgeben, falls nicht vorhanden
    
    # Konvertiert die 'Total Lineitem Quantity' Spalte zu int
    data['Total Lineitem Quantity'] = data['Total Lineitem Quantity'].astype(int)
    
    # Wendet die calculate_weight Funktion auf jede Zeile des DataFrames an und erstellt die 'Weight'-Spalte
    if country_code:
        data['Weight'] = data.apply(lambda row: calculate_weight(row) if row['Shipping Country'] == country_code else '', axis=1)
        print(f"Gewichtsspalte nur für Bestellungen aus {country_code} hinzugefügt.")
    else:
        data['Weight'] = data.apply(calculate_weight, axis=1)
        print("Gewichtsspalte hinzugefügt basierend auf der Gesamtanzahl der bestellten Untersetzer.")
    
    return data


def remove_column(data, column_name):
    """ Entfernt die angegebene Spalte """
    if column_name in data.columns:
        data = data.drop(columns=[column_name])
        print(f"Spalte '{column_name}' entfernt.")
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

def save_to_csv(data, filename, output_folder):
    """ Speichern der Daten in einer CSV-Datei """
    output_path = os.path.join(output_folder, filename)
    data.to_csv(output_path, index=False)
    print(f"Daten gespeichert in {output_path}")


def process_files(input_folder, output_folder, weight_map):
    """ Verarbeitet alle Dateien im Eingangsordner und speichert die resultierenden Dateien im Ausgangsordner """
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_folder, filename)
            # Lesen der Datei
            order_data = read_csv(file_path)

            # Berechnen der Gesamtanzahl der bestellten Untersetzer pro Bestellung
            order_data = calculate_total_quantity_per_order(order_data)

            # Unnötige Spalten entfernen für DHL
            columns_to_remove_dhl = [
                "Financial Status", "Paid at", "Fulfillment Status", "Fulfilled at", "Accepts Marketing", "Currency",
                "Subtotal", "Shipping", "Taxes", "Total", "Discount Code", "Discount Amount", "Created at", 
                "Lineitem price", "Lineitem compare at price", "Lineitem requires shipping", "Lineitem taxable", 
                "Lineitem fulfillment status", "Billing Name", "Billing Street", "Billing Address1", "Billing Address2", 
                "Billing Company", "Billing City", "Billing Zip", "Billing Province", "Billing Country", "Billing Phone", 
                "Shipping Address1", "Shipping Address2", "Shipping Province", "Shipping Phone", "Cancelled at", 
                "Payment Method", "Payment Reference", "Refunded Amount", "Id", "Tags", "Risk Level", "Source", 
                "Lineitem discount", "Tax 1 Name", "Tax 1 Value", "Tax 2 Name", "Tax 2 Value", "Tax 3 Name", 
                "Tax 3 Value", "Tax 4 Name", "Tax 4 Value", "Tax 5 Name", "Tax 5 Value", "Phone", "Receipt Number", 
                "Duties", "Billing Province Name", "Shipping Province Name", "Payment Terms Name", "Next Payment Due At", 
                "Payment ID", "Payment References", "Shipping Method", "Lineitem quantity", "Lineitem name", "Lineitem sku", "Notes", "Note Attributes", "Vendor"
                ]

                #Unnötige Spalten entfernen für Hersteller
            columns_to_remove_manufacturer = [
                "Email", "Financial Status", "Paid at", "Fulfillment Status", "Fulfilled at", "Accepts Marketing", "Currency", 
                "Subtotal", "Shipping", "Taxes", "Total", "Discount Code", "Discount Amount", "Created at", "Lineitem price", 
                "Lineitem compare at price", "Lineitem requires shipping", "Lineitem taxable", "Lineitem fulfillment status", 
                "Billing Name", "Billing Street", "Billing Address1", "Billing Address2", "Billing Company", "Billing City", 
                "Billing Zip", "Billing Province", "Billing Country", "Billing Phone", "Shipping Address1", "Shipping Address2", 
                "Shipping Province", "Shipping Phone", "Cancelled at", "Payment Method", "Payment Reference", "Refunded Amount", 
                "Id", "Tags", "Risk Level", "Source", "Lineitem discount", "Tax 1 Name", "Tax 1 Value", "Tax 2 Name", "Tax 2 Value", 
                "Tax 3 Name", "Tax 3 Value", "Tax 4 Name", "Tax 4 Value", "Tax 5 Name", "Tax 5 Value", "Phone", "Receipt Number", 
                "Duties", "Billing Province Name", "Shipping Province Name", "Payment Terms Name", "Next Payment Due At", "Payment ID", "Payment References"
                ]
            
            cleaned_data_dhl = remove_unnecessary_columns(order_data, columns_to_remove_dhl)
            cleaned_data_manufacturer = remove_unnecessary_columns(order_data, columns_to_remove_manufacturer)

            # Duplikate entfernen
            cleaned_data_dhl = remove_duplicates(cleaned_data_dhl)

            # Filtern und separate Dateien erstellen
            dhl_de_data = filter_by_country(cleaned_data_dhl, 'DE')
            dhl_at_data = filter_by_country(cleaned_data_dhl, 'AT')

            # Gewichtsspalte hinzufügen
            dhl_at_data = add_weight_column(dhl_at_data, weight_map)

            # Entfernen der Spalte 'Total Lineitem Quantity'
            dhl_de_data = remove_column(dhl_de_data, 'Total Lineitem Quantity')
            dhl_at_data = remove_column(dhl_at_data, 'Total Lineitem Quantity')

            # Shipping Street aufteilen und Spalten hinzufügen
            dhl_de_data = split_shipping_street_de(dhl_de_data)
            dhl_at_data = split_shipping_street_at(dhl_at_data)

            # Dateien speichern
            base_filename = os.path.splitext(filename)[0]
            save_to_csv(dhl_de_data, f"DHL_{base_filename}_DE.csv", output_folder)
            save_to_csv(dhl_at_data, f"Premium_DHL_{base_filename}_AT.csv", output_folder)

            # Hersteller CSV-Datei erstellen
            regular_data = add_weight_column(cleaned_data_manufacturer, weight_map, country_code='AT')
            regular_data = remove_column(regular_data, 'Total Lineitem Quantity')
            save_to_csv(regular_data, f"{base_filename}_EZ_Originalz.csv", output_folder)


# Ordner Daniels Mac
# input_folder = '/Users/danielgackle/Movies/EZ Originalz/Fullfilment Automatisierung/Automatic_Fullfilment/EZ_Fullfilment/input_data'  # Ersetzen Sie dies durch den Pfad zum Eingangsordner
# output_folder = '/Users/danielgackle/Movies/EZ Originalz/Fullfilment Automatisierung/Automatic_Fullfilment/EZ_Fullfilment/output_data'  # Ersetzen Sie dies durch den Pfad zum Ausgangsordner

# Ordner Windows Jan
input_folder = r'C:\Users\janbi\Desktop\CSV_input'
output_folder = r'C:\Users\janbi\Desktop\CSV_output'

weight_map = {1: 0.1, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.3, 6: 0.3, 7: 0.3, 8: 0.3, 9: 0.4, 10: 0.4, 11: 0.4, 12: 0.4, 13: 0.4, 14: 0.4, 15: 0.4, 16: 0.5, 17: 0.7, 18: 0.7, 19: 0.7, 20: 0.7}

process_files(input_folder, output_folder, weight_map)