from enum import Enum

class WebExtractor(Enum):

    W3_ME = ("Worldwide Web", "Metadata Extractor")
    
    BFP_CWTME = ("Books for Purchase", 
                "Controlled Web Test Metadata Extractor",
                "data/bfp_webdata.json")


    def __init__(self, name, category, data_path=None, additional_data_path=None):
        self._name = name
        self._category = category
        self._data_path = data_path

    @property
    def name(self):
        return self._name

    @property
    def category(self):
        return self._category

    @property
    def data_path(self):
        return self._data_path
    

# Usage Example
if __name__ == "__main__":
    chosen_extrator = WebExtractor.BFP_CWTME
    print(f"Name: {chosen_extrator.name}")
    print(f"Category: {chosen_extrator.category}")
    print(f"Data Path: {chosen_extrator.data_path}")
