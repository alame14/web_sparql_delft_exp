# /////////////////////////////////////////////////////////////////////////////
# Post-processing Script
# /////////////////////////////////////////////////////////////////////////////

import json
import os
import glob
import logging
from time import time


class MicrodataOfferLinker:

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self):
        
        # Configure logging
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger()
        
        self.data = None
        self.result = []
        self.rename_map_microdata = {}  # Mapping ancien -> nouveau pour les microdata
        self.rename_map_offer = {}     # Mapping ancien -> nouveau pour les offer

        
    # -------------------------------------------------------------------------
    # Main Processing Method
    # -------------------------------------------------------------------------
   
    def process(self, input_data, output_file):
        start_time = time()
        self.logger.info("***** Processor Run *****")  
        self.logger.info("Process started")
        
        self.load_json(input_data)
        self.logger.info("Data file loaded successfully")
        
        self.links_web_microdata_offer()
        # self.save_data(self.result, self._get_step_output_filename(output_file, 1))
        self.logger.info("Link web, microdata and offers (step 1)")
        
        self.rename_microdata()
        # self.save_data(self.result, self._get_step_output_filename(output_file, 2))
        self.logger.info("Rename microdata (step 2)")
        
        self.rename_offers()
        # self.save_data(self.result, self._get_step_output_filename(output_file, 3))
        self.logger.info("Rename offers (step 3)")
        
        self.apply_mapping_to_rows()
        self.logger.info("Apply mapping to rows (final step)")
        
        self.save_data(self.data, output_file)
        self.logger.info(f"Final output files saved: {output_file}")
            
        end_time = time()
        self.logger.info(f"Process completed in {end_time - start_time:.2f} seconds")
        
        
    # -------------------------------------------------------------------------
    # Loading/saving methods
    # -------------------------------------------------------------------------
        
    def load_json(self, input_path):
        """
        Charge le fichier JSON depuis le chemin d'entrée.
        """
        with open(input_path, 'r', encoding='utf-8') as file:
            self.data = json.load(file)

    def save_data(self, data, output_path):
        """
        Sauvegarde les résultats dans un fichier JSON au chemin de sortie.
        """
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)


    def _get_step_output_filename(self, base_filename, step):
        base, ext = os.path.splitext(base_filename)
        return f"{base}_kw{step}{ext}"
    

        
    # -------------------------------------------------------------------------
    # Microdata/Offer Linking Methods
    # -------------------------------------------------------------------------

    def links_web_microdata_offer(self):
        """
        Analyses queries to structure links between web, microdata and offer.
        """
        if not self.data:
            raise ValueError("JSON data is not loaded. Call load_json() first.")
        
        for query in self.data.get("queries", []):
            query_id = query.get("query_id")
            query_result = query.get("obtained_data_query_result", {})
            query_result = query.get("obtained_data_query_result", {})
            if isinstance(query_result, list) and not query_result:
                query_result = {}
            rows = query_result.get("rows", [])
    
            # Liaison des relations web -> microdata
            web_data = self.link_web_microdata(rows)
    
            # Liaison des relations microdata -> offer
            microdata_data = self.link_microdata_offer(rows)
    
            # Conversion en liste pour sérialisation
            web_list = list(web_data.values())
            microdata_list = list(microdata_data.values())
    
            # Ajout au résultat final
            self.result.append({
                "query_id": query_id,
                "web": web_list,
                "microdata": microdata_list
            })
   
    
    def link_web_microdata(self, rows):
        """
        Crée les relations entre web et microdata.
        """
        web_data = {}
        for row in rows:
            web = row.get("web", {}).get("value")
            microdata = row.get("microdata", {}).get("value")

            if web:
                if web not in web_data:
                    web_data[web] = {"value": web, "microdata": []}
                if microdata and microdata not in web_data[web]["microdata"]:
                    web_data[web]["microdata"].append(microdata)
        return web_data


    def link_microdata_offer(self, rows):
        """
        Crée les relations entre microdata et offer.
        """
        microdata_data = {}
        for row in rows:
            microdata = row.get("microdata", {}).get("value")
            offer = row.get("offer", {}).get("value")

            if microdata:
                if microdata not in microdata_data:
                    microdata_data[microdata] = {"value": microdata, "offer": []}
                if offer and offer not in microdata_data[microdata]["offer"]:
                    microdata_data[microdata]["offer"].append(offer)
        return microdata_data


    # -------------------------------------------------------------------------
    # Renaming Methods
    # -------------------------------------------------------------------------

    def rename_microdata(self):
        for query in self.result:
            web_data = query.get("web", [])
            microdata_data = query.get("microdata", [])
            
            for web_entry in web_data:
                web_url = web_entry["value"]
                new_microdata_list = []
                
                for index, old_microdata_uri in enumerate(web_entry["microdata"], start=1):
                    # Nouveau nom pour la microdata
                    new_microdata_uri = f"{web_url}/microdata/{index}"
                    
                    # Enregistrer le mapping ancien -> nouveau
                    self.rename_map_microdata[old_microdata_uri] = new_microdata_uri
                    
                    # Mettre à jour la microdata
                    new_microdata_list.append({
                        "old_uri": old_microdata_uri,
                        "new_uri": new_microdata_uri
                    })
                
                # Remplacer la liste de microdata par la version renommée
                web_entry["microdata"] = new_microdata_list
            
            # Mettre à jour les microdata dans la liste principale
            for microdata_entry in microdata_data:
                old_value = microdata_entry["value"]
                if old_value in self.rename_map_microdata:
                    microdata_entry["value"] = self.rename_map_microdata[old_value]
                    

    def rename_offers(self):
        for query in self.result:
            microdata_data = query.get("microdata", [])
            
            for microdata_entry in microdata_data:
                old_microdata_value = microdata_entry["value"]
                if old_microdata_value in self.rename_map_microdata:
                    microdata_entry["value"] = self.rename_map_microdata[old_microdata_value]
                
                new_offer_list = []
                for index, old_offer_uri in enumerate(microdata_entry.get("offer", []), start=1):
                    # Nouveau nom pour l'offer
                    new_offer_uri = f"{microdata_entry['value']}/offer/{index}"
                    
                    # Enregistrer le mapping ancien -> nouveau pour offer
                    self.rename_map_offer[old_offer_uri] = new_offer_uri
                    
                    # Ajouter l'offer renommé
                    new_offer_list.append({
                        "old_uri": old_offer_uri,
                        "new_uri": new_offer_uri
                    })
                
                # Mettre à jour la liste des offers dans microdata
                microdata_entry["offer"] = new_offer_list


    # -------------------------------------------------------------------------
    # Data Update Methods
    # -------------------------------------------------------------------------

    def apply_mapping_to_rows(self):
        """
        Applique les mappings aux données dans les lignes (rows) des résultats de requêtes.
        """
        for query in self.data.get("queries", []):
            query_result = query.get("obtained_data_query_result", {})
            if isinstance(query_result, list) and not query_result:
                query_result = {}
            rows = query_result.get("rows", [])
            for row in rows:
                # Remap microdata
                microdata_value = row.get("microdata", {}).get("value")
                if microdata_value in self.rename_map_microdata:
                    row["microdata"]["value"] = self.rename_map_microdata[microdata_value]
                
                # Remap offer
                offer_value = row.get("offer", {}).get("value")
                if offer_value in self.rename_map_offer:
                    row["offer"]["value"] = self.rename_map_offer[offer_value]




# =============================================================================
#  Main Script
# =============================================================================

if __name__ == '__main__':
    print("\n***** Microdata Offer Linking *****\n")

    base_folder = 'working_files/results_simple'
    
    # linker = MicrodataOfferLinker()
    # input_path = f'{base_folder}/bfp_query_price_result.json'
    # output_path = f'{base_folder}/bfp_query_price_result.json'
    # linker.process(input_path, output_path)

    json_files = glob.glob(os.path.join(base_folder, "*.json"))
    
    for json_file in json_files:
        linker = MicrodataOfferLinker()
        linker.process(json_file, json_file)
