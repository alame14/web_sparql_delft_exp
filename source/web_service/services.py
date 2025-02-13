from enum import Enum

class WebService(Enum):
    
    BFP_CWTS = ("Books for Purchase", 
                "Controlled Web Test Service",
                "data/bfp_webdata.json",
                "data/bfp_additional_data.json")
                    
    BFP_SWSS = ("Books for Purchase", 
                "Simulated Web Search Service",
                "data/bfp_web_queries.json",
                "data/bfp_additional_data.json")
    
    DDG_WSS = ("DuckDuckGo",
               "Web Search Service")


    def __init__(self, name, category, data_path=None, additional_data_path=None):
        self._name = name
        self._category = category
        self._data_path = data_path
        self._additional_data_path = additional_data_path

    @property
    def name(self):
        return self._name

    @property
    def category(self):
        return self._category

    @property
    def data_path(self):
        return self._data_path

    @property
    def additional_data_path(self):
        return self._additional_data_path
    

# Usage Example
if __name__ == "__main__":
    chosen_service = WebService.BFP_CWTS
    print(f"Name: {chosen_service.name}")
    print(f"Category: {chosen_service.category}")
    print(f"Data Path: {chosen_service.data_path}")
    print(f"Additional Data Path: {chosen_service.additional_data_path}")
