import json
import logging
import os


# =============================================================================
# TimesAnalyzer Class
# =============================================================================

class TimesAnalyzer:

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    def __init__(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger()

    # -------------------------------------------------------------------------
    # Main Processing Method
    # -------------------------------------------------------------------------
    def process_folder(self, folder_path, result_file):
        self.logger.info(f"Processing all JSON files in folder: {folder_path}")
        
        aggregated_data = {
            "total_queries": 0,
            "source_folder": folder_path,
            "source_files": [],
            "data_source": None,
            "pivot_variable": None,
            "web_keyword": None,
            "process_config": None,
            "processing_total_time": 0.0,
            "empty_query_count": 0,
            "non_empty_query_count": 0,
            "all_queries_evaluation_total": 0.0,
            "all_queries_evaluation_avg": 0.0,
            "all_queries_processing_times_total": {},
            "all_queries_processing_times_avg": {},
        }

        total_files = 0
        all_queries = 0
        all_totals = {}
        non_empty_queries = 0

        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(folder_path, filename)
                self.logger.info(f"Processing file: {file_path}")
                
                total_files += 1
                aggregated_data["source_files"].append(filename)

                # Process the file
                head, processing_times, evaluation_total, evaluation_avg, empty_count, non_empty_count = self._process_file(file_path)
                
                # Aggregate data
                all_queries += empty_count + non_empty_count
                non_empty_queries += non_empty_count
                aggregated_data["empty_query_count"] += empty_count
                aggregated_data["non_empty_query_count"] += non_empty_count
                aggregated_data["processing_total_time"] += head.get("processing_total_time", 0.0)
                aggregated_data["data_source"] = head.get("data_source")
                aggregated_data["pivot_variable"] = head.get("pivot_variable")
                aggregated_data["web_keyword"] = head.get("web_keyword")
                aggregated_data["process_config"] = head.get("process_config")

                # Aggregate execution times
                if not all_totals:
                    all_totals = processing_times
                else:
                    self._sum_nested_dictionaries(all_totals, processing_times)

        # Calculate averages
        aggregated_data["total_queries"] = all_queries
        aggregated_data["all_queries_evaluation_total"] = aggregated_data["processing_total_time"]
        aggregated_data["all_queries_processing_times_total"] = all_totals
        aggregated_data["all_queries_processing_times_avg"] = self._calculate_average_processing_times(all_totals, non_empty_queries)

        # Save result file
        self.save_data(result_file, aggregated_data)
        self.logger.info(f"Result file saved: {result_file}")


    # -------------------------------------------------------------------------
    # File Processing Method
    # -------------------------------------------------------------------------
    
    def _process_file(self, file_path):
        """Processes a single JSON file."""
        with open(file_path, "r") as f:
            data = json.load(f)
    
        head = data.get("head", {})
        queries = data.get("queries", [])
    
        empty_query_count = 0
        non_empty_query_count = 0
        total_evaluation_time = 0.0
    
        processing_times_total = {}
    
        for query in queries:
            obtained_data = query.get("obtained_data_query_result", {})
            if not obtained_data or not obtained_data.get("rows"):
                empty_query_count += 1
            else:
                non_empty_query_count += 1
                total_evaluation_time += max(query.get("evaluation_time", 0.0), 0.0)
                processing_times = query.get("processing_times", {})
    
                # Initialize processing_times_total with sanitized values
                if not processing_times_total:
                    processing_times_total = self._sanitize_initial_times(processing_times)
                else:
                    self._sum_nested_dictionaries(processing_times_total, processing_times)
    
        evaluation_avg = total_evaluation_time / non_empty_query_count if non_empty_query_count > 0 else 0.0
    
        return head, processing_times_total, total_evaluation_time, evaluation_avg, empty_query_count, non_empty_query_count



    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    def save_data(self, output_file, data):
        """Saves the aggregated data to a file."""
        try:
            with open(output_file, "w") as f:
                json.dump(data, f, indent=4)
                self.logger.info(f"Data saved successfully to file {output_file}.")
        except IOError as e:
            self.logger.error(f"Error saving file {output_file}: {e}")
            raise


    def _sanitize_initial_times(self, times):
        """
        Ensures all values in the given dictionary (including nested ones)
        are non-negative. Negative values are replaced with 0.
        """
        sanitized = {}
        for key, value in times.items():
            if isinstance(value, (int, float)):
                sanitized[key] = max(value, 0)  # Replace negative values with 0
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_initial_times(value)  # Recursive sanitization for nested dictionaries
            else:
                sanitized[key] = value  # Preserve non-numeric entries (if any, though unlikely)
        return sanitized


    def _sum_nested_dictionaries(self, target, source):
        """
        Recursively sums values from `source` into `target`.
        Ignores non-numeric values and negative values.
        Ensures no negative values remain in `target` after summation.
        """
        for key, value in source.items():
            if isinstance(value, (int, float)):
                # Sum values and ensure target[key] is non-negative
                current_target_value = max(target.get(key, 0), 0)
                target[key] = max(current_target_value + max(value, 0), 0)
            elif isinstance(value, dict):
                # Ensure target[key] is a dictionary before descending
                target[key] = target.get(key, {})
                if isinstance(target[key], dict):
                    self._sum_nested_dictionaries(target[key], value)
    
        # Final cleanup: Ensure all values in target are non-negative
        for key, value in target.items():
            if isinstance(value, (int, float)):
                target[key] = max(value, 0)
            elif isinstance(value, dict):
                # Recursively clean nested dictionaries
                self._sum_nested_dictionaries(value, {})


    def _calculate_average_processing_times(self, totals, count):
        """Calculates the average execution times from totals."""
        averages = {}

        def calculate_average(source, target):
            for key, value in source.items():
                if isinstance(value, (int, float)):
                    target[key] = value / count if count > 0 else 0
                elif isinstance(value, dict):
                    target[key] = {}
                    calculate_average(value, target[key])

        calculate_average(totals, averages)
        return averages
