import time
import json
import os
from typing import List, Dict, Optional


# =============================================================================
#  ControlledWebMetadataExtractor Class
# =============================================================================

class ControlledWebMetadataExtractor:

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, webdata_json_path, logger=None):
        self.logger = logger
        self.webdata_json_path = webdata_json_path
        self.data = self._load_data(webdata_json_path)
    
    def _load_data(self, json_path) -> List[Dict]:
        with open(json_path, 'r') as file:
            json_data = json.load(file)
            return json_data['web_data']
            
    
    # -------------------------------------------------------------------------
    # Accessor(s)
    # -------------------------------------------------------------------------

    def get_entry_count(self) -> int:
        return len(self.data)

    def get_dataset_title(self) -> str:
        return os.path.splitext(os.path.basename(self.webdata_json_path))[0]

    
    # -------------------------------------------------------------------------
    # Microdata Access Methods
    # -------------------------------------------------------------------------

    # *** Microdata by URL ***

    def get_microdata_by_url(self, url: str) -> Optional[Dict]:
        if self.logger: 
            self.logger.debug("-- Microdata extration using ControlledWebMetadataExtractor") 
        for entry in self.data:
            if url in entry['json_microdata']:
                return entry['json_microdata'][url]
        return None



# =============================================================================
#  Base use Test
# =============================================================================

if __name__ == "__main__":
    print("\n ***** ControlledWebMetadataExtractor Use Test ***** \n")
    data_dir_path = '../data/'
    webdata_json_path = f'{data_dir_path}bfp_webdata.json'
    
    start_time = time.time()
    extractor = ControlledWebMetadataExtractor(webdata_json_path)
    
    # Get microdata for a specific URL
    microdata = extractor.get_microdata_by_url('https://www.fnac.com/a8314981/Terry-Pratchett-Pyramids')
    print("\n -- Extraction time':", time.time() - start_time)
    print("\n -- Microdata for URL 'https://www.fnac.com/a8314981/Terry-Pratchett-Pyramids':", microdata)
    
    # Print entry count
    print("\n -- Entry Count:", extractor.get_entry_count())
    
    # Print dataset title
    print("\n -- Dataset Title:", extractor.get_dataset_title())

