import os
import pandas as pd
from .data_processor import DataProcessor

class FileManager:
    def __init__(self, input_folder, output_folder, led_coaster_weight_map):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.processor = DataProcessor(led_coaster_weight_map)

    def merge_csv_files(self):
        all_files = [os.path.join(self.input_folder, f) for f in os.listdir(self.input_folder) if f.endswith('.csv')]
        combined_data = pd.concat([self.processor.read_csv(file) for file in all_files], ignore_index=True)
        print(f"Alle Dateien im Ordner {self.input_folder} zusammengeführt.")
        return combined_data

    def save_to_csv(self, data, filename):
        output_path = os.path.join(self.output_folder, filename)
        data.to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')
        print(f"Daten gespeichert in {output_path}")

    def process_files(self, specific_name):
        combined_data = self.merge_csv_files()
        combined_data = self.processor.calculate_total_quantities_by_item_type_per_order(combined_data)

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

        cleaned_data_dhl = self.processor.remove_unnecessary_columns(combined_data, columns_to_remove_dhl)
        cleaned_data_manufacturer = self.processor.remove_unnecessary_columns(combined_data, columns_to_remove_manufacturer)

        cleaned_data_dhl = self.processor.remove_duplicates(cleaned_data_dhl)

        dhl_de_data = self.processor.filter_by_country(cleaned_data_dhl, 'DE')
        dhl_eu_data = self.processor.filter_not_by_country(cleaned_data_dhl, 'DE')

        dhl_eu_data = self.processor.add_weight_column(dhl_eu_data)

        #dhl_de_data = self.processor.remove_column(dhl_de_data, 'Total Lineitem Quantity')
        #dhl_eu_data = self.processor.remove_column(dhl_eu_data, 'Total Lineitem Quantity')

        dhl_de_data = self.processor.remove_column(dhl_de_data, 'Total LED Untersetzer')
        dhl_de_data = self.processor.remove_column(dhl_de_data, 'Total Glas Trinkhalme')
        dhl_eu_data = self.processor.remove_column(dhl_eu_data, 'Total LED Untersetzer')
        dhl_eu_data = self.processor.remove_column(dhl_eu_data, 'Total Glas Trinkhalme')


        dhl_de_data = self.processor.split_shipping_street(dhl_de_data, is_germany=True)
        dhl_eu_data = self.processor.split_shipping_street(dhl_eu_data, is_germany=False)

        self.save_to_csv(dhl_de_data, f"DHL_{specific_name}_EZ_Originalz.csv")
        self.save_to_csv(dhl_eu_data, f"Premium_DHL_{specific_name}_EZ_Originalz.csv")

        regular_data = self.processor.add_weight_column(cleaned_data_manufacturer)
        #regular_data = self.processor.remove_column(regular_data, 'Total Lineitem Quantity')
        regular_data = self.processor.remove_column(regular_data, 'Total LED Untersetzer')
        regular_data = self.processor.remove_column(regular_data, 'Total Glas Trinkhalme')
        self.save_to_csv(regular_data, f"{specific_name}_EZ_Originalz.csv")
