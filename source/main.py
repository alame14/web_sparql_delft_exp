import logging
import os

from query_processor import QueryProcessor
from web_service.services import WebService
from metahub.extractors import WebExtractor



# =============================================================================
#  Main Script
# =============================================================================

def process_query_files(input_folder, output_folder, 
                        input_base_name, start_num, end_num,
                        log_level=logging.INFO, # logging.INFO / logging.DEBUG
                        exec_mode='cold', # cold, hot
                        web_service = WebService.BFP_SWSS, # BFP_CWTS, BFP_SWSS, DDG_WSS
                        web_extractor = WebExtractor.BFP_CWTME # BFP_CWTME, W3_ME
                        ):
    """
    Process JSON query files from input_folder and save results to output_folder.

    Args:
        input_folder (str): Path to the folder containing input JSON files.
        output_folder (str): Path to the folder where output files will be saved.
        input_base_name (str): Base name of the input files (e.g., 'bfp_queries').
        start_num (int): Starting number of the files to process.
        end_num (int): Ending number of the files to process (inclusive).

    Returns:
        None
    """
        
    kg_spec_path = 'data/kg_specification.json'
    processor = QueryProcessor(kg_spec_path, 
                               log_level=log_level, exec_mode = exec_mode, 
                               web_service=web_service, web_extractor=web_extractor     
                               )  
    
    os.makedirs(output_folder, exist_ok=True)  # Create the output folder if it doesn't exist

    for i in range(start_num, end_num + 1):
        input_data = os.path.join(input_folder, f'{input_base_name}_{i}.json')
        output_data = os.path.join(output_folder, f'{input_base_name}_result_{i}.json')

        try:
            if not os.path.exists(input_data):
                print(f"Skipping: {input_data} (file not found)")
                continue
            
            print(f"Processing: {input_data} -> {output_data}")
            processor.evaluate_queries_from_json(input_data, output_data)

        except Exception as e:
            print(f"Error processing file {input_data}: {e}")



def process_single_query_file(input_file, output_file,
                              log_level=logging.INFO, # logging.INFO / logging.DEBUG
                              exec_mode='cold', # cold, hot
                              web_service = WebService.BFP_SWSS, # BFP_CWTS, BFP_SWSS, DDG_WSS
                              web_extractor = WebExtractor.BFP_CWTME # BFP_CWTME, W3_ME
                              ):
    """
    Process a single JSON query file and save the result.

    Args:
        input_file (str): Path to the input JSON file.
        output_file (str): Path to the output file where the result will be saved.

    Returns:
        None
    """
    try:
        
        kg_spec_path = 'data/kg_specification.json'
        processor = QueryProcessor(kg_spec_path, 
                                   log_level=log_level, exec_mode = exec_mode, 
                                   web_service=web_service, web_extractor=web_extractor     
                                   )  
        
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found")
            return

        # Ensure output folder exists
        output_folder = os.path.dirname(output_file)
        os.makedirs(output_folder, exist_ok=True)

        print(f"Processing: {input_file} -> {output_file}")
        processor.evaluate_queries_from_json(input_file, output_file)

    except Exception as e:
        print(f"Error processing file {input_file}: {e}")



if __name__ == '__main__':
    log_level=logging.INFO # logging.INFO / logging.DEBUG
    exec_mode='cold' # cold, hot
    web_service = WebService.BFP_SWSS # BFP_CWTS, BFP_SWSS, DDG_WSS
    web_extractor = WebExtractor.BFP_CWTME # BFP_CWTME, W3_ME
    
    input_folder = 'working_files/dev_queries'
    output_folder = os.path.join(input_folder, 'results')


    # -- Process a specific file
    
    specific_input_file = os.path.join(input_folder, 'wsq_4.json')
    specific_output_file = os.path.join(output_folder, 'dev_result.json')
    
    # specific_input_file = os.path.join(input_folder, 'calibrate_data.json')
    # specific_output_file = os.path.join(output_folder, 'calibrate_data_result.json')
        
    # specific_input_file = os.path.join(input_folder, 'bfp_loading_queries.json')
    # specific_output_file = os.path.join(output_folder, 'bfp_loading_queries_result.json')
    
    # specific_input_file = os.path.join(input_folder, 'bfp_tech_query_set_publisher.json')
    # specific_output_file = os.path.join(output_folder, 'bfp_tech_query_set_publisher_result.json')
    
    process_single_query_file(specific_input_file, specific_output_file,
                              exec_mode = exec_mode, 
                              web_service=web_service, web_extractor=web_extractor   
                              )


    # -- Process multiple files
    
    # main_folder = f'{input_folder}/main_query_set'
    # input_base_name = 'bfp_query'
    # process_query_files(main_folder, output_folder, 
    #                     input_base_name, start_num=603, end_num=603,
    #                     log_level=log_level, exec_mode = exec_mode, 
    #                     web_service=web_service, web_extractor=web_extractor                       
    #                     )
