import json
import logging
from time import time
import xml.etree.ElementTree as ET
import os

from endpoint_manager import EndpointManager
from sparql_manager import SPARQLManager
from web_service.services import WebService
from metahub.extractors import WebExtractor


# =============================================================================
#  QueryProcessor Class
# =============================================================================

class QueryProcessor:
    
    def __init__(self, kg_spec_path, 
                 log_level=logging.INFO, 
                 exec_mode='cold',
                 web_service = WebService.BFP_SWSS, # BFP_CWTS, BFP_SWSS, DDG_WSS
                 web_extractor = WebExtractor.BFP_CWTME # BFP_CWTME, W3_ME
                 ):
        
        self.logger = self._config_logging(log_level)
        self.endpoint_manager = EndpointManager(kg_spec_path, logger=self.logger)
        self.web_service = web_service
        self.web_extractor = web_extractor
        self.exec_mode = exec_mode
        self.WEB_QUERY_MAX = None
        self.sparql_manager = None
        self.microdata_change_flag = False
    
    def _config_logging(self, log_level):
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)
        
        # Make sure not to add several handlers
        if not logger.hasHandlers():
            ch = logging.StreamHandler()
            ch.setLevel(log_level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)
        
        return logger


    # -------------------------------------------------------------------------
    # Initialization Methods
    # -------------------------------------------------------------------------

    def initialize_sparql_manager(self, query):
        self.sparql_manager = SPARQLManager(query, self.endpoint_manager, self.web_service, self.web_extractor,
                                            web_query_max=self.WEB_QUERY_MAX, 
                                            exec_mode=self.exec_mode,
                                            logger=self.logger)
        
    
    
    # -------------------------------------------------------------------------
    # Loading/saving methods
    # -------------------------------------------------------------------------

    def load_data(self, data_file_path):
        try:
            with open(data_file_path, 'r') as f:
                self.data = json.load(f)
                self.logger.debug(f"Data from file {data_file_path} loaded successfully.")
        except FileNotFoundError:
            self.logger.error(f"Data file {data_file_path} not found.")
            raise
        except json.JSONDecodeError:
            self.logger.error(f"JSON decode error in data file {data_file_path}.")
            raise
            
    def save_data(self, data, output_file):
        try:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=4)
                self.logger.debug(f"Data saved successfully to file {output_file}.")
        except IOError as e:
            self.logger.error(f"Error writing to file {output_file}: {e}")
            raise
            
    def save_data_if_debug(self, data, output_file):
        if self.logger.getEffectiveLevel() == logging.DEBUG:
            try:
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=4)
                    self.logger.debug(f"Data saved successfully to file {output_file}.")
            except IOError as e:
                self.logger.error(f"Error writing to file {output_file}: {e}")
                raise

    def _get_step_output_filename(self, base_filename, step):
        base, ext = os.path.splitext(base_filename)
        return f"{base}_kw{step}{ext}"

    def _get_error_output_filename(self, base_filename):
        base, ext = os.path.splitext(base_filename)
        return f"{base}_error{ext}"
    
    def log_and_save_error_queries(self, error_queries, output_file):
        if error_queries:
            error_file = self._get_error_output_filename(output_file)
            error_query_ids = [query['query_id'] for query in error_queries]
            self.logger.error(f"Queries with errors: {error_query_ids}")
    
            with open(error_file, 'w') as f:
                json.dump({'queries': error_queries}, f, indent=4)
            self.logger.debug(f"Error queries saved to {error_file}")




    # -------------------------------------------------------------------------
    # Evaluation Functions
    # -------------------------------------------------------------------------

    def evaluate_queries_from_json(self, input_file, output_file):
        self.logger.info("*** Main Processing Run (Query Evaluation from JSON) ***")
        self.logger.debug("=== Debug Log ===")
        self.logger.debug(f"input_file: {input_file}")
        self.logger.debug(f"output_file: {output_file}")
        self.logger.debug(f"exec_mode: {self.exec_mode}")
        
        start_time = time()
        self.logger.info("Process started")
        
        self.load_data(input_file)
        self.save_data_if_debug(self.data, self._get_step_output_filename(output_file, 0))
        self.logger.debug("Input Data file loaded (step 0)")
        
        total_queries, non_empty_queries, error_count, error_queries = self.process_queries()
        self.save_data_if_debug(self.data, self._get_step_output_filename(output_file, 1))
        self.logger.info("All queries processed (step 1)")
            
        # Adding the process configuration to the head
        process_config = {
            "web_service": str(self.web_service),
            "web_extractor": str(self.web_extractor),
            "exec_mode": self.exec_mode,
            "WEB_QUERY_MAX": self.WEB_QUERY_MAX
        }
        
        if 'head' not in self.data:
            self.data['head'] = {}
        
        
        elapsed_time = time() - start_time
        self.data['head']['process_config'] = process_config
        self.data['head']['processing_total_time'] = elapsed_time
        
        with open(output_file, 'w') as f:
            json.dump(self.data, f, indent=4)
        self.logger.info(f"Evaluation results saved to {output_file}")
        
        self.log_and_save_error_queries(error_queries, output_file)
        
        self.logger.info(f"Process completed in {elapsed_time:.2f} seconds")



    
    def process_queries(self):
        total_queries = len(self.data['queries'])
        non_empty_queries = 0
        error_count = 0
        error_queries = []
        
        for query in self.data['queries']:
            self.logger.info(f"Evaluating query ID {query['query_id']}")
            try:
                result = self.evaluate_query(query['hybrid_query'])
                self.update_query_with_results(query, result)
                # f_score_details = self.calculate_f_score(query['expected_data_query_result'], query['obtained_data_query_result'])
                # self.update_query_with_f_score(query, f_score_details)
                # if result['statistics']['num_results'] > 0:
                #     non_empty_queries += 1
            except Exception as e:
                error_count += 1
                query['obtained_data_query_result'] = []
                query['evaluation_time'] = 0
                query['processing_times'] = {}
                query['execution_times'] = {}
                query['deep_times'] = None
                query['evaluation_error_list'] = str(e)
                error_queries.append(query)
        
        return total_queries, non_empty_queries, error_count, error_queries


    
    
    def update_query_with_results(self, query, result):
        query['obtained_data_query_result'] = self.convert_response_to_json(result['response'].text)
        query['execution_mode'] = result['execution_mode']
        query['result_stats'] = result['result_stats']
        query['evaluation_time'] = result['elapsed_time']
        query['processing_times'] = result['processing_times']
        query['deep_times'] = result['deep_times']
        query['result_stats'] = result['result_stats']
    
    
    def evaluate_query(self, query):
        start_time = time()
        
        self.initialize_sparql_manager(query)
        self.sparql_manager.sparql_query = query
        response = self.sparql_manager.perform_hybrid_evaluation()
        
        elapsed_time = time() - start_time
        self.microdata_change_flag = True
        
        self.logger.info(f"Query evaluation completed in {elapsed_time:.2f} seconds.")
                        
        return {
            'response': response,
            'execution_mode': self.sparql_manager.execution_mode,
            'result_stats': self.sparql_manager.result_stats,
            'elapsed_time': elapsed_time,
            'processing_times': self.sparql_manager.processing_times,
            'deep_times': self.sparql_manager.deep_times
        }


    # -------------------------------------------------------------------------
    # Result Handler Method(s)
    # -------------------------------------------------------------------------

    def convert_response_to_json(self, response):
        root = ET.fromstring(response)
        columns = [variable.get('name') for variable in root.findall('.//{http://www.w3.org/2005/sparql-results#}variable')]
        rows = []
        for result in root.findall('.//{http://www.w3.org/2005/sparql-results#}result'):
            row = {}
            for binding in result.findall('{http://www.w3.org/2005/sparql-results#}binding'):
                name = binding.get('name')
                value_element = binding[0]
                value_type = value_element.tag.split('}')[-1]
                value = value_element.text
                datatype = value_element.get('datatype') if value_type == 'literal' else None
                row[name] = {
                    'type': value_type,
                    'value': value
                }
                if datatype:
                    row[name]['datatype'] = datatype
            rows.append(row)
        return {
            'columns': columns,
            'rows': rows
        }