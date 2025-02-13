import os
import glob
import json
import logging
from time import time


class OfferFeatureLinker:

    def __init__(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger()
        
        self.data = None
        self.links = []
        self.rename_map_price = {}  # Mapping old -> new for prices
        self.rename_map_availability = {} # Mapping old -> new for availabilities
        self.rename_map_publisher = {}  # Mapping old -> new for publishers

        
    # -------------------------------------------------------------------------
    # Main Processing Method
    # -------------------------------------------------------------------------
       
    def process(self, input_data, output_file):
        start_time = time()
        self.logger.info("***** OfferFeatureLinker Run *****")
        self.logger.info("Process started")
        
        self.load_json(input_data)
        self.logger.info("Data file loaded successfully")
        
        self.link_offer_to_features()
        # self.save_data(self.links, self._get_step_output_filename(output_file, 1))
        self.logger.info("Link offer to features (step 1)")
        
        self.rename_prices()
        self.rename_availabilities()
        self.rename_publishers()
        self.logger.info("Rename features (step 2)")
        
        self.apply_mapping_to_rows()
        self.logger.info("Apply mapping to rows (final step)")
        
        self.save_data(self.data, output_file)
        self.logger.info(f"Final output file saved: {output_file}")
        
        end_time = time()
        self.logger.info(f"Process completed in {end_time - start_time:.2f} seconds")
        
        
    # -------------------------------------------------------------------------
    # Loading/saving methods
    # -------------------------------------------------------------------------
    
    def load_json(self, input_path):
        with open(input_path, 'r', encoding='utf-8') as file:
            self.data = json.load(file)
    
    def save_data(self, data, output_path):
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
 
    def _get_step_output_filename(self, base_filename, step):
        base, ext = os.path.splitext(base_filename)
        return f"{base}_s{step}{ext}"
    
    
    # -------------------------------------------------------------------------
    # Linking Methods
    # -------------------------------------------------------------------------  
 
    def link_offer_to_features(self):
        if not self.data:
            raise ValueError("JSON data is not loaded. Call load_json() first.")
        
        for query in self.data.get("queries", []):
            query_id = query.get("query_id")
            query_result = query.get("obtained_data_query_result", {})
            if isinstance(query_result, list) and not query_result:
                query_result = {}
            rows = query_result.get("rows", [])
        
        
            offer_data = {}
            offer_data = self.link_offer_to_price(rows, offer_data)
            offer_data = self.link_offer_to_availability(rows, offer_data)
            offer_data = self.link_offer_to_publisher(rows, offer_data)
            offer_list = list(offer_data.values())
        
            self.links.append({
                "query_id": query_id,
                "offers": offer_list
            })
    
    def link_offer_to_price(self, rows, offer_data):
        for row in rows:
            offer = row.get("offer", {}).get("value")
            price = row.get("price", {}).get("value")
        
            if offer:
                if offer not in offer_data:
                    offer_data[offer] = {"value": offer, "price": [], "availability": [], "publisher": []}
                if price and price not in offer_data[offer]["price"]:
                    offer_data[offer]["price"].append(price)
        
        return offer_data

    def link_offer_to_availability(self, rows, offer_data):
        for row in rows:
            offer = row.get("offer", {}).get("value")
            availability = row.get("availability", {}).get("value")
        
            if offer:
                if offer not in offer_data:
                    offer_data[offer] = {"value": offer, "price": [], "availability": [], "publisher": []}
                if availability and availability not in offer_data[offer]["availability"]:
                    offer_data[offer]["availability"].append(availability)
        
        return offer_data
    
    def link_offer_to_publisher(self, rows, offer_data):
        for row in rows:
            offer = row.get("offer", {}).get("value")
            publisher = row.get("publisher", {}).get("value")
        
            if offer:
                if offer not in offer_data:
                    offer_data[offer] = {"value": offer, "price": [], "availability": [], "publisher": []}
                if publisher and publisher not in offer_data[offer]["publisher"]:
                    offer_data[offer]["publisher"].append(publisher)
        
        return offer_data
  
    
    # -------------------------------------------------------------------------
    # Renaming Methods
    # -------------------------------------------------------------------------
  
    def rename_prices(self):
        for query in self.links:
            for offer in query.get("offers", []):
                updated_prices = []
                for price in offer.get("price", []):
                    new_name = f"{offer['value']}/price/{price}"
                    self.rename_map_price[price] = new_name
                    updated_prices.append(new_name)
                offer["price"] = updated_prices
    
  
    def rename_availabilities(self):
        for query in self.links:
            for offer in query.get("offers", []):
                updated_availabilities = []
                for availability in offer.get("availability", []):
                    new_name = f"{offer['value']}/availability/{availability}"
                    self.rename_map_availability[availability] = new_name
                    updated_availabilities.append(new_name)
                offer["availability"] = updated_availabilities
              
    def rename_publishers(self):
        for query in self.links:
            for offer in query.get("offers", []):
                updated_publishers = []
                for publisher in offer.get("publisher", []):
                    new_name = f"{offer['value']}/publisher/{publisher}"
                    self.rename_map_publisher[publisher] = new_name
                    updated_publishers.append(new_name)
                offer["publisher"] = updated_publishers
    
    
    # -------------------------------------------------------------------------
    # Data Update Methods
    # -------------------------------------------------------------------------   
    
    def apply_mapping_to_rows(self):
        for query in self.data.get("queries", []):
            query_result = query.get("obtained_data_query_result", {})
            if isinstance(query_result, list) and not query_result:
                query_result = {}
            rows = query_result.get("rows", [])
        
            for row in rows:
                price = row.get("price", {}).get("value")
                if price in self.rename_map_price:
                    row["price"]["value"] = self.rename_map_price[price]
                availability = row.get("availability", {}).get("value")
                if availability in self.rename_map_availability:
                    row["availability"]["value"] = self.rename_map_availability[availability]
                publisher = row.get("publisher", {}).get("value")
                if publisher in self.rename_map_publisher:
                    row["publisher"]["value"] = self.rename_map_publisher[publisher]


# =============================================================================
#  Main Script
# =============================================================================

if __name__ == '__main__':
    print("\n***** Offer Feature Linking *****\n")

    base_folder = 'working_files/results_simple'
    
    # linker = OfferFeatureLinker()
    # input_path = f'{base_folder}/bfp_query_price_result.json'
    # output_path = f'{base_folder}/bfp_query_price_result.json'
    # linker.process(input_path, output_path)
    
    json_files = glob.glob(os.path.join(base_folder, "*.json"))
    
    for json_file in json_files:
        linker = OfferFeatureLinker()
        linker.process(json_file, json_file)