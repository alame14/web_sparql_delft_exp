import re


# =============================================================================
#  QueryPreprocessor Class
# =============================================================================

class QueryPreprocessor:
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self):
        self.required_prefixes = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "mk": "http://mekano.org/",
            "md": "https://microdata.flamelis.org/",
        }
        self.replacement_dict = {
            "<webpage>": "mk:contains-thing",
            "sdo:webpage": "mk:contains-thing",
            "https://schema.org/webpage": "mk:contains-thing",
        }
        
            
    # -------------------------------------------------------------------------
    # Preprocessing Methods
    # -------------------------------------------------------------------------

    def replace_prefixes(self, query):
        prefix_pattern = re.compile(r'PREFIX\s+(\w+):\s+<([^>]+)>')
        prefixes = dict(prefix_pattern.findall(query))

        existing_uris = {uri: prefix for prefix, uri in prefixes.items()}

        for required_prefix, required_uri in self.required_prefixes.items():
            if required_prefix in prefixes:
                if prefixes[required_prefix] != required_uri:
                    index = 1
                    new_prefix = f"{required_prefix}{index}"
                    while new_prefix in prefixes:
                        index += 1
                        new_prefix = f"{required_prefix}{index}"
                    
                    query = re.sub(rf'PREFIX\s+{required_prefix}:\s+<{prefixes[required_prefix]}>',
                                   f'PREFIX {new_prefix}: <{prefixes[required_prefix]}>',
                                   query)
                    query = re.sub(rf'\b{required_prefix}:', f'{new_prefix}:', query)
                    
                    query = f"PREFIX {required_prefix}: <{required_uri}>\n" + query
            else:
                if required_uri in existing_uris:
                    old_prefix = existing_uris[required_uri]
                    query = re.sub(rf'\b{old_prefix}:', f'{required_prefix}:', query)
                    query = re.sub(rf'PREFIX\s+{old_prefix}:\s+<{required_uri}>',
                                   f'PREFIX {required_prefix}: <{required_uri}>',
                                   query)
                else:
                    query = f"PREFIX {required_prefix}: <{required_uri}>\n" + query
        
        return query
    

    def replace_properties(self, query):
        for prop, replacement in self.replacement_dict.items():
            query = re.sub(rf'{prop}', replacement, query)
        return query


    def replace_class_type(self, query):
        query = re.sub(r'\ba\b', 'rdf:type', query)
        return query


    def preprocess_query(self, query):
        query = self.replace_prefixes(query)
        query = self.replace_properties(query)
        query = self.replace_class_type(query)
        return query



# =============================================================================
#  Base Use Test
# =============================================================================

def test_replace_prefixes_case_1():
    query_preprocessor = QueryPreprocessor()
    query = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 a dbo:Actor .
        ?Actor_1 <webpage> ?webpage_102 .
        ?webpage_102 n6:url ?url_191 . }
LIMIT 200
"""
    expected_result = """PREFIX md: <http://microdata.mekano.org/>
PREFIX mk: <http://mekano.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 a dbo:Actor .
        ?Actor_1 <webpage> ?webpage_102 .
        ?webpage_102 n6:url ?url_191 . }
LIMIT 200
"""
    result = query_preprocessor.replace_prefixes(query)
    assert result == expected_result, f"Test Case 1 Failed: {result}"

def test_replace_prefixes_case_2():
    query_preprocessor = QueryPreprocessor()
    query = """PREFIX mk: <http://incorrect.uri/>
SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 mk:contains-thing ?webpage_102 .
        ?webpage_102 mk:url ?url_191 . }
LIMIT 200
"""
    expected_result = """PREFIX md: <http://microdata.mekano.org/>
PREFIX mk: <http://mekano.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX mk1: <http://incorrect.uri/>
SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 mk1:contains-thing ?webpage_102 .
        ?webpage_102 mk1:url ?url_191 . }
LIMIT 200
"""
    result = query_preprocessor.replace_prefixes(query)
    assert result == expected_result, f"Test Case 2 Failed: {result}"

def test_replace_prefixes_case_3():
    query_preprocessor = QueryPreprocessor()
    query = """PREFIX old: <http://mekano.org/>
SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 old:contains-thing ?webpage_102 .
        ?webpage_102 old:url ?url_191 . }
LIMIT 200
"""
    expected_result = """PREFIX md: <http://microdata.mekano.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX mk: <http://mekano.org/>
SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 mk:contains-thing ?webpage_102 .
        ?webpage_102 mk:url ?url_191 . }
LIMIT 200
"""
    result = query_preprocessor.replace_prefixes(query)
    assert result == expected_result, f"Test Case 3 Failed: {result}"

def test_replace_prefixes_case_4():
    query_preprocessor = QueryPreprocessor()
    query = """PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 dbo:Actor .
        ?Actor_1 <webpage> ?webpage_102 .
        ?webpage_102 n6:url ?url_191 . }
LIMIT 200
"""
    expected_result = """PREFIX md: <http://microdata.mekano.org/>
PREFIX mk: <http://mekano.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 dbo:Actor .
        ?Actor_1 <webpage> ?webpage_102 .
        ?webpage_102 n6:url ?url_191 . }
LIMIT 200
"""
    result = query_preprocessor.replace_prefixes(query)
    assert result == expected_result, f"Test Case 4 Failed: {result}"

def test_replace_properties():
    query_preprocessor = QueryPreprocessor()
    query = """SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 <webpage> ?webpage_102 .
        ?webpage_102 sdo:webpage ?url_191 . }
LIMIT 200
"""
    expected_result = """SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 mk:contains-thing ?webpage_102 .
        ?webpage_102 mk:contains-thing ?url_191 . }
LIMIT 200
"""
    result = query_preprocessor.replace_properties(query)
    assert result == expected_result, f"Replace Properties Test Failed: {result}"

def test_replace_class_type():
    query_preprocessor = QueryPreprocessor()
    query = """SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 a dbo:Actor .
        ?Actor_1 <webpage> ?webpage_102 .
        ?webpage_102 n6:url ?url_191 . }
LIMIT 200
"""
    expected_result = """SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 rdf:type dbo:Actor .
        ?Actor_1 <webpage> ?webpage_102 .
        ?webpage_102 n6:url ?url_191 . }
LIMIT 200
"""
    result = query_preprocessor.replace_class_type(query)
    assert result == expected_result, f"Replace Class Type Test Failed: {result}"

def test_preprocess_query():
    query_preprocessor = QueryPreprocessor()
    query = """PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX n6: <http://microdata.mekano.org/>
SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 a dbo:Actor .
        ?Actor_1 <webpage> ?webpage_102 .
        ?webpage_102 n6:url ?url_191 . }
LIMIT 200
"""
    expected_result = """PREFIX mk: <http://mekano.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX md: <http://microdata.mekano.org/>
SELECT DISTINCT ?Actor_1 ?webpage_102 ?url_191
WHERE { ?Actor_1 rdf:type dbo:Actor .
        ?Actor_1 mk:contains-thing ?webpage_102 .
        ?webpage_102 md:url ?url_191 . }
LIMIT 200
"""
    result = query_preprocessor.preprocess_query(query)
    assert result == expected_result, f"Preprocess Query Test Failed: {result}"

# Running tests
if __name__ == "__main__":
    test_replace_prefixes_case_1()
    test_replace_prefixes_case_2()
    test_replace_prefixes_case_3()
    test_replace_prefixes_case_4()
    test_replace_properties()
    test_replace_class_type()
    test_preprocess_query()
    print("All tests passed.")
