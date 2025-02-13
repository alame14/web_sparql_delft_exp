import time
from rdflib import ConjunctiveGraph

from metahub.extractors import WebExtractor
from metahub.w3_metadata_extractor import W3MetadataExtractor
from metahub.controlled_web_metadata_extractor import ControlledWebMetadataExtractor

from metahub.graph_loader import GraphLoader
from metahub.graph_updater import GraphUpdater
from metahub.graph_evaluator import QueryEvaluator
from metahub.microdata_property_accessor import MicrodataPropertyAccessor


# =============================================================================
#  Processor: control metadata analysis
# =============================================================================

class WebMicrodataHandler:

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, web_extractor, logger=None, exec_mode=None):
        self.logger = logger
        self.microdata_graph = ConjunctiveGraph()
        self.web_extractor = web_extractor
        self.web_extractor_class = self._init_web_extractor_class(web_extractor)
        self.processing_stats = self._init_stat_dict()
        self.microdata_count = 0
        self.graph_loader = GraphLoader(self.microdata_graph)
        if exec_mode != 'hot':
            self.graph_loader.init_graph()
        self.microdata_property_accessor = MicrodataPropertyAccessor(GraphLoader.DYNAMIC_MICRODATA_GRAPH_PATH)


    def _init_stat_dict(self):
        stat_dict = { "success_count": 0, "failure_count": 0, 
                     "successful_urls": [], "failed_urls": [] }
        return stat_dict
        
        
    def _init_web_extractor_class(self, web_extractor):
        web_extractor_class = None
        if self.web_extractor == WebExtractor.W3_ME:
            web_extractor_class = W3MetadataExtractor(logger=self.logger)
        elif self.web_extractor == WebExtractor.BFP_CWTME:  
            web_extractor_class = ControlledWebMetadataExtractor(self.web_extractor.data_path, logger=self.logger)
        else:    
            raise Exception(f'web_extractor unknown: {self.web_extractor}')
        self.logger.debug(f"web_extractor_class: {web_extractor_class.__class__.__name__}")
        return web_extractor_class


    # -------------------------------------------------------------------------
    # Accessor(s)
    # -------------------------------------------------------------------------

    def get_processing_stats(self):
        return self.processing_stats    
    
    def get_property_keys(self, subject=None):
        microdata_property_accessor = MicrodataPropertyAccessor(GraphLoader.DYNAMIC_MICRODATA_GRAPH_PATH)
        return microdata_property_accessor.get_property_keys(subject)
    
    def get_property_uri(self, key, subject=None):
        microdata_property_accessor = MicrodataPropertyAccessor(GraphLoader.DYNAMIC_MICRODATA_GRAPH_PATH)
        return microdata_property_accessor.get_property_uri(key, subject)
    

    # -------------------------------------------------------------------------
    # Handle Method(s)
    # -------------------------------------------------------------------------

    def load_graph(self):
        self.graph_loader.load_graph()
        microdata_property_accessor = MicrodataPropertyAccessor(GraphLoader.DYNAMIC_MICRODATA_GRAPH_PATH)
        microdata_property_accessor.update_properties()    
        

    def recalculate_graph(self, query_pivot, web_result):
        start_time = time.time()
        execution_times = { "updater_init": -1, "graph_computing": -1,
                         "property_access_init": -1, "properties_update": -1,
                         "total": -1}
        
        start_time_1 = time.time() 
        graph_updater = GraphUpdater(self.microdata_graph, self.web_extractor_class, 
                                     self.processing_stats, logger=self.logger)
        execution_times["updater_init"] = time.time() - start_time_1
        
        self.microdata_graph, updating_time = graph_updater.recalculate_graph(query_pivot, web_result)
        self.microdata_count = graph_updater.microdata_count
        execution_times["graph_computing"] = updating_time
        
        start_time_3 = time.time()
        microdata_property_accessor = MicrodataPropertyAccessor(GraphLoader.DYNAMIC_MICRODATA_GRAPH_PATH)
        execution_times["property_access_init"] = time.time() - start_time_3
        
        start_time_4 = time.time()
        microdata_property_accessor.update_properties()   
        execution_times["properties_update"] = time.time() - start_time_4   
        
        self.logger.debug(f"Recalculate Graph Execution Time: {execution_times}")
        
        execution_times["total"] = time.time() - start_time
        return execution_times
        

    def update_graph(self, web_result):
        graph_updater = GraphUpdater(self.microdata_graph, self.web_extractor_class, self.processing_stats)
        self.microdata_graph = graph_updater.update_graph(web_result)
        microdata_property_accessor = MicrodataPropertyAccessor(GraphLoader.DYNAMIC_MICRODATA_GRAPH_PATH)
        microdata_property_accessor.update_properties()        

    def evaluate_query(self, query, format_result=True):
        query_evaluator = QueryEvaluator(self.microdata_graph)
        return query_evaluator.evaluate_query(query, format_result)

