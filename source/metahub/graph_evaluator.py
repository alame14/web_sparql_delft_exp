from rdflib import URIRef, BNode, Literal


# =============================================================================
#  QueryEvaluator Class
# =============================================================================

class QueryEvaluator:

    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, graph):
        self.graph = graph


    # -------------------------------------------------------------------------
    # Method(s)
    # -------------------------------------------------------------------------

    def evaluate_query(self, query, format_result=True):
        try:
            rdflib_result = self.graph.query(query)
            if format_result:
                return self._format_results(rdflib_result), None
            return rdflib_result, None
        except Exception as e:
            return None, e

    def _format_results(self, query_result):
        columns = query_result.vars
        rows = []

        for row in query_result:
            binding = {}
            for var in query_result.vars:
                value = row[var]
                if value is not None:
                    if isinstance(value, URIRef):
                        binding[var] = {"type": "uri", "value": str(value)}
                    elif isinstance(value, BNode):
                        binding[var] = {"type": "bnode", "value": str(value)}
                    elif isinstance(value, Literal):
                        literal_info = {"type": "literal", "value": str(value)}
                        if value.datatype:
                            literal_info["datatype"] = str(value.datatype)
                        if value.language:
                            literal_info["xml:lang"] = value.language
                        binding[var] = literal_info
            rows.append(binding)

        return {"columns": columns, "rows": rows}
