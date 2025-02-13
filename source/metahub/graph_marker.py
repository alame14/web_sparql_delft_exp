from rdflib import Graph, Namespace, URIRef


# =============================================================================
# GraphMarker Class
# =============================================================================

class GraphMarker:
    """
    GraphMarker: class for marking namespaces in an RDF graph.
    
    This class is designed to:
    - Add missing namespaces to an RDF graph with generated prefixes.
    - Ensure existing namespaces retain their original prefixes.
    - Mark namespaces by appending a specified marking namespace to each original namespace.
    - Bind a specified prefix to the marking namespace.

    The process involves creating a new graph and transferring all triples from the original graph
    to the new graph while marking the namespaces and retaining the original prefixes.
    """
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
                
    def __init__(self, rdf_graph, exclude_list = [], 
                 marking_prefix = 'md', marking_namespace = 'https://microdata.flamelis.org/'):
        self.original_graph = rdf_graph
        self.exclude_list = exclude_list
        self.marking_prefix = marking_prefix
        self.marking_namespace = marking_namespace
        self.md = Namespace(self.marking_namespace)
        self.prefix_count = 1
        self.marked_graph = None
        
        
    # -------------------------------------------------------------------------
    # Main Method
    # -------------------------------------------------------------------------

    def mark_graph(self) -> Graph:
        self._adjust_prefix_count(self.original_graph)
        
        new_graph = Graph()
        new_graph.namespace_manager.bind(self.marking_prefix, self.md)

        existing_prefixes = {str(ns): prefix for prefix, ns in self.original_graph.namespace_manager.namespaces()}
        
        for subj, pred, obj in self.original_graph:
            new_subj = self._mark_namespace(subj, new_graph, existing_prefixes) if str(subj) not in self.exclude_list else subj
            new_pred = self._mark_namespace(pred, new_graph, existing_prefixes) if str(pred) not in self.exclude_list else pred
            new_obj = self._mark_namespace(obj, new_graph, existing_prefixes) if str(obj) not in self.exclude_list else obj
            new_graph.add((new_subj, new_pred, new_obj))

        self.marked_graph = new_graph
        
        return new_graph
            
    
    # -------------------------------------------------------------------------
    # Adjustment Method(s)
    # -------------------------------------------------------------------------

    def _adjust_prefix_count(self, graph: Graph):
        for prefix, namespace in graph.namespace_manager.namespaces():
            if prefix.startswith("ns"):
                try:
                    self.prefix_count = max(self.prefix_count, int(prefix[2:]) + 1)
                except ValueError:
                    pass
            
            
    # -------------------------------------------------------------------------
    # Marking Method(s)
    # -------------------------------------------------------------------------

    def _mark_namespace(self, uri: URIRef, new_graph: Graph, existing_prefixes: dict) -> URIRef:
        
        if isinstance(uri, URIRef):
            
            # Checks whether the URI already begins with the marking namespace
            if str(uri).startswith(self.marking_namespace):
                return uri
            
            namespace = str(uri).rsplit('/', 1)[0] + '/'
            if namespace == self.marking_namespace:
                prefix = self.marking_prefix
                new_graph.namespace_manager.bind(prefix, Namespace(namespace))
                return uri
            if namespace not in existing_prefixes:
                prefix = self._generate_prefix()
                new_namespace = Namespace(f"{self.marking_namespace}{namespace}")
                new_graph.namespace_manager.bind(prefix, new_namespace)
                existing_prefixes[namespace] = prefix
            else:
                prefix = existing_prefixes[namespace]
                new_namespace = Namespace(f"{self.marking_namespace}{namespace}")
                new_graph.namespace_manager.bind(prefix, new_namespace)
            
            local_part = str(uri).rsplit('/', 1)[-1]
            return URIRef(new_namespace[local_part])
        
        return uri


    def _generate_prefix(self) -> str:
        prefix = f"ns{self.prefix_count}"
        self.prefix_count += 1
        return prefix
