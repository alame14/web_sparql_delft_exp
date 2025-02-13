import os

FILE_PATH = os.path.abspath(__file__)
FILE_DIR = os.path.dirname(FILE_PATH)


# =============================================================================
#  GraphLoader Class
# =============================================================================

class GraphLoader:
    
    # -------------------------------------------------------------------------
    # Class attribute(s) / method(s)
    # -------------------------------------------------------------------------

    DYNAMIC_MICRODATA_GRAPH_PATH = f"{FILE_DIR}/dynamic_microdata_graph.ttl"


    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
        
    def __init__(self, graph):
        self.graph = graph


    # -------------------------------------------------------------------------
    # Method(s)
    # -------------------------------------------------------------------------

    def init_graph(self):
        try:
            self.graph.serialize(destination=GraphLoader.DYNAMIC_MICRODATA_GRAPH_PATH, format='turtle')
        except Exception as e:
            raise Exception(f'metahub.GraphLoader.init_graph >> {str(e)}')
            

    def load_graph(self):
        try:
            graph_path = GraphLoader.DYNAMIC_MICRODATA_GRAPH_PATH
            # print('----- load graph from file: ', graph_path)

            if not os.path.exists(graph_path):
                print(f'File does not exist: {graph_path}')
                return

            self.graph.parse(graph_path, format="turtle")

        except Exception as e:
            raise Exception(f'metahub.GraphLoader.load_graph >> {str(e)}')