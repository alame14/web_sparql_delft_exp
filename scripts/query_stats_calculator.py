import json
import logging
from query_keys import QueryKeys


class QueryStatsCalculator:
    
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()


    def compute_stats(self, count_file, global_values_file, output_file):
        try:
            # Charger les fichiers nécessaires
            with open(count_file, 'r') as f:
                details_data = json.load(f)
            with open(global_values_file, 'r') as f:
                global_values_data = json.load(f)
    
            query_stats = details_data.get("query_details", [])
            element_counts = global_values_data.get("element_counts", {})
    
            # Calculer les statistiques globales
            average_per_query = self._compute_average_stats(query_stats)
            coverage_stats = self._compute_coverage_stats(query_stats)
            success_stats = self._compute_success_stats(query_stats)
            average_results_stats = self._compute_average_results_per_successful_query(query_stats)
    
            # Stats Output
            stats_output = {
                "total_queries": len(query_stats),
                "average_per_query": average_per_query,
                "total_elements_across_queries": element_counts,
                "coverage_stats": coverage_stats,
                "success_stats": success_stats,
                "average_results_per_successful_query": average_results_stats
            }
    
            # Sauvegarder le fichier final
            with open(output_file, 'w') as f:
                json.dump(stats_output, f, indent=4)
    
            self.logger.info(f"Final stats file saved to {output_file}")
        except Exception as e:
            self.logger.error(f"Error computing stats: {e}")
            raise


    def _compute_average_stats(self, query_stats):
        element_totals = {key.result_key: 0 for key in QueryKeys}
        element_counts = {key.result_key: 0 for key in QueryKeys}

        for stats in query_stats:
            for key in QueryKeys:
                result_key = key.result_key
                if result_key in stats:
                    element_totals[result_key] += stats[result_key]
                    element_counts[result_key] += 1

        return {
            f"average_{key.result_key}_per_query": round(
                element_totals[key.result_key] / element_counts[key.result_key], 2
            ) if element_counts[key.result_key] > 0 else None
            for key in QueryKeys
        }
    
    
    def _compute_coverage_stats(self, query_stats):
        total_queries = len(query_stats)
        coverage_counts = {key.result_key: 0 for key in QueryKeys}
    
        for stats in query_stats:
            for key in QueryKeys:
                if f"?{key.query_key}" in stats.get("selected_elements", []):
                    coverage_counts[key.result_key] += 1
    
        return {
            key.result_key: {
                "queries_with_feature": coverage_counts[key.result_key],
                "percentage_queries_with_feature": round(
                    (coverage_counts[key.result_key] / total_queries) * 100, 2
                ) if total_queries > 0 else 0
            }
            for key in QueryKeys
        }
        
    
    def _compute_success_stats(self, query_stats):
        success_counts = {key.result_key: 0 for key in QueryKeys}
        search_counts = {key.result_key: 0 for key in QueryKeys}
    
        for stats in query_stats:
            for key in QueryKeys:
                if f"?{key.query_key}" in stats.get("selected_elements", []):
                    search_counts[key.result_key] += 1
                    if stats.get(key.result_key, 0) > 0:
                        success_counts[key.result_key] += 1
    
        return {
            key.result_key: {
                "queries_with_results": success_counts[key.result_key],
                "percentage_queries_with_results": round(
                    (success_counts[key.result_key] / search_counts[key.result_key]) * 100, 2
                ) if search_counts[key.result_key] > 0 else 0
            }
            for key in QueryKeys
        }


    def _compute_average_results_per_successful_query(self, query_stats):
        total_results = {key.result_key: 0 for key in QueryKeys}
        successful_queries = {key.result_key: 0 for key in QueryKeys}
    
        for stats in query_stats:
            for key in QueryKeys:
                if f"?{key.query_key}" in stats.get("selected_elements", []) and stats.get(key.result_key, 0) > 0:
                    total_results[key.result_key] += stats[key.result_key]
                    successful_queries[key.result_key] += 1
    
        return {
            key.result_key: {
                "average_results_per_successful_query": round(
                    (total_results[key.result_key] / successful_queries[key.result_key]), 2
                ) if successful_queries[key.result_key] > 0 else None
            }
            for key in QueryKeys
        }

