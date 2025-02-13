from rdflib.plugins.sparql import prepareQuery
from rdflib.term import Variable, URIRef, Literal

# =============================================================================
#  Extraction Class
# =============================================================================

class SparqlExtractor:
    
    def extract_prefixes(self, query):
        prefixes = {}
        lines = query.strip().splitlines()
        for line in lines:
            if line.strip().lower().startswith("prefix"):
                parts = line.split()
                prefix = parts[1].strip(':')
                uri = parts[2].strip('<>')
                prefixes[prefix] = uri
        return prefixes

    def extract_limit_from_query(self, query):
        limit = None
        lines = query.strip().splitlines()
        for line in lines:
            if line.strip().lower().startswith("limit"):
                limit = int(line.split()[1])
        return limit
    
    def extract_limit_from_algebra(self, algebra):
        if 'limit' in algebra:
            return algebra['limit']
        return None

    def extract_triples(self, node):
        triples = []
        if hasattr(node, 'triples') and node.triples is not None:
            triples.extend(node.triples)
        if hasattr(node, 'p') and node.p is not None:
            triples.extend(self.extract_triples(node.p))
        if hasattr(node, 'p1') and node.p1 is not None:
            triples.extend(self.extract_triples(node.p1))
        if hasattr(node, 'p2') and node.p2 is not None:
            triples.extend(self.extract_triples(node.p2))
        return triples
