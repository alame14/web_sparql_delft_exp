import time
from rdflib import ConjunctiveGraph
from rdflib import URIRef

from metahub.graph_builder import GraphBuilder
from metahub.graph_refiner import GraphRefiner
from metahub.graph_marker import GraphMarker
from metahub.graph_loader import GraphLoader


# =============================================================================
#  GraphUpdater Class
# =============================================================================

class GraphUpdater:

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, graph, 
                 web_extractor_class, 
                 processing_stats,
                 logger=None
                 ):
        
        self.logger = logger
        self.graph = graph
        self.web_extractor_class = web_extractor_class
        
        self.processing_stats = processing_stats
        self.microdata_count = 0
        self.processing_time = { "extraction": 0, "building": 0, 
                                "builder_init": 0, "microdata_adding": 0,
                                "total": 0 }
        
        self._excluded_urls = [
            "https://www.purchasedirect.com/"
        ]


    # -------------------------------------------------------------------------
    # Method(s)
    # -------------------------------------------------------------------------

    def recalculate_graph(self, query_pivot, web_result):
        try:
            start_time_1 = time.time()
            # print('----- recalculate_graph (init + update graph)')
            self.graph = ConjunctiveGraph() 
            self.update_graph(query_pivot, web_result)
              
            self.processing_time["total"] = time.time() - start_time_1
            return self.graph, self.processing_time

        except Exception as e:
            raise RuntimeError(f"metahub.GraphUpdater.recalculate_graph >> Error updating graph: {e}")
            

    def update_graph(self, query_pivot, web_result):
        try:
            start_time_1 = time.time()
            self.logger.debug("\n ***** Web Microdata Graph Updating ***** \n")
            
            # print("\n--- Extract URL list")
            # print('----- web_result: ', web_result)
            # print('----- query_pivot: ', query_pivot)
            url_list = self._extract_urls(query_pivot, web_result)
            
            # print('----- url_list: ', url_list)  
            # print('----- url_list length: ', len(url_list))  
            # print("\n--- Update Graph from URL microdata")
            # for (entity_list, url) in url_list:
            #     self._update_graph_from_url_metadata(query_pivot, entity_list, url)
            
            for entity_list, url in [(entity_list, url) for entity_list, url in url_list if url]:
                self._update_graph_from_url_metadata(query_pivot, entity_list, url)

            # print("\n--- Finalize graph updating")
            # marker = GraphMarker(self.graph, url_list)
            # self.graph = marker.mark_graph()
            self.graph.serialize(destination=GraphLoader.DYNAMIC_MICRODATA_GRAPH_PATH, format='turtle')
            
            self.processing_time["total"] = time.time() - start_time_1
            return self.graph, self.processing_time

        except Exception as e:
            raise RuntimeError(f"metahub.GraphUpdater.update_graph >> Error updating graph: {e}")
            

    def _extract_urls(self, query_pivot, web_result):
        url_key = query_pivot.web_pivot_variable
        entity_keys = query_pivot.web_target_entity_variable_list
        url_list = []
        
        if not web_result["rows"]:  # Checks whether the list is empty
            self.logger.debug("web_result['rows'] is empty, skipping key check.")
        else:
            if url_key not in web_result["rows"][0].keys():  # Checks whether the key is present
                raise ValueError(f"No consistent ‘webpage’ key found in web_result ({url_key}).")

        # key = possible_keys[0]
        # print('----- extract URLs using url_key: ', url_key)
        for row in web_result["rows"]:
            if url_key in row and "value" in row[url_key]:
                url = row[url_key]["value"]
                if isinstance(url, URIRef):
                    url = str(url)
                entity_list = self._extract_entity_list_from_row(entity_keys, row)
                entry = (entity_list, url)
                url_list.append(entry)
            else:
                raise ValueError(f"No 'value' found for identifier '{url_key}'.")
        url_list = [s for s in url_list if s] # filter empty strings

        return url_list

    def _extract_entity_list_from_row(self, entity_keys, row):
        entity_list = []
        for entity_key in entity_keys:
            entity_key_str = str(entity_key)
            if entity_key_str in row and "value" in row[entity_key_str]:                
                entity = row[entity_key_str]["value"]
                entity_list.append(entity)
        return entity_list


    def _update_graph_from_url_metadata(self, query_pivot, entity_list, url):
        try:
            start_time_1 = time.time()
            microdata = self._extract_metadata(url)
            self.microdata_count += 1 if microdata else 0
            self.processing_time["extraction"] += time.time() - start_time_1
            
            start_time_2 = time.time()
            self._build_microdata_graph(query_pivot, entity_list, url, microdata)
            self.processing_time["building"] += time.time() - start_time_2
            
            self.processing_stats["success_count"] += 1
            self.processing_stats["successful_urls"].append(url)

        except Exception as e:
            self.processing_stats["failure_count"] += 1
            self.processing_stats["failed_urls"].append({"url": url, "error": str(e)})
            # print(f'----- Exception while updating graph ({str(e)})')


    def _extract_metadata(self, url):
        try:
            if self._is_excluded_url(url):
                self.logger.info(f"URL excluded for the microdata extraction task: {url}")
                return None
            
            extractor = self.web_extractor_class
            microdata = extractor.get_microdata_by_url(url)
            return microdata
        
        except Exception as e:
            raise RuntimeError(f"Error extracting metadata for URL {url}: {e}")
            
                     
    def _is_excluded_url(self, url):
        """Checks whether the URL is on the exclusion list."""
        return any(url.startswith(excluded) for excluded in self._excluded_urls)


    def _build_microdata_graph(self, query_pivot, entity_list, url, microdata):
        try:
            start_time_1 = time.time()
            builder = GraphBuilder()
            self.processing_time["builder_init"] += (time.time() - start_time_1)
            
            builder.add_url(url)
            if microdata:
                start_time_1 = time.time()
                builder.add_json_microdata(url, microdata)
                self.processing_time["microdata_adding"] += (time.time() - start_time_1)
            builder.add_contains_thing(url, entity_list)
            builder.add_contains_word(url, query_pivot.web_target_keyword_list)
            
            # refiner = GraphRefiner(builder.get_graph())
            # refiner.adapt_graph()
            
            self.graph += builder.get_graph()
            
        except Exception as e:
            raise RuntimeError(f"Error creating the microdata graph for URL {url}: {e}")