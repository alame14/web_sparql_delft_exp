from sparql_analyzer.sparql_algebra_investigator import SparqlAlgebraInvestigator
from urllib.parse import urlparse


# =============================================================================
#  QueryAdjuster Class
# =============================================================================

class QueryAdjuster:

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, prefix, property_accessor):
        self.prefix = prefix
        self.property_accessor = property_accessor


    # -------------------------------------------------------------------------
    # Method(s)
    # -------------------------------------------------------------------------

    def adjust_query(self, query):
        query = self._preprocess_query(query)
        investigator = SparqlAlgebraInvestigator(query=query)
        target_triples = investigator.filter_triples_by_prefix(self.prefix)
        
        # Triples without prefixes from target list
        all_triples = investigator.get_triples()
        other_triples = [t for t in all_triples if t not in target_triples]
    
        adjusted_triples = other_triples
        
        for triple in target_triples:
            subject, predicate, obj = triple
            adjusted_predicate = self._adjust_property(predicate)
            adjusted_triples.append((subject, adjusted_predicate, obj))
        
        investigator.set_triples(adjusted_triples)
        return investigator.reconstruct_query()
    
    
    def _preprocess_query(self, query):
        """ Preprocess the query if needed (e.g., removing comments, formatting) """
        return query

    
    def _adjust_property(self, property_uri):
        """ Adjust the property URI using the property_accessor """
        namespace, local_name = self._split_uri(property_uri)
        print('-- local_name: ', local_name)
        new_uri = self.property_accessor.get_property_uri(local_name)
        new_uri = self._format_uri(new_uri)
        print('-- prop_keys: ', self.property_accessor.get_property_keys())
        print('-- new_uri: ', new_uri)
        return new_uri
    
    
    def _split_uri(self, uri):
        """ Split the URI into namespace and local_name """
        parsed_uri = urlparse(uri)
        namespace = f"{parsed_uri.scheme}://{parsed_uri.netloc}{parsed_uri.path.rsplit('/', 1)[0]}/"
        local_name = uri[len(namespace):]
        return namespace, local_name
    
    
    def _format_uri(self, uri):
        """ Ensure the URI is properly formatted with <...> if not already """
        if not (uri.startswith("<") and uri.endswith(">")):
            return f"<{uri}>"
        return uri
