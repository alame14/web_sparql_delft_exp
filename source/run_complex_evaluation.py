import logging
import os

from main import process_query_files # process_single_query_file
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

author_index = {
    "Lewis Carroll": ["100", "101", "102", "103"],
    "Antoine de Saint-Exupéry": ["200", "201", "202", "203"],
    "Arthur Conan Doyle": ["300", "301", "302", "303", "304", "305"],
    "Maurice Leblanc": ["400", "401", "402", "403"],
    "Umberto Eco": ["500", "501", "502", "503", "504", "505"],
    "Terry Pratchett": ["600", "601", "602", "603", "604", "605"],
    "Victor Hugo": ["700", "701", "702", "703", "704"],
    "Alexandre Dumas": ["800", "801", "802", "803", "804", "805"],
    "Frank Herbert": ["900", "901", "902", "903", "904", "905"],
    "J. R. R. Tolkien": ["1000", "1001", "1002", "1003"]
}



# =============================================================================
#  Main Script
# =============================================================================


if __name__ == '__main__':    
    
    # -- Process multiple files from a given folder
    
    process_query_files(main_folder, output_folder, 
                        input_base_name, start_num=800, end_num=1003,
                        log_level=log_level, exec_mode = exec_mode, 
                        web_service=web_service, web_extractor=web_extractor                       
                        )
