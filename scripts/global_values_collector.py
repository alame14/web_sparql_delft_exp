import json
import os
import logging
from query_keys import QueryKeys


class GlobalValuesCollector:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()
        self.data = {}


    def process(self, input_path, output_file):
        self.load_data(input_path)
        
        values_from_queries = self.collect_values_from_all_queries()
        element_counts = self._count_elements(values_from_queries)
        
        output_data = {
            "element_counts": element_counts,
            "values_from_queries": values_from_queries
        }
        
        self._save_output(output_data, output_file)
        self.logger.info(f"Values file saved to {output_file}")


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


    def collect_values_from_all_queries(self):
        total_values = {key.stats_key: set() for key in QueryKeys}
    
        for query in self.data.get("queries", []):
            rows = self._get_rows(query)
            obtained_data = query.get("obtained_data_query_result")
    
            if not self._is_valid_query(obtained_data):
                continue

            for key in QueryKeys:
                stats_key = key.stats_key
                query_key = key.query_key
                total_values[stats_key].update(
                    row.get(query_key, {}).get("value") for row in rows if query_key in row
                )

        return {key: list(values) for key, values in total_values.items()}

    def _get_rows(self, query, data_ref='obtained_data_query_result'):
        obtained_data_query_result = query.get(data_ref, {})
        rows = obtained_data_query_result.get('rows', []) if isinstance(obtained_data_query_result, dict) else []
        return rows
    
    def _is_valid_query(self, obtained_data):
        return obtained_data is not None and obtained_data != [] and obtained_data != {}


    def _count_elements(self, unique_values):
        """Count the number of unique elements for each key."""
        return {key: len(values) for key, values in unique_values.items()}