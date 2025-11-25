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
    
    def calculate_total_quantities_by_item_type_per_order(self, data):
        """ Berechnet die Gesamtanzahl der bestellten LED-Untersetzer, Glas-Trinkhalme und Holzaufsteller pro Bestellung
        und fügt entsprechende Spalten hinzu. """

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

        # Holzaufsteller
        holz_mask = data['Lineitem name'].str.contains("Holzaufsteller", case=False, na=False)
        holz_sums = (
            data[holz_mask]
            .groupby('Name')['Lineitem quantity']
            .sum()
            .reset_index(name='Total Holzaufsteller')
        )

        # Zusammenführen der berechneten Werte mit dem ursprünglichen DataFrame
        data = pd.merge(data, led_sums, on='Name', how='left')
        data = pd.merge(data, glas_sums, on='Name', how='left')
        data = pd.merge(data, holz_sums, on='Name', how='left')

        # Fehlende Werte (z. B. wenn keine Untersetzer oder Trinkhalme enthalten sind) auf 0 setzen
        data['Total LED Untersetzer'] = data['Total LED Untersetzer'].fillna(0).astype(int)
        data['Total Glas Trinkhalme']  = data['Total Glas Trinkhalme'].fillna(0).astype(int)
        data['Total Holzaufsteller'] = data['Total Holzaufsteller'].fillna(0).astype(int)

        print("Anzahl der bestellten Produkte der jeweiligen Produkttypen pro Bestellung berechnet und hinzugefügt.")
        return data

    
    def remove_columns(self, data, columns_to_remove):
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
        """
        Berechnet das Gesamtgewicht einer Bestellung

        Das Gewicht der LED-Untersetzer wird dabei wie bisher über die led_coaster_weight_map ermittelt,
        basierend auf der Spalte 'Total LED Untersetzer'.
    
        Für die Glas-Trinkhalme gilt:
          - Anzahl der bestellten Glas-Trinkhalme wird mit 0,13 multipliziert."""
    
        def calculate_weight(row):
            weight_glass_straw_package = 0.126  # Gewicht pro Glas-Trinkhalm-Packung in kg
            weight_wood_stand = 0.117  # Gewicht pro Holzaufsteller in kg

            # LED-Gewicht ermitteln: Basierend auf der Gesamtanzahl der LED-Untersetzer
            total_led = int(row['Total LED Untersetzer'])
            led_weight = self.led_coaster_weight_map.get(total_led)
            # Falls kein Eintrag in der Map vorhanden ist, kann alternativ ein Standardwert (z.B. 0) genutzt werden
            if led_weight is None and total_led == 0:
                led_weight = 0.1
            if led_weight is None and total_led > 28:
                led_weight = total_led * 0.0345
        
            # Glas-Trinkhalme: Anzahl der bestellten Glas-Trinkhalme
            total_glass = int(row['Total Glas Trinkhalme'])
            glass_weight = total_glass * weight_glass_straw_package

            # Holzaufsteller
            total_wood = int(row['Total Holzaufsteller'])
            wood_weight = total_wood * weight_wood_stand
        
            total_weight = led_weight + glass_weight + wood_weight

            # Aufrunden auf 0,1 kg-Schritte
            total_weight = math.ceil(total_weight * 10) / 10

            # Rückgabe als Float
            return total_weight
    
        # Sicherstellen, dass die relevanten Spalten als int vorliegen
        data['Total LED Untersetzer'] = data['Total LED Untersetzer'].astype(int)
        data['Total Glas Trinkhalme'] = data['Total Glas Trinkhalme'].astype(int)
        data['Total Holzaufsteller'] = data['Total Holzaufsteller'].astype(int)

        # Gewichtsspalte für alle Bestellungen berechnen
        data['Weight'] = data.apply(lambda row: calculate_weight(row) if pd.notnull(row['Shipping Country']) else '', axis=1)

        print("Gewichtsspalte für alle Bestellungen außer DE basierend auf LED-Untersetzer, Glas-Trinkhalmen und Holzaufsteller hinzugefügt.")
        return data

    def split_shipping_street(self, data):
        """ Spalte 'Shipping Street' aufteilen und 'Shipping Supplement' hinzufügen. Zusätzlich werden 'Stiege' und 'Top' hinzugefügt, wenn das Land 'AT' (Österreich) ist."""
        street_index = data.columns.get_loc('Shipping Street')
        data.insert(street_index + 1, 'Shipping Supplement', '')

        for index, row in data.iterrows():
            street = row['Shipping Street']
            parts = street.split(',', 1)  # Split at the first comma only
            data.at[index, 'Shipping Street'] = parts[0].strip()
            if len(parts) > 1:
                data.at[index, 'Shipping Supplement'] = parts[1].strip()

        print(f"Spalte 'Shipping Street' aufgeteilt.")
        return data
    
    def add_austria_specific_columns(self, data):
        """ Fügt die Spalten 'Stiege' und 'Top' hinzu, unabhängig vom Land. """
        street_index = data.columns.get_loc('Shipping Street')
        # Spalten "Stiege" und "Top" hinzufügen
        data.insert(street_index + 2, 'Stiege', '')
        data.insert(street_index + 3, 'Top', '')
        print("Spalten 'Stiege' und 'Top' hinzugefügt.")
        return data
    
    def add_manufacturer_costs(self, data):
        """
        Fügt pro Bestellung den 'Manufacturer Cost'-Wert hinzu (nur erste Zeile jeder Bestellung),
        berechnet externe Produktkosten und fügt am Ende eine Gesamtsummen-Zeile mit
        Produktanzahlen und Bestellanzahl hinzu.
        """

        # Preise
        unit_price_led_coaster = 1.22           # pro LED-Untersetzer
        price_sticker_front = 0.05              # Aufkleber Vorderseite
        price_sticker_back = 0.06               # Aufkleber Rückseite
        price_additional_battery = 0.25         # zusätzliche Batterie

        price_pack_2 = 0.27                     # 2er-Schachtel
        price_pack_4 = 0.27                     # 4er-Schachtel
        price_packing_in_packs = 0.12           # Verpacken in Schachteln

        price_delivery_package = 0.30           # Versandverpackung
        order_processing_fee = 1.87             # Fixe Auftragsbearbeitungskosten

        price_packing_external_product = 0.25   # Verpackung externer Produkte (Beispiel: Casa Vivida Gläser)
        unit_price_glass_straw = 1.70           # pro Glasstrohhalm
        unit_price_wooden_stand = 4.50          # pro Holzaufsteller

        # Neue Spalte anlegen
        data['Manufacturer Cost'] = ''

        # Eindeutige Bestellungen bestimmen
        unique_orders = data['Name'].unique()

        # Speichert die berechneten Kosten je Bestellung zur späteren Summierung
        total_costs = []

        # Zähler für Summenzeile
        total_led = 0
        total_glass = 0
        total_wood = 0
        total_external = 0
        total_pack_2 = 0
        total_pack_4 = 0


        for order in unique_orders:
            order_rows = data[data['Name'] == order]
            first_row_idx = order_rows.index[0]
            subset = data.loc[first_row_idx]

            # Mengen
            quantity_led = int(subset.get('Total LED Untersetzer', 0))
            quantity_glass = int(subset.get('Total Glas Trinkhalme', 0))
            quantity_wood = int(subset.get('Total Holzaufsteller', 0))

            # Externe Produkte (alle, die kein Untersetzer, Glas-Trinkhalm oder Holzaufsteller sind)
            product_names = order_rows['Lineitem name'].unique()
            external_products = [p for p in product_names if not any(x in p for x in ['Untersetzer', 'Glas-Trinkhalme', 'Holzaufsteller'])]
            qty_external = order_rows[order_rows['Lineitem name'].isin(external_products)]['Lineitem quantity'].sum() if len(external_products) > 0 else 0

            # LED-Untersetzer-Kosten
            product_cost_led = quantity_led * (unit_price_led_coaster + price_sticker_front + price_sticker_back + price_additional_battery)


            # Verpackungslogik (nur 2er und 4er Schachteln)
            qty_4 = quantity_led // 4
            remainder = quantity_led % 4

            if remainder == 3:
                qty_4 += 1
                qty_2 = 0
            elif remainder == 1:
                qty_2 = 1
            else:
                qty_2 = remainder // 2

            # Verpackungszähler erhöhen
            total_pack_2 += qty_2
            total_pack_4 += qty_4


            packaging_cost = qty_4 * price_pack_4 + qty_2 * price_pack_2
            packing_work_cost = (qty_4 + qty_2) * price_packing_in_packs

            # Glas-Trinkhalme und Holzaufsteller
            glass_cost = quantity_glass * unit_price_glass_straw
            wood_cost = quantity_wood * unit_price_wooden_stand

            # Externe Produktkosten
            external_cost = qty_external * price_packing_external_product

            # Gesamtkosten
            total_cost = (
                product_cost_led
                + packaging_cost
                + packing_work_cost
                + glass_cost
                + wood_cost
                + external_cost
                + order_processing_fee
                + price_delivery_package
            )

            total_cost = round(total_cost, 2)
            data.at[first_row_idx, 'Manufacturer Cost'] = f"{total_cost:.2f}".replace('.', ',')

            # Zähler erhöhen
            total_led += quantity_led
            total_glass += quantity_glass
            total_wood += quantity_wood
            total_external += qty_external
            total_costs.append(total_cost)

        # Gesamtsumme & Zusammenfassung
        total_sum = round(sum(total_costs), 2)
        total_orders = len(unique_orders)

        total_row = pd.Series({col: '' for col in data.columns})
        total_row['Name'] = 'GESAMTSUMME'
        total_row['Manufacturer Cost'] = f"{total_sum:.2f}".replace('.', ',')
        total_row['Total LED Untersetzer'] = total_led
        total_row['Total Glas Trinkhalme'] = total_glass
        total_row['Total Holzaufsteller'] = total_wood
        total_row['Externe Produkte'] = total_external
        total_row['Anzahl Bestellungen'] = total_orders
        total_row['Gesamt 2er-Schachteln'] = total_pack_2
        total_row['Gesamt 4er-Schachteln'] = total_pack_4


        data = pd.concat([data, pd.DataFrame([total_row])], ignore_index=True)

        print("Herstellerkosten berechnet, externe Produkte berücksichtigt und Gesamtsumme mit Produktanzahlen hinzugefügt.")
        return data
