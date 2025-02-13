from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException
from duckduckgo_search.exceptions import RatelimitException as DuckDuckGoRatelimitException
from duckduckgo_search.exceptions import TimeoutException as DuckDuckGoTimeoutException
import time


# =============================================================================
#  DuckDuckGoSearchService Class
# =============================================================================

class DuckDuckGoSearchService():

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, results_count = 10):
        self.service_name = "DuckDuckGo"
        self.results_count = results_count
        self.rate_limit = True
              
    
    # -------------------------------------------------------------------------
    # Search Methods
    # -------------------------------------------------------------------------

    # *** URLs by Web Query ***
    
    def search_by_query(self, keyword):
        start_time = time.time()
        results = []
        
        try:
            with DDGS() as ddgs:
                for i, result in enumerate(ddgs.text(keyword)):
                    if i >= self.results_count:
                        break
                    results.append(result['href'])
                    
        except DuckDuckGoRatelimitException as e:
            print(f"Rate limit exceeded: {e}")
            raise RatelimitException(str(e))
        except DuckDuckGoTimeoutException as e:
            print(f"Request timed out: {e}")
            raise TimeoutException(str(e))
        except DuckDuckGoSearchException as e:
            print(f"Search error: {e}")
            raise SearchEngineException(str(e))
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        return results, elapsed_time


# =============================================================================
#  Exception Classes
# =============================================================================

class SearchEngineException(Exception):
    """General exception for search engine errors."""
    pass

class RatelimitException(SearchEngineException):
    """Exception for rate limitation errors."""
    pass

class TimeoutException(SearchEngineException):
    """Exception for timeout errors."""
    pass


# =============================================================================
#  Base Use Test
# =============================================================================

if __name__ == '__main__':
    print("\n *** Base Use Test ***")
    ddgss =  DuckDuckGoSearchService()
    results = ddgss.search_by_query("Beowulf and the Critics purchase")
    print(results)
    