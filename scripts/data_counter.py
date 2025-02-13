import re
import os
import json
import logging
from query_keys import QueryKeys

class DataCounter:

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
 
    def __init__(self):
        self.data = {}
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()


    # -------------------------------------------------------------------------
    # Loading/saving methods
    # -------------------------------------------------------------------------
      
    def load_data(self, input_path):
        try:
            if os.path.isfile(input_path):
                with open(input_path, 'r') as f:
                    self.data = json.load(f)
            elif os.path.isdir(input_path):
                self.data["queries"] = []
                for file_name in os.listdir(input_path):
                    if file_name.endswith('.json'):
                        with open(os.path.join(input_path, file_name), 'r') as f:
                            file_data = json.load(f)
                            if "queries" in file_data:
                                self.data["queries"].extend(file_data["queries"])
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise


    def _save_output(self, output_data, output_file):
        try:
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=4)
        except IOError as e:
            self.logger.error(f"Error saving output: {e}")
            raise

        
    # -------------------------------------------------------------------------
    # Processing Methods
    # -------------------------------------------------------------------------

    def process(self, input_path, output_file):
        self.load_data(input_path)
        query_stats = self.count_elements_per_query()
        query_stats.sort(key=lambda x: x.get("query_id", 0))
        output_data = {"query_details": query_stats}
        self._save_output(output_data, output_file)
        self.logger.info(f"Details file saved to {output_file}")
        return query_stats


    def count_elements_per_query(self):
        query_stats = []
        for query in self.data.get("queries", []):
            query_id = query.get("query_id")
            stats = {"query_id": query_id}
            stats["selected_elements"] = self._extract_selected_elements(query.get("hybrid_query", ""))
            result_stats = query.get("result_stats", {})
            rows = query.get("obtained_data_query_result", {}).get("rows", [])
            
            for key in QueryKeys:
                if key.stats_key and key.stats_key in result_stats:
                    stats[key.result_key] = result_stats[key.stats_key]
                else:
                    if key.is_feature:
                        stats[key.result_key] = len([row for row in rows if key.query_key in row])
                    else:
                        stats[key.result_key] = len({row.get(key.query_key, {}).get("value") for row in rows if key.query_key in row})    
            
            query_stats.append(stats)
        return query_stats


    def _extract_selected_elements(self, query):
        match = re.search(r"SELECT\s+DISTINCT\s+(.+?)\s+WHERE", query, re.DOTALL | re.IGNORECASE)
        if match:
            elements = match.group(1)
            elements = re.split(r"[\s,\n]+", elements)
            return [elem.strip() for elem in elements if elem.startswith("?")]
        return []
