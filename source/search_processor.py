import os
import re
from urllib.parse import urlparse
import time

from web_service.services import WebService
from web_service.controlled_web_test_service import ControlledWebTestService
from web_service.simulated_search_service import SimulatedSearchService
from web_service.ddg_search_service import DuckDuckGoSearchService
from sparql_result_handler import SPARQLResultHandler

from metahub.url_converter import URLConverter


# =============================================================================
#  SearchService Class
# =============================================================================

class SearchProcessor:

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, query_pattern, web_service, logger=None):
        self.logger = logger
        self.query_pattern = query_pattern
        self.web_service = web_service
        self._web_service_class = self._init_web_service_class(web_service)
        self.query_list = []
        self.search_results = {}
        self.pause_time = 2
        self.search_total_time = 0
        self.total_searches = 0
        self.url_converter = URLConverter(cache_enabled=True)
        
        
    def _init_web_service_class(self, web_service):
        web_service_class = None
        if self.web_service == WebService.BFP_CWTS:  
            web_service_class = ControlledWebTestService(self.web_service.data_path)
            web_service_class.add_additional_data(self.web_service.additional_data_path)
        elif self.web_service == WebService.BFP_SWSS:
            web_service_class = SimulatedSearchService(self.web_service.data_path)
        elif self.web_service == WebService.DDG_WSS:
            web_service_class = DuckDuckGoSearchService(results_count=30)
        else:    
            raise Exception(f'web_service unknown: {self.web_service}')
        return web_service_class
        
    
    # -------------------------------------------------------------------------
    # Accessor(s)
    # -------------------------------------------------------------------------
    
    @property
    def service_name(self):
        return self.web_service.name
    
    
    # -------------------------------------------------------------------------
    # Queries Generation Methods
    # -------------------------------------------------------------------------

    def generate_query_list(self, kg_data):
        self.logger.debug("Query Generation.")
        self.query_list = []
        if not self.query_pattern:
            return self.query_list
    
        # kg_data = self._convert_columns(kg_data)
        kg_data = self._check_and_adapt_kg_data(kg_data)
        for row in kg_data['rows']:
            query = self.query_pattern
            for var in kg_data['columns']:
                var_placeholder = f"{{?{var}}}"
                if var_placeholder in query:
                    if var in row:
                        entity_value = row[var]['value']
                        entity_name = self._specify_entity_name(entity_value)
                        query = query.replace(var_placeholder, entity_name)
                    else:
                        query = None
                        break
            if query is not None:
                query = self._finalize_query(query)
            self.query_list.append((query, row))
        
        return self.query_list
    
    def _specify_entity_name(self, entity_value):
        _, local_name = self._split_uri(entity_value)
        res = local_name.replace('_', ' ')
        return res
    
    @classmethod 
    def _check_and_adapt_kg_data(cls, kg_data):
        
        if kg_data is None: 
            kg_data = { 'columns': [], 'rows': [] }
            
        else:      
            if SPARQLResultHandler.is_valid_result_xml(kg_data):
                kg_data = SPARQLResultHandler.convert_result_xml_to_dict(kg_data)
            
            if SPARQLResultHandler.is_valid_result_dict(kg_data):
                # print('----- standardize kg_data')
                kg_data = SPARQLResultHandler.convert_columns(kg_data)
            else:
                raise ValueError("Invalid result format. Expected SPARQL XML or valid dictionary.")

        return kg_data
    
    
    @classmethod
    def _split_uri(cls, uri: str):
        parsed_uri = urlparse(uri)
        base_uri = f"{parsed_uri.scheme}://{parsed_uri.netloc}/"
        local_name = os.path.basename(parsed_uri.path)
        return base_uri, local_name
    
    
    @classmethod
    def _finalize_query(cls, query: str) -> str:
        return query.replace('{?', '').replace('}', '')


    # -------------------------------------------------------------------------
    # Search Methods
    # -------------------------------------------------------------------------

    def perform_searches(self,  web_query_max=2):
        self.logger.debug("Perform searches for the list of queries.")
        self.search_results = []
        self.search_total_time = 0
        self.total_searches = 0
        for i, (query, row) in enumerate(self.query_list[:web_query_max]):
            try:
                time_taken = self._measure_time(self._search, query, row)
                self.search_total_time += time_taken
                self.total_searches += 1
                if self._web_service_class.rate_limit:
                    time.sleep(self.pause_time)
            except Exception as e:
                print(f"An error occurred while searching for '{query}': {e}")
                self.search_results.append((query, row, []))
        return self.search_results
    
    
    def _search(self, query, row):
        self.logger.debug(f"Searching for: {query}")  
        search_result, search_time = self._web_service_class.search_by_query(query)
        start_time = time.time()
        self.search_results.append((query, row, search_result))
        end_time = time.time()
        return search_time + (end_time - start_time)


    def _measure_time(self, func, *args):
        """Measure the time taken by a function to execute."""
        start_time = time.time()
        search_time = func(*args)
        end_time = time.time()
        return search_time or (end_time - start_time)


    # -------------------------------------------------------------------------
    # Format Methods
    # -------------------------------------------------------------------------
        
    def format_results(self, query_pivot):
        self.logger.debug("Web Search Result Formatting.") 
        # print('----- query_pattern: ', self.query_pattern)
        # print('----- search_results: ', self.search_results)
        
        web_pivot_variable = query_pivot.web_pivot_variable
        select_vars = self._extract_select_vars(self.query_pattern, web_pivot_variable)
        formatted_results = {
            "columns": select_vars,
            "rows": []
        }
    
        for query, row, search_result in self.search_results:
            if search_result:
                for web_url in search_result:
                    web_uriref = self.url_converter.url_to_uriref(web_url)
                    result_row = {}
                    for var in select_vars:
                        var_name = var
                        if var_name in row:
                            result_row[var_name] = row[var_name]
                        else:
                            result_row[var_name] = {"type": "url", "value": web_url}
                            # result_row[var_name] = {"type": "url", "value": web_uriref}
                    formatted_results["rows"].append(result_row)
            else:
                result_row = {}
                for var in select_vars:
                    var_name = var
                    if var_name in row:
                        result_row[var_name] = row[var_name]
                    else:
                        result_row[var_name] = {"type": "url", "value": ""}
                formatted_results["rows"].append(result_row)
    
        return formatted_results


    def _extract_select_vars(self, query, web_pivot_variable):
        # Initialize an empty list to store the extracted variables
        select_vars = []
    
        # Use a simple parsing approach to find all occurrences of {?variable} in the query
        pattern = r'\{\?(\w+)\}'
        matches = re.findall(pattern, query)
        
        # Add all found variables to the list
        for match in matches:
            select_vars.append(match)
    
        # Add the web_pivot_variable to the list
        select_vars.append(web_pivot_variable)
    
        return select_vars



# =============================================================================
#  Base Use Test
# =============================================================================

if __name__ == '__main__':
    print("\n *** Base Use Test ***")

    query = '{?book} purchase'
    service = WebService.BFP_SWSS
    
    kg_data = {
        "columns": ["book"],
        "rows": [
            {"book": {"type": "uri", "value": "http://dbpedia.org/resource/Carpe_Jugulum"}},
            {"book": {"type": "uri", "value": "http://dbpedia.org/resource/Pyramids_(novel)"}}
        ]
    }
    
    processor = SearchProcessor(query, service)
    processor.generate_query_list(kg_data)
    processor.perform_searches()
    formatted_results = processor.format_results('web')
    print("\nQuery list:", processor.query_list)
    print("\nSearch results:", processor.search_results)
    print("\nFormatted results:", formatted_results)
