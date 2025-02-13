import json
import os
from typing import List, Dict, Optional
import unicodedata
import time


# =============================================================================
#  ControlledWebTestService Class
# =============================================================================

class ControlledWebTestService:

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, webdata_json_path):
        self.webdata_json_path = webdata_json_path
        self.data = self._load_data(webdata_json_path)
        self.entity_map = self._build_entity_map()
        self.web_query_map = self._build_web_query_map()
        self.rate_limit = None
    
    def _load_data(self, json_path) -> List[Dict]:
        with open(json_path, 'r') as file:
            return json.load(file)
    
    def _build_entity_map(self) -> Dict[str, int]:
        entity_map = {}
        for entry in self.data:
            entity = entry['kg_entity_uri']
            entity_map[entity] = entry['id']
        return entity_map
    
    def _build_web_query_map(self) -> Dict[str, int]:
        web_query_map = {}
        for entry in self.data:
            query = entry['web_query']
            web_query_map[query] = entry['id']
        return web_query_map
    
    
    # -------------------------------------------------------------------------
    # Accessor(s)
    # -------------------------------------------------------------------------
    
    def get_supported_entities(self) -> List[str]:
        return list(self.entity_map.keys())

    def get_supported_queries(self) -> List[str]:
        return list(self.web_query_map.keys())

    def get_entry_count(self) -> int:
        return len(self.data)

    def get_dataset_title(self) -> str:
        return os.path.splitext(os.path.basename(self.webdata_json_path))[0]

    def add_additional_data(self, additional_json_path: str):
        additional_data = self._load_data(additional_json_path)
        for entry in additional_data:
            id = entry['id']
            if 'kg_entity_uri' in entry:
                if isinstance(entry['kg_entity_uri'], list):
                    for entity in entry['kg_entity_uri']:
                        self.entity_map[entity] = id
                else:
                    entity = entry['kg_entity_uri']
                    self.entity_map[entity] = id
            
            if 'web_query' in entry:
                if isinstance(entry['web_query'], list):
                    for query in entry['web_query']:
                        self.web_query_map[query] = id
                else:
                    query = entry['web_query']
                    self.web_query_map[query] = id
                    
    
    # -------------------------------------------------------------------------
    # Search Methods
    # -------------------------------------------------------------------------

    # *** URLs by Entity ***
    
    def search_by_entity(self, kg_entity_uri: str) -> Optional[List[str]]:
        id = self.entity_map.get(kg_entity_uri)
        if id is not None:
            entry = next((item for item in self.data if item["id"] == id), None)
            if entry:
                return entry['url_list']
        return None


    # *** URLs by Web Query ***
    
    def search_by_query(self, web_query: str) -> Optional[List[str]]:
        start_time = time.time()
        results = None
        
        # First pass: precise search
        id = self.web_query_map.get(web_query)
        if id is not None:
            entry = next((item for item in self.data if item["id"] == id), None)
            if entry:
                results = entry['url_list']
        
        # Second pass: extended search
        normalized_query = self._normalize_query(web_query)
        for query, id in self.web_query_map.items():
            if self._normalize_query(query) == normalized_query:
                entry = next((item for item in self.data if item["id"] == id), None)
                if entry:
                    results = entry['url_list']
                    continue

        end_time = time.time()
        elapsed_time = end_time - start_time
        
        return results, elapsed_time
    

    def _normalize_query(self, query: str) -> str:
        query = query.lower()  # Convert to lower case
        query = unicodedata.normalize('NFKD', query).encode('ASCII', 'ignore').decode('ASCII')  # Delete accents
        query = query.replace(' ', '').replace('_', '').replace('-', '')  # Delete spaces, hyphens and underscores
        return query

    
    # -------------------------------------------------------------------------
    # Microdata Access Methods
    # -------------------------------------------------------------------------

    # *** Microdata by URL ***

    def get_microdata_by_url(self, url: str) -> Optional[Dict]:
        for entry in self.data:
            if url in entry['json_microdata']:
                return entry['json_microdata'][url]
        return None



# =============================================================================
#  Base use Test
# =============================================================================

if __name__ == "__main__":
    print("\n ***** ControlledWebTestService Use Test ***** \n")
    data_dir_path = '../data/'
    webdata_json_path = f'{data_dir_path}bfp_webdata.json'
    additional_data_json_path = f'{data_dir_path}bfp_additional_data.json'
    
    service = ControlledWebTestService(webdata_json_path)
    
    # Print all supported entities
    print("\n -- Supported Entities:", service.get_supported_entities())
    
    # Print all supported queries
    print("\n -- Supported Queries:", service.get_supported_queries())
    
    # Get URLs for a specific entity
    entity_urls = service.search_by_entity('http://dbpedia.org/resource/Pyramids_(novel)')
    print("\n -- URLs for Entity 'http://dbpedia.org/resource/Pyramids_(novel)':", entity_urls)
    
    # Get URLs for a specific web query
    query_urls = service.search_by_query('Pyramids (novel) Terry Pratchett purchase')
    print("\n -- URLs for Query 'Pyramids (novel) Terry Pratchett purchase':", query_urls)
    
    # Get microdata for a specific URL
    microdata = service.get_microdata_by_url('https://www.fnac.com/a8314981/Terry-Pratchett-Pyramids')
    print("\n -- Microdata for URL 'https://www.fnac.com/a8314981/Terry-Pratchett-Pyramids':", microdata)
    
    # Print entry count
    print("\n -- Entry Count:", service.get_entry_count())
    
    # Print dataset title
    print("\n -- Dataset Title:", service.get_dataset_title())
    
    # Add additional data from another JSON file
    service.add_additional_data(additional_data_json_path)
    
    # Re-print all supported entities after adding additional data
    print("\n -- Supported Entities after adding additional data:", service.get_supported_entities())
    
    # Re-print all supported queries after adding additional data
    print("\n -- Supported Queries after adding additional data:", service.get_supported_queries())

    # Example of a search using a normalized web query
    query_urls = service.search_by_query('Pyramids-(novel) Terry Pratchett purchase')
    print("\n -- URLs for Query 'Pyramids-(novel) Terry Pratchett purchase':", query_urls)

