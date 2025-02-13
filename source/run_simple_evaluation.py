import logging
import os

from main import process_single_query_file # process_query_files
from web_service.services import WebService
from metahub.extractors import WebExtractor


# =============================================================================
#  Settings
# =============================================================================

log_level=logging.INFO # logging.INFO / logging.DEBUG

exec_mode = 'cold' # cold, hot

web_service = WebService.BFP_SWSS # BFP_CWTS, BFP_SWSS, DDG_WSS
web_extractor = WebExtractor.BFP_CWTME # BFP_CWTME, W3_ME


input_folder = 'working_files'
output_folder = os.path.join(input_folder, 'results')
main_folder = f'{input_folder}/dataset/complex_queries'
input_base_name = 'bfp_query'



# =============================================================================
#  Main Script
# =============================================================================


if __name__ == '__main__':

    # -- Process specific files
        
    specific_input_file = os.path.join(input_folder, 'dataset/simple_queries/bfp_book_price.json')
    specific_output_file = os.path.join(output_folder, 'bfp_query_book_result.json')
    process_single_query_file(specific_input_file, specific_output_file,
                              exec_mode = exec_mode, 
                              web_service=web_service, web_extractor=web_extractor   
                              )
        
    specific_input_file = os.path.join(input_folder, 'dataset/simple_queries/bfp_query_price.json')
    specific_output_file = os.path.join(output_folder, 'bfp_query_price_result.json')
    process_single_query_file(specific_input_file, specific_output_file,
                              exec_mode = exec_mode, 
                              web_service=web_service, web_extractor=web_extractor   
                              )
    
    specific_input_file = os.path.join(input_folder, 'dataset/simple_queries/bfp_query_availability.json')
    specific_output_file = os.path.join(output_folder, 'bfp_query_availability_result.json')
    process_single_query_file(specific_input_file, specific_output_file,
                              exec_mode = exec_mode, 
                              web_service=web_service, web_extractor=web_extractor   
                              )
        
    specific_input_file = os.path.join(input_folder, 'dataset/simple_queries/bfp_query_publisher.json')
    specific_output_file = os.path.join(output_folder, 'bfp_query_publisher_result.json')
    process_single_query_file(specific_input_file, specific_output_file,
                              exec_mode = exec_mode, 
                              web_service=web_service, web_extractor=web_extractor   
                              )
