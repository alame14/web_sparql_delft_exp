from rdflib.plugins.sparql import prepareQuery
from rdflib.term import Variable, URIRef, Literal


# =============================================================================
#  Display Class
# =============================================================================

class SparqlDisplay:
    
    def display_node(self, node, level, prefixes):
        indent = "  " * level
        display_str = indent
        
        if hasattr(node, 'name') and node.name is not None:
            display_str += f"{node.name}"
        else:
            display_str += f"{node}"
        
        display_str += f" (type: {type(node).__name__}"
        
        if hasattr(node, '_vars') and node._vars is not None:
            display_str += f" ; vars: {[str(var) for var in node._vars]}"
        
        display_str += ')'
        
        result_str = display_str + "\n"
        
        if hasattr(node, 'p') and node.p is not None:
            result_str += self.display_node(node.p, level + 1, prefixes)
        
        if hasattr(node, 'expr') and node.expr is not None:
            result_str += self.display_node(node.expr, level + 1, prefixes)
        
        if hasattr(node, 'p1') and node.p1 is not None:
            result_str += self.display_node(node.p1, level + 1, prefixes)
        
        if hasattr(node, 'p2') and node.p2 is not None:
            result_str += self.display_node(node.p2, level + 1, prefixes)
        
        if hasattr(node, 'triples') and node.triples is not None:
            result_str += indent + "  triples (type: list)\n"
            for triple in node.triples:
                formatted_triple = self.display_triple(triple, prefixes)
                result_str += indent + "    " + formatted_triple + "\n"
        
        return result_str

    def display_raw(self, node):
        raw_str = f"{type(node).__name__}"
        
        if isinstance(node, dict):
            raw_str += f"_{node}"
        elif hasattr(node, '__dict__'):
            raw_str += f"_{node.__dict__}"
        else:
            raw_str += f"_{node}"
        
        return raw_str

    def display_triple(self, triple, prefixes):
        def format_term(term):
            if isinstance(term, Variable):
                return f"Variable '{term}'"
            elif isinstance(term, URIRef):
                for prefix, uri in prefixes.items():
                    if str(term).startswith(uri):
                        return f"URIRef '{prefix}:{str(term)[len(uri):]}'"
                return f"URIRef '{term}'"
            elif isinstance(term, Literal):
                return f"Literal '{term}'"
            else:
                return str(term)
        
        return f"({format_term(triple[0])}, {format_term(triple[1])}, {format_term(triple[2])})"
