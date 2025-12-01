import os
import re
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
from .data_processor import DataProcessor

class FileManager:
    def __init__(self, input_folder, output_folder, led_coaster_weight_map):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.processor = DataProcessor(led_coaster_weight_map)
        self.marmor_sku_marker = "01010103"
        self.schwarzer_marmor_sku_marker = "01010105"
        self.accessory_skus = {"9999999998", "9999999999", "G00000001"}

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

    def process_files(self, specific_name, delivery_note_files=None, shipping_label_files=None):
        stats = {
            "upload_order_count": 0,
            "processed_order_count": 0,
            "upload_delivery_notes_page_count": 0,
            "upload_delivery_notes_order_count": 0,
            "processed_delivery_notes_page_count": 0,
            "processed_delivery_notes_order_count": 0,
            "upload_shipping_labels_count": 0,
            "processed_shipping_labels_count": 0,
        }
        try:
            combined_data = self.merge_csv_files()
            combined_data = self.processor.calculate_total_quantities_by_item_type_per_order(combined_data)
        except Exception as e:
            print(f"Fehler bei der Verarbeitung der Dateien: {e}")
            return stats

        # Upload-Bestellungen zählen (Rohdaten)
        if 'Name' in combined_data.columns:
            stats["upload_order_count"] = combined_data['Name'].dropna().map(self._normalize_order_number).dropna().nunique()

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

        # Internationale Bestellungen (nicht DE)
        international_warenpost_data = self.processor.filter_not_by_country(dhl_warenpost_data, 'DE')
        international_paket_data = self.processor.filter_not_by_country(dhl_paket_data, 'DE')
        
        # Hinzufügen der Spalten "Stiege" und "Top", falls "AT" enthalten ist
        international_warenpost_data = self.processor.add_austria_specific_columns(international_warenpost_data)
        international_paket_data = self.processor.add_austria_specific_columns(international_paket_data)
        
        # Speichern der internationalen CSVs
        self.save_to_csv(international_warenpost_data, f"International_DHL_Warenpost_{specific_name}_EZ_Originalz.csv")
        self.save_to_csv(international_paket_data, f"International_DHL_Paket_{specific_name}_EZ_Originalz.csv")

        #Manufacturer Data
        regular_data = cleaned_data_manufacturer.copy()
        regular_data = self.processor.remove_columns(regular_data, ['Total LED Untersetzer', 'Total Glas Trinkhalme', 'Total Holzaufsteller', 'Shipping Street', 'Shipping Company', 'Shipping City', 'Shipping Zip'])
        self.save_to_csv(regular_data, f"{specific_name}_EZ_Originalz.csv")

        order_sequence = self._collect_order_sequence(regular_data)
        order_categories = self._categorize_orders(combined_data)

        #Manufacturer Total Costs
        cost_data = self.processor.add_manufacturer_costs(cleaned_data_manufacturer)
        cost_data = self.processor.remove_columns(cost_data, ['Shipping Street', 'Shipping Company', 'Shipping City', 'Shipping Zip'])
        self.save_to_csv(cost_data, f"{specific_name}_Herstellkosten.csv")
        
        #Designübersicht
        design_overview = self.processor.generate_design_overview(regular_data)
        self.save_to_csv(design_overview, f"{specific_name}_Designübersicht.csv")

        stats["processed_order_count"] = len(order_sequence)

        if delivery_note_files:
            delivery_notes = self._split_delivery_note_pages(delivery_note_files)
            stats["upload_delivery_notes_order_count"] = len(delivery_notes.keys())
            stats["upload_delivery_notes_page_count"] = sum(len(pages) for pages in delivery_notes.values())
            try:
                delivery_stats = self._combine_delivery_notes(
                    delivery_notes,
                    order_sequence,
                    order_categories,
                    specific_name
                )
                if isinstance(delivery_stats, dict):
                    stats["processed_delivery_notes_page_count"] = int(delivery_stats.get("pages", 0) or 0)
                    stats["processed_delivery_notes_order_count"] = int(delivery_stats.get("orders", 0) or 0)
            except Exception as e:
                print(f"Lieferscheine konnten nicht verarbeitet werden: {e}")

        if shipping_label_files:
            labels = self._split_delivery_note_pages(shipping_label_files)
            stats["upload_shipping_labels_count"] = sum(len(pages) for pages in labels.values())
            try:
                stats["processed_shipping_labels_count"] = self._combine_shipping_labels(
                    labels,
                    order_sequence,
                    order_categories,
                    specific_name
                )
            except Exception as e:
                print(f"Versandlabels konnten nicht verarbeitet werden: {e}")

        return stats

    @staticmethod
    def _normalize_order_number(value):
        if pd.isna(value):
            return None
        order = str(value).strip()
        if order.startswith('#'):
            order = order[1:]
        return order if order else None

    def _collect_order_sequence(self, data):
        seen = set()
        sequence = []
        if 'Name' not in data.columns:
            return sequence

        for name in data['Name']:
            normalized = self._normalize_order_number(name)
            if normalized and normalized not in seen:
                sequence.append(normalized)
                seen.add(normalized)
        return sequence

    def _extract_order_number_from_text(self, text):
        patterns = [
            r'Bestellnummer\s*[:#]?\s*(\d+)',
            r'Commande\s*#\s?(\d+)',
            r'Order\s*#\s?(\d+)',
            r'#\s?(\d{4,})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return self._normalize_order_number(match.group(1))
        return None

    def _split_delivery_note_pages(self, delivery_note_files):
        delivery_notes = {}
        unknown_counter = 1

        for pdf_path in delivery_note_files:
            reader = PdfReader(pdf_path)
            current_order = None
            current_pages = []

            for page in reader.pages:
                text = page.extract_text() or ''
                order_number = self._extract_order_number_from_text(text)

                if order_number:
                    if current_order is None:
                        current_order = order_number
                    elif order_number != current_order:
                        if current_pages:
                            delivery_notes.setdefault(current_order, []).extend(current_pages)
                        current_order = order_number
                        current_pages = []
                elif current_order is None:
                    current_order = f"UNBEKANNT_{unknown_counter}"
                    unknown_counter += 1

                current_pages.append(page)

            if current_pages and current_order:
                delivery_notes.setdefault(current_order, []).extend(current_pages)

        return delivery_notes

    def _combine_delivery_notes(self, delivery_notes, order_sequence, order_categories, output_basename):
        if not delivery_notes:
            print("Keine Lieferscheine gefunden.")
            return {"pages": 0, "orders": 0}

        total_pages = sum(len(pages) for pages in delivery_notes.values())
        total_orders = len(delivery_notes.keys())

        writers = {
            "marmor": PdfWriter(),
            "schwarzer_marmor": PdfWriter(),
            "rest": PdfWriter(),
        }

        added_orders = set()

        def add_pages(order, pages):
            category = order_categories.get(order, "rest")
            writer = writers.get(category, writers["rest"])
            for page in pages:
                writer.add_page(page)
            added_orders.add(order)

        for order in order_sequence:
            pages = delivery_notes.get(order)
            if pages:
                add_pages(order, pages)

        for order, pages in delivery_notes.items():
            if order in added_orders:
                continue
            add_pages(order, pages)

        output_files = {
            "marmor": f"{output_basename}_Lieferscheine_Marmor.pdf",
            "schwarzer_marmor": f"{output_basename}_Lieferscheine_Schwarzer_Marmor.pdf",
            "rest": f"{output_basename}_Lieferscheine_Rest.pdf",
        }

        for key, writer in writers.items():
            if len(writer.pages) == 0:
                continue
            output_path = os.path.join(self.output_folder, output_files[key])
            with open(output_path, 'wb') as output_pdf:
                writer.write(output_pdf)
            print(f"Lieferscheine ({key}) gespeichert in {output_path} (geordnet nach CSV-Reihenfolge).")
        return {"pages": total_pages, "orders": total_orders}

    def _combine_shipping_labels(self, labels, order_sequence, order_categories, output_basename):
        if not labels:
            print("Keine Versandlabels gefunden.")
            return 0

        total_pages = sum(len(pages) for pages in labels.values())

        writers = {
            "marmor": PdfWriter(),
            "schwarzer_marmor": PdfWriter(),
            "rest": PdfWriter(),
        }

        added_orders = set()

        def add_pages(order, pages):
            category = order_categories.get(order, "rest")
            writer = writers.get(category, writers["rest"])
            for page in pages:
                writer.add_page(page)
            added_orders.add(order)

        for order in order_sequence:
            pages = labels.get(order)
            if pages:
                add_pages(order, pages)

        for order, pages in labels.items():
            if order in added_orders:
                continue
            add_pages(order, pages)

        output_files = {
            "marmor": f"{output_basename}_Versandlabels_Marmor.pdf",
            "schwarzer_marmor": f"{output_basename}_Versandlabels_Schwarzer_Marmor.pdf",
            "rest": f"{output_basename}_Versandlabels_Rest.pdf",
        }

        for key, writer in writers.items():
            if len(writer.pages) == 0:
                continue
            output_path = os.path.join(self.output_folder, output_files[key])
            with open(output_path, 'wb') as output_pdf:
                writer.write(output_pdf)
            print(f"Versandlabels ({key}) gespeichert in {output_path} (geordnet nach CSV-Reihenfolge).")
        return total_pages

    def _categorize_orders(self, data):
        categories = {}
        if 'Name' not in data.columns or 'Lineitem sku' not in data.columns:
            return categories

        grouped = data.groupby('Name')
        for name, group in grouped:
            order = self._normalize_order_number(name)
            if not order:
                continue

            led_rows = group[group['Lineitem name'].str.contains('Untersetzer', case=False, na=False)]

            led_skus_all = set(
                str(sku).strip()
                for sku in led_rows['Lineitem sku'].dropna().astype(str)
                if str(sku).strip() and str(sku).strip() not in self.accessory_skus
            )

            if not led_skus_all:
                categories[order] = "rest"
                continue

            only_marmor = all(self.marmor_sku_marker in sku for sku in led_skus_all)
            only_schwarzer_marmor = all(self.schwarzer_marmor_sku_marker in sku for sku in led_skus_all)

            if only_marmor:
                categories[order] = "marmor"
            elif only_schwarzer_marmor:
                categories[order] = "schwarzer_marmor"
            else:
                categories[order] = "rest"

        return categories
