import json
import time


# =============================================================================
#  SimulatedSearchService Class
# =============================================================================

class SimulatedSearchService:
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, query_file_path):
        self.query_file_path = query_file_path
        self.queries = []
        self.load_queries()
        self.rate_limit = None
        
    # -------------------------------------------------------------------------
    # Load Queries from File
    # -------------------------------------------------------------------------
    
    def load_queries(self):
        """Load the queries from the JSON file."""
        try:
            with open(self.query_file_path, 'r') as f:
                data = json.load(f)
                self.queries = data.get("queries", [])
                print(f"Loaded {len(self.queries)} queries from {self.query_file_path}.")
        except FileNotFoundError:
            print(f"File {self.query_file_path} not found.")
            raise
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file {self.query_file_path}.")
            raise

    # -------------------------------------------------------------------------
    # Simulated Search Method
    # -------------------------------------------------------------------------

    def search_by_query(self, keyword):
        """
        Simulate a web search using pre-evaluated data. 
        Return the search results and evaluation time.
        """
        start_time = time.time()

        # Find the query with the matching keyword
        query = next((q for q in self.queries if q["web_query"] == keyword), None)
        
        if query:
            results = query.get("query_result", [])
            evaluation_time = query.get("evaluation_time", 0.0)
        else:
            results = []  # Return empty results if query not found
            evaluation_time = 0.0

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Simulated delay for the search
        return results, evaluation_time or elapsed_time


# =============================================================================
#  Base Use Test
# =============================================================================

if __name__ == '__main__':
    print("\n *** Simulated Search Service Test ***")
    
    # Initialize the service with a path to a JSON file containing queries
    simulated_service = SimulatedSearchService('../data/bfp_web_queries.json')
    
    # Test with a query from the file
    keyword = "Pyramids (novel) purchase"
    results, eval_time = simulated_service.search_by_query(keyword)
    print(f"Results for '{keyword}': {results}")
    print(f"Evaluation time: {eval_time:.2f} seconds")
    
    # Test with a query not in the file
    unknown_keyword = "Unknown query purchase"
    results, eval_time = simulated_service.search_by_query(unknown_keyword)
    print(f"Results for '{unknown_keyword}': {results}")
    print(f"Evaluation time: {eval_time:.2f} seconds")
