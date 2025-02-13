import requests
import json
import os
import logging
from werkzeug.datastructures import ImmutableMultiDict

DEFAULT_KG_NAME = 'dbpedia'


# =============================================================================
#  EndpointManager: class to manage KG SPARQL endpoint
# =============================================================================

class EndpointManager:
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, kg_spec_path, logger=None):
        self.logger = logger
        self.kg_spec_table = self._load_kg_table(kg_spec_path)
        self.set_kg_definition(DEFAULT_KG_NAME)
        self.num = 0
          
        
    def _load_kg_table(self, kg_table_path):
        logging.debug(f"Attempting to load configuration file: {kg_table_path}")
        
        if not os.path.exists(kg_table_path):
            logging.error(f"KG Table file not found: {kg_table_path}.")
            raise FileNotFoundError(f"KG Table file not found: {kg_table_path}.")
        
        try:
            kg_table = {}
            with open(kg_table_path, 'r') as file:
                kg_table = json.load(file)
                logging.debug(f"KG Table file loaded successfully ({len(kg_table)}).")
                
                if not isinstance(kg_table, dict):
                    logging.error("Invalid KG Table file.")
                    raise ValueError("Invalid KG Table file.")
            return kg_table                                        
        except json.JSONDecodeError as e:
            logging.error(f"Error reading JSON file: {str(e)}")
            raise ValueError(f"Error reading JSON file: {str(e)}")
        except Exception as e:
            logging.error(f"An error occurred while loading KG Table: {str(e)}")
            raise RuntimeError(f"An error occurred while loading KG Table: {str(e)}")
          
            
    # -------------------------------------------------------------------------
    # Accessor(s)
    # -------------------------------------------------------------------------

    def get_kg_table(self):
        return self.kg_spec_table
    
    def set_kg_definition(self, new_kg_name):
        self.kg_definition = self.kg_spec_table[new_kg_name]

    def get_endpoint(self):
        return self.kg_definition["endpoint"]
 
          
    # -------------------------------------------------------------------------
    # Query Method(s)
    # -------------------------------------------------------------------------
    
    def execute_query(self, query):
        self.logger.debug(f'----- execute query on endpoint: {self.get_endpoint()}')
        params = {
            'query': query,
            'format': 'json'
        }
        # print(f'----- params: {params}')
        response = requests.get(self.get_endpoint(), params=params)
        # print(' ***** DEV *****')
        # print(f'----- response: {response.text}')
        # print(' ***** *** *****')
        if response.status_code == 200:
            # return response.json()
            return response
        else:
            response.raise_for_status()
           
            
    def ask(self, data):
        self.logger.debug(f'----- ask endpoint: {self.get_endpoint()}')
        # print(f'----- data: {data}')
          
        # Check the input data format and adapt it if necessary
        if isinstance(data, ImmutableMultiDict):
            adapted_data = data
        elif isinstance(data, str):
            adapted_data = {'query': data, 'format': 'xml'}
        else:
            raise ValueError("Unsupported data format")
            
        # print(f'----- adapted_data: {adapted_data}')
        
        response = requests.post(self.get_endpoint(), data=adapted_data)

        if response.status_code == 200:
            return response
        else:
            response.raise_for_status()


# =============================================================================
#  Basic Use Test
# =============================================================================

if __name__ == "__main__":
    
    pass


