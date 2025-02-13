from rdflib.plugins.sparql import prepareQuery
from rdflib.term import Variable, URIRef, Literal

from sparql_analyzer.sparql_extractor import SparqlExtractor
from sparql_analyzer.sparql_display import SparqlDisplay
from sparql_analyzer.sparql_reconstructor import SparqlReconstructor


# =============================================================================
#  SparqlAlgebraInvestigator Class
# =============================================================================

class SparqlAlgebraInvestigator:
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
        
    # def __init__(self, algebra=None, query=None, mode="structured"):
    #     self.extractor = SparqlExtractor()
        
    #     if query:
    #         self.algebra = prepareQuery(query).algebra
    #         self.prefixes = self.extractor.extract_prefixes(query)
    #         self.limit = self.extractor.extract_limit_from_query(query)
    #     elif algebra:
    #         self.algebra = algebra
    #         self.prefixes = {}
    #         self.limit = self.extractor.extract_limit_from_algebra(self.algebra)
    #     else:
    #         raise ValueError("You must provide either a SPARQL query or an algebra.")
        
    #     self.reconstructor = SparqlReconstructor(self.algebra, self.prefixes, self.limit)
    #     self.display = SparqlDisplay()
        
    #     self.mode = mode


    def __init__(self, algebra=None, query=None, mode="structured", ignore_limit=False):
        self.extractor = SparqlExtractor()
        
        if query:
            self.algebra = prepareQuery(query).algebra
            self.prefixes = self.extractor.extract_prefixes(query)
            self.limit = None if ignore_limit else self.extractor.extract_limit_from_query(query)
        elif algebra:
            self.algebra = algebra
            self.prefixes = {}
            self.limit = None if ignore_limit else self.extractor.extract_limit_from_algebra(self.algebra)
        else:
            raise ValueError("You must provide either a SPARQL query or an algebra.")
        
        self.reconstructor = SparqlReconstructor(self.algebra, self.prefixes, self.limit)
        self.display = SparqlDisplay()

        self.mode = mode

    # -------------------------------------------------------------------------
    # Display
    # -------------------------------------------------------------------------
    
    def __str__(self):
        if self.mode == "structured":
            return self.display.display_node(self.algebra, 0, self.prefixes)
        elif self.mode == "raw":
            return self.display.display_raw(self.algebra)
        else:
            raise ValueError("Invalid mode. Use 'structured' or 'raw'.")
    
    def set_mode(self, mode):
        if mode in ["structured", "raw"]:
            self.mode = mode
        else:
            raise ValueError("Invalid mode. Use 'structured' or 'raw'.")


    # -------------------------------------------------------------------------
    # Query Reconstruction
    # -------------------------------------------------------------------------

    def reconstruct_query(self):
        return self.reconstructor.reconstruct_query()
    
    
    # -------------------------------------------------------------------------
    # Algebra Handling Methods
    # -------------------------------------------------------------------------
    
    def get_select_clause(self):
        # Assumes the algebra representation has a 'PV' attribute for the SELECT variables
        select_vars = self.algebra['PV']
        select_clause = " ".join([f'?{str(var)}' for var in select_vars])
        return select_clause

    def get_triples(self):
        return self._extract_triples(self.algebra)

    def get_formatted_triple_list(self):
        raw_triples = self.get_triples()
        formatted_triple_list = [self.reconstructor.format_triple(triple) for triple in raw_triples]
        formatted_triple_list = [tuple(triple.split()) for triple in formatted_triple_list]
        return formatted_triple_list

    def _extract_triples(self, node):
        triples = []
        if hasattr(node, 'triples') and node.triples is not None:
            triples.extend(node.triples)
        if hasattr(node, 'p') and node.p is not None:
            triples.extend(self._extract_triples(node.p))
        if hasattr(node, 'p1') and node.p1 is not None:
            triples.extend(self._extract_triples(node.p1))
        if hasattr(node, 'p2') and node.p2 is not None:
            triples.extend(self._extract_triples(node.p2))
        return triples

    def set_triples(self, new_triples):
        self._set_triples_recursive(self.algebra, new_triples)

    def _set_triples_recursive(self, node, new_triples):
        if hasattr(node, 'triples') and node.triples is not None:
            node.triples = new_triples
        if hasattr(node, 'p') and node.p is not None:
            self._set_triples_recursive(node.p, new_triples)
        if hasattr(node, 'p1') and node.p1 is not None:
            self._set_triples_recursive(node.p1, new_triples)
        if hasattr(node, 'p2') and node.p2 is not None:
            self._set_triples_recursive(node.p2, new_triples)

    def filter_triples_by_properties(self, properties):
        return [triple for triple in self.get_triples() if triple[1] in properties]

    def filter_triples_by_prefix(self, prefix):
        return [
            triple for triple in self.get_triples()
            if any(str(triple[1]).startswith(uri) for pfx, uri in self.prefixes.items() if pfx == prefix)
        ]

    def get_variables_in_triples(self):
        variables = set()
        for triple in self.get_triples():
            for term in triple:
                if isinstance(term, Variable):
                    variables.add(term)
        return list(variables)

    def get_variables(self):
        return self.algebra['PV']

    def set_variables(self, new_vars):
        self.algebra['PV'] = new_vars

    def clean_unused_variables(self):
        used_vars = set(self.get_variables_in_triples())
        current_vars = set(self.algebra['PV'])
        updated_vars = list(current_vars.intersection(used_vars))
        self.set_variables(updated_vars)
        
    def maximize_projection_variables(self):
        variables = self.get_variables_in_triples()
        self.set_variables(variables)



