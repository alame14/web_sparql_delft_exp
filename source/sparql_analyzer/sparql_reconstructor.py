from rdflib.term import Variable, URIRef, Literal

# =============================================================================
#  Reconstruction Class
# =============================================================================

class SparqlReconstructor:
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, algebra, prefixes, limit):
        self.algebra = algebra
        self.prefixes = prefixes
        self.limit = limit
    
    # -------------------------------------------------------------------------
    # Query Reconstruction
    # -------------------------------------------------------------------------
    
    def reconstruct_query(self):
        prefixes_str = self._reconstruct_prefixes()
        select_str = self._reconstruct_select()
        where_str = self._reconstruct_where(self.algebra)
        limit_value = self.limit
        
        query_str = f"{prefixes_str}\n{select_str}\nWHERE {{\n{where_str}\n}}"
        
        # TODO: gérer ORDER BY
        
        if limit_value is not None:
            query_str += "\nORDER BY ASC(?book)" # TODO: gérer ORDER BY
            query_str += f"\nLIMIT {limit_value}"
            
        return query_str

    def _reconstruct_prefixes(self):
        prefixes = "\n".join([f"PREFIX {prefix}: <{uri}>" for prefix, uri in self.prefixes.items()])
        prefixes += "\n"
        return prefixes

    def _reconstruct_select(self):
        vars_str = " ".join([f'?{str(var)}' for var in self.algebra['PV']])
        return f"SELECT {vars_str}"

    def _reconstruct_where(self, node, level=1, visited_triples=None):
        if visited_triples is None:
            visited_triples = set()
        
        indent = "  " * level
        where_clauses = []
        
        if hasattr(node, 'triples') and node.triples is not None:
            for triple in node.triples:
                formatted_triple = self.format_triple(triple)
                if formatted_triple not in visited_triples:
                    where_clauses.append(f"{indent}{formatted_triple} .")
                    visited_triples.add(formatted_triple)
        
        if hasattr(node, 'p') and node.p is not None:
            where_clauses.append(self._reconstruct_where(node.p, level, visited_triples))
        
        if hasattr(node, 'expr') and node.expr is not None:
            where_clauses.append(self._reconstruct_where(node.expr, level, visited_triples))
        
        if hasattr(node, 'p1') and node.p1 is not None:
            where_clauses.append(self._reconstruct_where(node.p1, level, visited_triples))
        
        if hasattr(node, 'p2') and node.p2 is not None:
            where_clauses.append(self._reconstruct_where(node.p2, level, visited_triples))
        
        # Filtrer les éléments vides avant de joindre
        return "\n".join([clause for clause in where_clauses if clause])
    



    # -------------------------------------------------------------------------
    # Triple Formatting
    # -------------------------------------------------------------------------
    
    def format_triple(self, triple):
        subject = self.format_term(triple[0])
        predicate = self.format_term(triple[1])
        obj = self.format_term(triple[2])
        return f"{subject} {predicate} {obj}"

    def format_term(self, term):
        if isinstance(term, Variable):
            return self.format_variable(term)
        elif isinstance(term, URIRef):
            return self.format_uriref(term)
        elif isinstance(term, Literal):
            return self.format_literal(term)
        else:
            return self.format_generic(term)
    
    def format_variable(self, term):
        return f"?{term}"
    
    def format_uriref(self, term):
        for prefix, uri in self.prefixes.items():
            if str(term).startswith(uri):
                return f"{prefix}:{str(term)[len(uri):]}"
        return f"<{term}>"
    
    def format_literal(self, term):
        if term.language:
            return f"\"{term}\"@{term.language}"
        elif term.datatype:
            return f"\"{term}\"^^<{term.datatype}>"
        else:
            return f"\"{term}\""
    
    def format_generic(self, term):
        return str(term)
