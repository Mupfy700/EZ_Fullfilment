import os
import pandas as pd
from .data_processor import DataProcessor

class FileManager:
    def __init__(self, input_folder, output_folder, led_coaster_weight_map):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.processor = DataProcessor(led_coaster_weight_map)

    # Diese Funktion durchsucht den Eingabeordner nach allen CSV-Dateien,liest sie ein und kombiniert sie zu einem einzigen DataFrame.
    def merge_csv_files(self):
        all_files = [os.path.join(self.input_folder, f) for f in os.listdir(self.input_folder) if f.endswith('.csv')]
        combined_data = pd.concat([self.processor.read_csv(file) for file in all_files], ignore_index=True)
        print(f"Alle Dateien im Ordner {self.input_folder} zusammengeführt.")
        return combined_data
    
    # Diese Funktion speichert die übergebenen Daten (DataFrame) als CSV-Datei im angegebenen Ausgabeordner. Der Dateiname wird durch den Parameter `filename` bestimmt.
    def save_to_csv(self, data, filename):
        # Überprüfen, ob der DataFrame leer ist
        if data.empty:
            print(f"Die Datei {filename} wurde nicht gespeichert, da der DataFrame leer ist.")
            return

        output_path = os.path.join(self.output_folder, filename)

        # Umwandlung des Dezimaltrennzeichens für die CSV-Ausgabe
        if 'Weight' in data.columns:
            data['Weight'] = data['Weight'].apply(lambda x: str(x).replace('.', ','))

        data.to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')
        print(f"Daten gespeichert in {output_path}")

    def process_files(self, specific_name):
        try:
            combined_data = self.merge_csv_files()
            combined_data = self.processor.calculate_total_quantities_by_item_type_per_order(combined_data)
        except Exception as e:
            print(f"Fehler bei der Verarbeitung der Dateien: {e}")
            return

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
            "Payment ID", "Payment References", "Shipping Method", "Lineitem quantity", "Lineitem name", "Lineitem sku", "Notes", "Note Attributes", "Vendor", "Note Attributes"
        ]
        columns_to_remove_manufacturer = [
            "Email", "Financial Status", "Paid at", "Fulfillment Status", "Fulfilled at", "Accepts Marketing", "Currency", 
            "Subtotal", "Shipping", "Taxes", "Total", "Discount Code", "Discount Amount", "Created at", "Lineitem price", 
            "Lineitem compare at price", "Lineitem requires shipping", "Lineitem taxable", "Lineitem fulfillment status", 
            "Billing Name", "Billing Street", "Billing Address1", "Billing Address2", "Billing Company", "Billing City", 
            "Billing Zip", "Billing Province", "Billing Country", "Billing Phone", "Shipping Address1", "Shipping Address2", 
            "Shipping Province", "Shipping Phone", "Cancelled at", "Payment Method", "Payment Reference", "Refunded Amount", 
            "Id", "Tags", "Risk Level", "Source", "Lineitem discount", "Tax 1 Name", "Tax 1 Value", "Tax 2 Name", "Tax 2 Value", 
            "Tax 3 Name", "Tax 3 Value", "Tax 4 Name", "Tax 4 Value", "Tax 5 Name", "Tax 5 Value", "Phone", "Receipt Number", 
            "Duties", "Billing Province Name", "Shipping Province Name", "Payment Terms Name", "Next Payment Due At", "Payment ID", "Payment References", "Note Attributes"
        ]


        cleaned_data_dhl = self.processor.remove_columns(combined_data, columns_to_remove_dhl)
        cleaned_data_manufacturer = self.processor.remove_columns(combined_data, columns_to_remove_manufacturer)

        cleaned_data_dhl = self.processor.remove_duplicates(cleaned_data_dhl)
        cleaned_data_dhl = self.processor.add_weight_column(cleaned_data_dhl)
        cleaned_data_dhl = self.processor.remove_columns(cleaned_data_dhl, ['Total LED Untersetzer', 'Total Glas Trinkhalme', 'Total Holzaufsteller'])

        cleaned_data_dhl = self.processor.split_shipping_street(cleaned_data_dhl)

        dhl_warenpost_data = cleaned_data_dhl[cleaned_data_dhl['Weight'].astype(float) < 1]
        dhl_paket_data = cleaned_data_dhl[cleaned_data_dhl['Weight'].astype(float) >= 1]

        #DE
        dhl_de_warenpost_data = self.processor.filter_by_country(dhl_warenpost_data, 'DE')
        dhl_de_paket_data = self.processor.filter_by_country(dhl_paket_data, 'DE')
        self.save_to_csv(dhl_de_warenpost_data, f"DE_DHL_Warenpost_{specific_name}_EZ_Originalz.csv")
        self.save_to_csv(dhl_de_paket_data, f"DE_DHL_Paket_{specific_name}_EZ_Originalz.csv")


        #FR
        dhl_fr_warenpost_data = self.processor.filter_by_country(dhl_warenpost_data, 'FR')
        dhl_fr_paket_data = self.processor.filter_by_country(dhl_paket_data, 'FR')
        self.save_to_csv(dhl_fr_warenpost_data, f"FR_DHL_Premium_Warenpost_{specific_name}_EZ_Originalz.csv")
        self.save_to_csv(dhl_fr_paket_data, f"FR_DHL_Premium_Paket_{specific_name}_EZ_Originalz.csv")


        # Internationale Bestellungen (nicht DE und nicht FR)
        international_warenpost_data = self.processor.filter_not_by_country(dhl_warenpost_data, 'DE')
        international_warenpost_data = self.processor.filter_not_by_country(international_warenpost_data, 'FR')
        international_paket_data = self.processor.filter_not_by_country(dhl_paket_data, 'DE')
        international_paket_data = self.processor.filter_not_by_country(international_paket_data, 'FR')
        
        # Hinzufügen der Spalten "Stiege" und "Top", falls "AT" enthalten ist
        international_warenpost_data = self.processor.add_austria_specific_columns(international_warenpost_data)
        international_paket_data = self.processor.add_austria_specific_columns(international_paket_data)
        
        # Speichern der internationalen CSVs
        self.save_to_csv(international_warenpost_data, f"International_DHL_Warenpost_{specific_name}_EZ_Originalz.csv")
        self.save_to_csv(international_paket_data, f"International_DHL_Paket_{specific_name}_EZ_Originalz.csv")




        #Manufacturer Data
        regular_data = self.processor.add_weight_column(cleaned_data_manufacturer)
        regular_data = self.processor.remove_columns(regular_data, ['Total LED Untersetzer', 'Total Glas Trinkhalme', 'Total Holzaufsteller'])
        self.save_to_csv(regular_data, f"{specific_name}_EZ_Originalz.csv")