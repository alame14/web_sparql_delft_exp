from sparql_analyzer.sparql_algebra_investigator import SparqlAlgebraInvestigator
from sparql_analyzer.query_preprocessing import QueryPreprocessor
from rdflib.term import Variable, URIRef, Literal

class QueryPivot:
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, query, logger=None):
        self.logger = logger
        self.original_query = query
        self.preprocessed_query = self._preprocess_query(query)
        self.investigator = SparqlAlgebraInvestigator(query=self.preprocessed_query)
        self.triple_list = self.get_triples()
        self._check_web_pivot_consistency()
        self.web_pivot_variable = self._extract_web_pivot()
        self.microdata_pivot_variable = self._extract_microdata_pivot()
        self.web_target_entity_variable_list = self._extract_web_target_entitiy_variables()
        self.web_target_keyword_list = self._extract_web_target_keywords() 
        # print('----- original_query: ', self.original_query)  
        # print('----- preprocessed_query: ', self.preprocessed_query)  
        # print('----- triples: ', self.triple_list)   
        # print('----- web_pivot: ', self.web_pivot_variable)   
        # print('----- microdata_pivot: ', self.microdata_pivot_variable)   
        # print('----- web_target_entity_variable_list: ', self.web_target_entity_variable_list)   
        # print('----- web_target_keyword_list: ', self.web_target_keyword_list)     
        


    def _preprocess_query(self, query):
        query_preprocessor = QueryPreprocessor()
        return query_preprocessor.preprocess_query(query)  
    
    def _check_web_pivot_consistency(self):
        thing_property = URIRef('http://mekano.org/containsThing')
        keyword_property = URIRef('http://mekano.org/containsWord')
        microdata_property = URIRef('http://mekano.org/hasMicrodata')
    
        web_pivot_subjects = set()
    
        for triple in self.triple_list:
            subject, predicate, obj = self._parse_triple(triple)
            if predicate in [thing_property, keyword_property, microdata_property]:
                web_pivot_subjects.add(subject)
    
        if len(web_pivot_subjects) > 1:
            raise ValueError("Inconsistent web pivot variables found: " + ", ".join(web_pivot_subjects))
    
        self.logger.debug("-- Web pivot variable consistency verified")
        
        
    def __str__(self):
        return f'QueryPivot({self.web_pivot_variable}, {self.microdata_pivot_variable})'
            
        
    # -------------------------------------------------------------------------
    # Extraction Methods
    # -------------------------------------------------------------------------

    def _extract_web_pivot(self):
        thing_property = URIRef('http://mekano.org/containsThing')
        keyword_property = URIRef('http://mekano.org/containsWord')
        microdata_property = URIRef('http://mekano.org/hasMicrodata')
        
        for triple in self.triple_list:
            subject, predicate, obj = self._parse_triple(triple)
            if predicate in [thing_property, keyword_property, microdata_property]:
                return subject
        
        self.logger.info("-- Web pivot variable could not be deduced")
        return None


    def _extract_microdata_pivot(self):
        microdata_property = URIRef('http://mekano.org/hasMicrodata')
        
        for triple in self.triple_list:
            subject, predicate, obj = self._parse_triple(triple)
            if predicate == microdata_property:
                return obj
        
        self.logger.debug("-- Microdata pivot variable could not be deduced")
        return None


    def _extract_web_target_entitiy_variables(self):
        if self.web_pivot_variable is None:
            self.logger.debug("-- Cannot extract target entities because web_pivot is None")
            return []

        target_entity_list = []
        thing_property = URIRef('http://mekano.org/containsThing')

        for triple in self.triple_list:
            subject, predicate, obj = self._parse_triple(triple)
            if predicate == thing_property and subject == self.web_pivot_variable:
                target_entity_list.append(obj)

        if not target_entity_list:
            self.logger.debug("-- No target entities could be extracted")

        return target_entity_list

    def _extract_web_target_keywords(self):
        if self.web_pivot_variable is None:
            self.logger.debug("-- Cannot extract target keywords because web_pivot is None")
            return []

        target_keyword_list = []
        keyword_property = URIRef('http://mekano.org/containsWord')

        for triple in self.triple_list:
            subject, predicate, obj = self._parse_triple(triple)
            if predicate == keyword_property and subject == self.web_pivot_variable:
                target_keyword_list.append(obj)

        if not target_keyword_list:
            self.logger.debug("-- No target keywords could be extracted")

        return target_keyword_list


    def _parse_triple(self, triple):
        return triple[0], triple[1], triple[2]
                    
    
    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------

    def get_web_pivot_variable(self):
        if self.web_pivot_variable:
            return Variable(self.web_pivot_variable)
        else:
            return None

    def get_microdata_pivot_variable(self):
        if self.microdata_pivot_variable:
            return Variable(self.microdata_pivot_variable)
        else:
            return None

    def get_select_clause(self):
        return self.investigator.get_select_clause()

    def get_triples(self):
        return self.investigator.get_triples()

    def get_bindings_web_pivot(self):
        res = self.get_bindings(self.web_pivot_variable)
        return self._triples_to_strings(res)

    def get_bindings_microdata_pivot(self):
        res = self.get_bindings(self.microdata_pivot_variable)
        return self._triples_to_strings(res)

    def get_scope_microdata_pivot(self):
        res = self.get_scope(self.microdata_pivot_variable)
        return self._triples_to_strings(res)

    def get_forward_scope_microdata_pivot(self):
        res = self.get_forward_scope(self.microdata_pivot_variable)
        return self._triples_to_strings(res)

    def _triples_to_strings(self, triples):
        return [f"({str(subj)} {str(pred)} {str(obj)})" for subj, pred, obj in triples]
            
            
    # -------------------------------------------------------------------------
    # Variable Relationship Methods
    # -------------------------------------------------------------------------

    def get_bindings(self, variable):
        triples = [triple for triple in self.investigator.get_triples() if variable in triple]
        return self._remove_duplicate_triples(triples)


    def get_scope(self, variable, visited=None):
        if visited is None:
            visited = set()
        scope_triples = self.get_bindings(variable)
        related_vars = {var for triple in scope_triples for var in triple if var != variable and triple[0] == variable}
        for var in related_vars:
            if var not in visited:
                visited.add(var)
                scope_triples.extend(self.get_scope(var, visited))
        return self._remove_duplicate_triples(scope_triples)


    def get_forward_scope(self, variable, visited=None):
        if visited is None:
            visited = set()
        forward_scope_triples = self.get_bindings(variable)
        related_vars = {triple[2] for triple in forward_scope_triples if isinstance(triple[2], Variable) and triple[2] != variable}
        for var in related_vars:
            if var not in visited:
                visited.add(var)
                forward_scope_triples.extend(self.get_scope(var, visited))
        return self._remove_duplicate_triples(forward_scope_triples)

    def _remove_duplicate_triples(self, triples):
        seen = set()
        unique_triples = []
        for triple in triples:
            if triple not in seen:
                unique_triples.append(triple)
                seen.add(triple)
        return unique_triples
