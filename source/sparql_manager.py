import time

import xml.etree.ElementTree as ET

from sparql_result_handler import SPARQLResultHandler

from sparql_analyzer.query_pivot import QueryPivot
from sparql_analyzer.query_splitter import QuerySplitter
from sparql_analyzer.query_adjuster import QueryAdjuster

from search_processor import SearchProcessor
from web_service.services import WebService

from web_microdata_handler import WebMicrodataHandler
from metahub.extractors import WebExtractor

from result_merger import ResultMerger


# =============================================================================
#  SPARQLManager: class for managing SPARQL queries
# =============================================================================

class SPARQLManager:
    
    
    def __init__(self, ):
        self.logger = None  # Exemple, si un logger est utilisé
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, sparql_query, 
                 kg_endpoint, 
                 web_service=WebService.BFP_CWTS,
                 web_extractor=WebExtractor.BFP_CWTME,
                 web_query_max=2,
                 exec_mode='cold', #cold, hot
                 result_null_handling="strict", # strict, relaxed
                 logger=None):
        
        self.logger = logger
        self._sparql_query = sparql_query
        self._kg_endpoint = kg_endpoint
        self.web_service = web_service
        self._web_query_max = web_query_max
        self.execution_mode=exec_mode
        self.result_null_handling = result_null_handling
        self._web_microdata_handler = WebMicrodataHandler(web_extractor, logger=self.logger, exec_mode=self.execution_mode)
        self.query_pivot = None
        self.select_clause = None
        self.kg_query = None
        self.web_query_pattern = None
        self.md_query = None
        self.kg_results = None
        self.web_results = None
        self.md_results = None
        self.md_stats = None
        self.result_stats = {}
        self.processing_times = {}
        self.deep_times = {}
            
    
    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------
        
    @property
    def sparql_query(self):
        return self._sparql_query

    @sparql_query.setter
    def sparql_query(self, value):
        self._sparql_query = value

    @property
    def kg_endpoint(self):
        return self._kg_endpoint

    @kg_endpoint.setter
    def kg_endpoint(self, value):
        self._kg_endpoint = value

    @property
    def service(self):
        return self._service

    @service.setter
    def service(self, value):
        self._service = value

    @property
    def web_microdata_handler(self):
        return self._web_microdata_handler

    @web_microdata_handler.setter
    def web_microdata_handler(self, value):
        self._web_microdata_handler = value


    # -------------------------------------------------------------------------
    # Main Method
    # -------------------------------------------------------------------------   
    
    def perform_hybrid_evaluation(self):
        try:
            if not self._sparql_query:
                return {"error": "No SPARQL query provided"}, 400
    
            self.processing_times = {}
    
            # Step 1: Query Decomposition
            split_start = time.time()
            self.split_query()
            split_time = time.time() - split_start
            self.processing_times["query_decomposition"] = split_time
    
            # Step 2: Static Query Evaluation
            kg_start = time.time()
            self.evaluate_static_query()
            kg_time = time.time() - kg_start
            self.processing_times["static_query_evakluation"] = kg_time
    
            # Step 3: Web Data Retrieval
            web_start = time.time()
            web_data_retrieval_time = self.retrieve_data_from_web()
            if self.execution_mode == 'hot':
                web_time = time.time() - web_start
            else:
                web_time = web_data_retrieval_time
            self.processing_times["web_data_retrieval"] = web_time
    
            # Step 4: Dynamic Query Evaluation
            md_start = time.time()
            self.evaluate_dynamic_query()
            md_time = time.time() - md_start
            self.processing_times["dynamic_query_evaluation"] = md_time
    
            # Step 5: Joining Results
            merge_start = time.time()
            response = self.get_merged_response()
            merge_time = time.time() - merge_start
            self.processing_times["result_merge"] = merge_time
    
            # Total time computed as sum of step times
            total_time = (
                split_time +
                kg_time +
                web_time +
                md_time +
                merge_time
            )
            self.processing_times["total"] = total_time
    
            return response
    
    
        except Exception as e:
            err_msg = f'SPARQLManager.perform_hybrid_evaluation >> {str(e)}'
            self.logger.error(err_msg)
            raise Exception(err_msg)

            
            
    def get_microdata_property_keys(self, subject=None):
        self.logger.debug("Microdata Property Key Access.")
        self.web_microdata_handler.load_graph()
        all_keys = self.web_microdata_handler.get_property_keys()
        result_keys = self.web_microdata_handler.get_property_keys(subject)
        return result_keys
    

    # -------------------------------------------------------------------------
    # Query Splitting
    # -------------------------------------------------------------------------
    
    def split_query(self):
        self.logger.debug("Query Splitting.")
        self.query_pivot = QueryPivot(query=self._sparql_query, logger=self.logger)
        splitter = QuerySplitter(self.query_pivot, empty_query_option="empty", logger=self.logger)
        self.select_clause = splitter.get_select_clause()
        self.kg_query = splitter.get_kg_query()
        self.web_query_pattern = splitter.get_web_query_pattern()
        self.md_query = splitter.get_web_microdata_query()
        self._adjust_microdata_query()
        
        
    def _adjust_microdata_query(self):
        self.logger.debug("-- adjust microdata query")
        self.web_microdata_handler.load_graph()
        prefix = "md"
        # all_property_of_table = self.web_microdata_handler.microdata_property_accessor.get_property_keys()
        # print('----- all_property_of_table: ', all_property_of_table)
        adjuster = QueryAdjuster(prefix, self.web_microdata_handler)
        self.md_query = adjuster.adjust_query(self.md_query)


    # -------------------------------------------------------------------------
    # Query Evaluation 
    # -------------------------------------------------------------------------

    def evaluate_static_query(self):
        try:
            self.logger.debug("KG Query Evaluation.")
            self.logger.debug("-- ask current endpoint for query KG part")
            # print('----- kg_query: ', self.kg_query)
            # print('----- mock response: standard')
            # self.kg_results = mock_response(None)
            endpoint_response = self._kg_endpoint.ask(self.kg_query)
            self.kg_results = endpoint_response.text
            self.result_stats['number_of_static_results'] = self.count_resp_sparL_results(self.kg_results)
        except Exception as e:
            err_msg = f'SPARQLManager.evaluate_static_query >> {str(e)}'
            self.logger.error(err_msg)
            raise Exception(err_msg)
            

    def retrieve_data_from_web(self):
        try:
            self.logger.debug("Web Data Retrieval.")
            rec_graph_exec_time = None
            microdata_extraction_time = 0
            microdata_storing_time = 0
                
            
            init_start = time.time()
            processor = SearchProcessor(self.web_query_pattern, self.web_service, logger=self.logger)            
            processor.generate_query_list(self.kg_results)
            init_time = time.time() - init_start
            
            processor.perform_searches(web_query_max=self._web_query_max)
            
            formatting_start = time.time()
            self.web_results = processor.format_results(self.query_pivot)
            self.result_stats['number_of_web_results'] = self.count_dict_sparL_results(self.web_results)
            all_property_of_table = self.web_microdata_handler.microdata_property_accessor.get_property_keys()
            formatting_time = time.time() - formatting_start
            
            web_query_eval_time = init_time + processor.search_total_time + formatting_time
            self.deep_times["web_query_evaluation"] = {
                "init": init_time, "searches": processor.search_total_time, "web_formatting": formatting_time,
                "total": web_query_eval_time
                }
            
            if self.execution_mode != 'hot':
                rec_graph_exec_time = self.web_microdata_handler.recalculate_graph(self.query_pivot, self.web_results)  
                self.result_stats['number_of_extracted_microdata'] = self.web_microdata_handler.microdata_count
                self.deep_times["web_microdata_graph_generation"] = rec_graph_exec_time
                microdata_extraction_time = rec_graph_exec_time['graph_computing']['extraction']
                microdata_storing_time = rec_graph_exec_time['graph_computing']['microdata_adding']
            
            update_graph_start = time.time()
            # self.web_microdata_handler.update_graph(self.web_results)
            self.deep_times["web_microdata_graph_update"] = time.time() - update_graph_start
               
            web_data_retrieval_time = web_query_eval_time + microdata_extraction_time + microdata_storing_time
            self.deep_times["web_data_retrieval"] = {
                "url_finding": web_query_eval_time,
                "microdata_extraction": microdata_extraction_time,
                "storing": microdata_storing_time,
                "total": web_data_retrieval_time,
                }
            
            return web_data_retrieval_time
            
        except Exception as e:
            err_msg = f'SPARQLManager.retrieve_data_from_web >> {str(e)}'
            self.logger.error(err_msg)
            raise Exception(err_msg)
            

    def evaluate_dynamic_query(self):
        try:
            start_time = time.time()
            self.logger.debug("Microdata Query Evaluation.")
            self.logger.debug(f'----- md_query: {self.md_query}')
            self.logger.debug(f'----- web_results: {self.web_results}')

            eval_query_start = time.time()
            self.md_results, error = self.web_microdata_handler.evaluate_query(self.md_query)
            # print(self.md_results)
            self.deep_times["microdata_query_evaluation"] = time.time() - eval_query_start
                
            stats_computing_start = time.time()
            self.md_stats = self.web_microdata_handler.get_processing_stats()
            self.deep_times["microdata_stats_computing"] = time.time() - stats_computing_start
            
            return error
        
        except Exception as e:
            err_msg = f'SPARQLManager.evaluate_dynamic_query >> {str(e)}'
            self.logger.error(err_msg)
            raise Exception(err_msg)
            

    def evaluate_query_on_microdata_graph(self, query):
        try:
            self.logger.debug(f"Query Evaluation on Microdata graph.")
            # processor = MicrodataProcessor()
            self.web_microdata_handler.load_graph()
            self.md_results, error = self.web_microdata_handler.evaluate_query(query)
            self.md_stats = self.web_microdata_handler.get_processing_stats()
            return error
        except Exception as e:
            err_msg = f'SPARQLManager.evaluate_query_on_microdata_graph >> {str(e)}'
            self.logger.error(err_msg)
            raise Exception(err_msg)


    # -------------------------------------------------------------------------
    # Result Stats
    # -------------------------------------------------------------------------
    
    def count_resp_sparL_results(self, xml_data: str) -> int:
        """
        Compte le nombre de résultats dans une réponse SPARQL XML.
        
        :param xml_data: Chaîne XML contenant les résultats SPARQL
        :return: Nombre de résultats ou 0 en cas d'erreur
        """
        try:
            root = ET.fromstring(xml_data)
            results = root.findall(".//{http://www.w3.org/2005/sparql-results#}result")
            return len(results)
        except ET.ParseError as e:
            self.logger.error(f"Erreur de parsing XML: {e}")
        except Exception as e:
            self.logger.error(f"Erreur inattendue: {e}")
        return 0


    def count_dict_sparL_results(self, sparql_data: dict) -> int:
        """
        Compte le nombre de résultats dans une réponse SPARQL sous forme de dictionnaire.
        
        :param sparql_data: Dictionnaire contenant les résultats SPARQL
        :return: Nombre de résultats ou 0 en cas d'erreur
        """
        try:
            if not isinstance(sparql_data, dict) or "rows" not in sparql_data:
                raise ValueError("Format de données invalide")
            return len(sparql_data["rows"])
        except Exception as e:
            self.logger.error(f"Erreur inattendue: {e}")
        return 0


    # -------------------------------------------------------------------------
    # Result Handle
    # -------------------------------------------------------------------------

    def get_union_response(self):  
        
        res1 = self.kg_results     
        if SPARQLResultHandler.is_valid_result_xml(res1):
            res1 = SPARQLResultHandler.convert_result_xml_to_dict(res1)
        if SPARQLResultHandler.is_valid_result_dict(res1):
            res1 = SPARQLResultHandler.convert_columns(res1)
            
        if self.md_results is None:
            result_rows = res1["rows"]
        else:  
            res2 = SPARQLResultHandler.convert_columns(self.md_results)  
            if res1["columns"] != res2["columns"]:
                raise ValueError("Columns in the two structures are not identical.")       
            result_rows = res1["rows"] + res2["rows"]  
            
        union_result_dict = { "columns": res1["columns"], "rows": result_rows }
        result_dict = SPARQLResultHandler.remove_null_values(union_result_dict)
                
        result_xml = SPARQLResultHandler.dict_to_sparql_xml(result_dict)
                
        response = SPARQLResultHandler.create_response_from_xml(result_xml)
        
        return response
    

    def get_merged_response(self):
        
        merged_result_dict = self.merge_result()
        
        if self.result_null_handling == "strict":
            result_dict = SPARQLResultHandler.remove_null_rows(merged_result_dict)
        elif self.result_null_handling == "relaxed":
            result_dict = SPARQLResultHandler.remove_null_values(merged_result_dict)
                   
        self.result_stats['number_of_query_results'] = self.count_dict_sparL_results(result_dict)
        result_xml = SPARQLResultHandler.dict_to_sparql_xml(result_dict)
                
        response = SPARQLResultHandler.create_response_from_xml(result_xml)
        
        return response


    def merge_result(self):
        self.logger.debug("Result Merging.")
        
        merger = ResultMerger()
        
        for res in [self.kg_results, self.md_results]:
            merger.add_result(res)
    
        merged_result = merger.merge_results(self.select_clause)
    
        return merged_result



