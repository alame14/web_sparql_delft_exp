import requests
from bs4 import BeautifulSoup
import json


# =============================================================================
#  W3MetadataExtractor Class
# =============================================================================

class W3MetadataExtractor:

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, logger=None):
        self.logger = logger
        self.metadata_dict = {}
        

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------

    def get_metadata(self, url, metadata_type=None):
        self.add_web_page(url)
        metadata = self.metadata_dict.get(url, {})
        if metadata_type:
            return metadata.get(metadata_type, {})
        return metadata
    
    def get_all_metadata(self):
        return self.metadata_dict
    
    def get_metadata_types(self, url):
        metadata = self.get_metadata(url)
        print(metadata)
        return [key for key, value in metadata.items() if value]

    
    # -------------------------------------------------------------------------
    # Microdata Access Methods
    # -------------------------------------------------------------------------

    # *** Microdata by URL ***

    # def get_microdata_by_url(self, url):
    #     print('----- microdata extration using W3MetadataExtractor')
    #     return self.get_metadata(url, metadata_type='json_ld')

    def get_microdata_by_url(self, url):
        print('----- microdata extration using W3MetadataExtractor')
        try:
            return self.extract_json_ld(url)
        except requests.RequestException as e:
            print(f"Error extracting metadata from {url}: {e}")
            return {}
    
    
    def extract_json_ld(self, url):
        """Extract JSON-LD microdata from a given URL."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                json_ld = soup.find('script', type='application/ld+json')
                if json_ld:
                    self.logger.info(f"JSON-LD successfully extracted from {url}")
                    return json.loads(json_ld.string)
            else:
                self.logger.warning(f"Error fetching {url}: {response.status_code} {response.reason}")
        except requests.RequestException as e:
            self.logger.error(f"Request error for {url}: {e}")
        except json.JSONDecodeError:
            self.logger.warning(f"Invalid JSON-LD format in {url}.")
        return {}
        

    # -------------------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------------------    

    def add_web_page(self, url):
        if url not in self.metadata_dict:
            self._extract_and_store_metadata(url)

    def force_refresh_metadata(self, url=None):
        if url:
            self._extract_and_store_metadata(url)
        else:
            for url in self.metadata_dict.keys():
                self._extract_and_store_metadata(url)

    def clear_metadata(self):
        self.metadata_dict.clear()


    # -------------------------------------------------------------------------
    # Extractors
    # -------------------------------------------------------------------------

    def _extract_and_store_metadata(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            page_content = response.content

            metadata = {
                'json_ld': self.extract_json_ld(page_content),
                'rdfa': self.extract_rdfa(page_content),
                'microdata': self.extract_microdata(page_content)
            }
            self.metadata_dict[url] = metadata
        except requests.RequestException as e:
            print(f"Error extracting metadata from {url}: {e}")
            self.metadata_dict[url] = {
                'json_ld': {},
                'rdfa': {},
                'microdata': {}
            }

    # def extract_json_ld(self, content):
    #     soup = BeautifulSoup(content, 'html.parser')
    #     json_ld = soup.find_all('script', type='application/ld+json')
    #     data = []
    #     for tag in json_ld:
    #         try:
    #             data.append(json.loads(tag.string))
    #         except json.JSONDecodeError:
    #             continue
    #     return data
    
    def extract_rdfa(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        rdfa_data = soup.find_all(attrs={'typeof': True})
        data = []
        for tag in rdfa_data:
            data.append(str(tag))
        return data

    def extract_microdata(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        microdata_items = soup.find_all(itemscope=True)
        data = []
        for item in microdata_items:
            item_dict = {}
            for prop in item.find_all(itemprop=True):
                item_dict[prop['itemprop']] = prop.get('content', prop.text)
            data.append(item_dict)
        return data
