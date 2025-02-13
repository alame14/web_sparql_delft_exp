from sparql_analyzer.sparql_algebra_investigator import SparqlAlgebraInvestigator
from rdflib.term import Variable, Literal

class QuerySplitter:
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, query_pivot, empty_query_option="empty", logger=None):
        self.logger = logger
        self.logger.debug('\n-- Query Splitter Init ')
        # self.logger.debug(f'----- origin query: {query}')
        self.query_pivot = query_pivot
        self.query = self.query_pivot.preprocessed_query
        self.web_pivot = self.query_pivot.get_web_pivot_variable()
        self.microdata_pivot = self.query_pivot.get_microdata_pivot_variable()
        self.empty_query_option = empty_query_option
        
        self.investigator = self.query_pivot.investigator # SparqlAlgebraInvestigator(query=self.query)
        
        self._split_queries_with_pivots()
            
    
    # -------------------------------------------------------------------------
    # Splitting Methods
    # -------------------------------------------------------------------------

    def _split_queries_with_pivots(self):
        
        # Triples Computing
        web_pivot_bindings = self.query_pivot.get_bindings(self.web_pivot)
        microdata_pivot_forward_scope = self.query_pivot.get_forward_scope(self.microdata_pivot)
        all_triples = self.investigator.get_triples()
        web_microdata_triples = web_pivot_bindings + microdata_pivot_forward_scope
        triples_a = [triple for triple in all_triples if triple not in web_microdata_triples]
    
        # Query Constructions
        self.kg_query = self._construct_kg_query(triples_a)
        self.web_query_pattern = self._construct_web_query_pattern(web_pivot_bindings)
        self.web_microdata_query = self._construct_web_microdata_query(web_microdata_triples)


    def _construct_kg_query(self, triples):
        investigator_a = SparqlAlgebraInvestigator(algebra=self.investigator.algebra, query=self.query)
        investigator_a.set_triples(triples)
        investigator_a.clean_unused_variables()
        investigator_a.maximize_projection_variables()
        return self._finalize_query(investigator_a)


    def _construct_web_query_pattern(self, triples):
        contains_thing_obj = None
        contains_word_obj = None
                
        for triple in triples:
            subject, predicate, obj = triple
            if str(predicate) == "http://mekano.org/containsThing":
                contains_thing_obj = obj
            elif str(predicate) == "http://mekano.org/containsWord":
                contains_word_obj = obj
        
        if contains_thing_obj and isinstance(contains_word_obj, Literal):
            pattern = f"{{?{contains_thing_obj}}} {contains_word_obj}"
        else:
            pattern = ""
    
        return pattern


    def _construct_web_microdata_query(self, triples):
        investigator_c = SparqlAlgebraInvestigator(algebra=self.investigator.algebra, 
                                                   query=self.query,
                                                   ignore_limit=True)
        triples = self.query_pivot._remove_duplicate_triples(triples)
        investigator_c.set_triples(triples)
        investigator_c.clean_unused_variables()
        investigator_c.maximize_projection_variables()
        return self._finalize_query(investigator_c)


    def _finalize_query(self, investigator):
        if investigator.get_triples() and investigator.get_variables():
            return investigator.reconstruct_query()
        else:
            if self.empty_query_option == "empty":
                return "SELECT * WHERE { FILTER(false) }"
            elif self.empty_query_option == "none":
                return None
            else:
                return ""
                                
    
    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------

    def get_kg_query(self):
        return self.kg_query

    def get_web_query_pattern(self):
        return self.web_query_pattern

    def get_web_microdata_query(self):
        return self.web_microdata_query

    def get_original_query(self):
        return self.query

    def get_select_clause(self):
        return self.investigator.get_select_clause()

    def get_triples(self):
        res = self.investigator.get_triples()
        return self._triples_to_strings(res)

    def get_bindings_web_pivot(self):
        res = self.query_pivot.get_bindings()
        return self._triples_to_strings(res)

    def get_bindings_microdata_pivot(self):
        res = self.query_pivot.get_bindings(self.microdata_pivot)
        return self._triples_to_strings(res)

    def get_scope_microdata_pivot(self):
        res = self.query_pivot.get_scope(self.microdata_pivot)
        return self._triples_to_strings(res)

    def get_forward_scope_microdata_pivot(self):
        res = self.query_pivot.get_forward_scope(self.microdata_pivot)
        return self._triples_to_strings(res)

    def _triples_to_strings(self, triples):
        return [f"({str(subj)} {str(pred)} {str(obj)})" for subj, pred, obj in triples]
