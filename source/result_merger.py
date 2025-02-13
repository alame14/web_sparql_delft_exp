import xml.etree.ElementTree as ET
from rdflib import Variable
import json

from sparql_result_handler import SPARQLResultHandler


# =============================================================================
#  ResultMerger: class to merge results of SPARQL query evaluations
# =============================================================================

class ResultMerger:
    
    type_equivalences = [('url', 'uri')]  # Define equivalent types
        
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------

    def __init__(self, logger=None):
        self.logger = logger
        self.results = []
            
        
    # -------------------------------------------------------------------------
    # Adding Result Method(s)
    # -------------------------------------------------------------------------
        
    def add_result(self, result):
        """
        Adds a JSON result to the list of results.
        
        param result: The SPARQL result in JSON format.
        """
        if result is not None: 
            # print('----- result: ', result)       
            if SPARQLResultHandler.is_valid_result_xml(result):
                result = SPARQLResultHandler.convert_result_xml_to_dict(result)
            
            if SPARQLResultHandler.is_valid_result_dict(result):
                # print('----- standardize and add result')
                result = SPARQLResultHandler.convert_columns(result)
                self.results.append(result)
            else:
                raise ValueError("Invalid result format. Expected SPARQL XML or valid dictionary.")
            
            
    # def _is_valid_result_xml(self, result):
    #     if isinstance(result, (bytes, str)):
    #         try:
    #             print('----- try to parse the result data as XML')
    #             root = ET.fromstring(result)
    #             return root.tag == "{http://www.w3.org/2005/sparql-results#}sparql"
    #         except ET.ParseError:
    #             return False
    #     return False


    # def _is_valid_result_dict(self, data):
    #     if isinstance(data, dict):
    #         if 'columns' in data and 'rows' in data:
    #             if isinstance(data['columns'], list) and all(isinstance(col, str) for col in data['columns']):
    #                 if isinstance(data['rows'], list) and all(isinstance(row, dict) for row in data['rows']):
    #                     return True
    #     return False        
    
            
    # def _convert_result_xml_to_dict(self, result_xml):
    #     print('----- convert result xml to result dict')
        
    #     # Parse the XML data
    #     root = ET.fromstring(result_xml)
        
    #     # Extract column names from the <head> section
    #     columns = []
    #     for variable in root.find("{http://www.w3.org/2005/sparql-results#}head"):
    #         columns.append(variable.attrib['name'])
        
    #     # Extract rows from the <results> section
    #     rows = []
    #     for result in root.find("{http://www.w3.org/2005/sparql-results#}results"):
    #         row = {}
    #         for binding in result:
    #             name = binding.attrib['name']
    #             uri = binding.find("{http://www.w3.org/2005/sparql-results#}uri").text
    #             row[name] = {'type': 'uri', 'value': uri}
    #         rows.append(row)
        
    #     # Create the final dictionary
    #     result_dict = {
    #         'columns': columns,
    #         'rows': rows
    #     }
        
    #     return result_dict
    

    # def _convert_columns(self, data):
    #     columns = [str(col) if isinstance(col, Variable) else col for col in data['columns']]
    #     result = {
    #         'columns': columns,
    #         'rows': []
    #     }
        
    #     for row in data['rows']:
    #         new_row = {}
    #         for key, value in row.items():
    #             new_key = str(key) if isinstance(key, Variable) else key
    #             new_row[new_key] = value
    #         result['rows'].append(new_row)
        
    #     return result
    
        
    # -------------------------------------------------------------------------
    # Merging Result Method(s)
    # -------------------------------------------------------------------------

    def merge_results(self, select_vars, join_type='inner'):
        if not self.results:
            return {"columns": [], "rows": []}
        
        merged_results = self.results[0]['rows']
        merged_columns = set(self.results[0]['columns'])
        
        # print(' ***** DEV (ResultMerger.merge_result) *****')
        # for result in self.results:
        #     print('!!!!!!! ', result['columns'])
        # print(' ***** *** *****')

        for result in self.results[1:]:
            common_keys = merged_columns.intersection(set(result['columns']))
            if len(common_keys) == 0:
                continue

            if len(result['rows']) > 0:
                if join_type == 'inner':
                    merged_results = self._inner_join(merged_results, result['rows'], common_keys)
                elif join_type == 'outer':
                    merged_results = self._outer_join(merged_results, result['rows'], common_keys)
                merged_columns.update(result['columns'])
        
        selected_vars = select_vars.strip().split()
        filtered_results = self._select_columns(merged_results, selected_vars)
        
        return {
            "columns": [var[1:] for var in selected_vars],
            "rows": filtered_results
        }

    def _are_equivalent(self, value1, value2):
        if value1['value'] == value2['value']:
            type1 = value1['type']
            type2 = value2['type']
            if type1 == type2:
                return True
            for (equiv1, equiv2) in ResultMerger.type_equivalences:
                if (type1 == equiv1 and type2 == equiv2) or (type1 == equiv2 and type2 == equiv1):
                    return True
        return False

    def _inner_join(self, left, right, common_keys):
        join_result = []

        for left_binding in left:
            for right_binding in right:
                if all(self._are_equivalent(left_binding[key], right_binding[key]) for key in common_keys):
                    joined_binding = {**right_binding, **left_binding}
                    join_result.append(joined_binding)

        return join_result

    def _outer_join(self, left, right, common_keys):
        join_result = []

        for left_binding in left:
            match_found = False
            for right_binding in right:
                if all(self._are_equivalent(left_binding[key], right_binding[key]) for key in common_keys):
                    joined_binding = {**right_binding, **left_binding}
                    join_result.append(joined_binding)
                    match_found = True
            if not match_found:
                null_right = {key: None for key in right[0].keys() if key not in left_binding}
                join_result.append({**left_binding, **null_right})

        for right_binding in right:
            if not any(all(self._are_equivalent(right_binding[key], left_binding[key]) for key in common_keys) for left_binding in left):
                null_left = {key: None for key in left[0].keys() if key not in right_binding}
                join_result.append({**null_left, **right_binding})

        return join_result

    def _select_columns(self, bindings, selected_vars):
        filtered_results = []
        for binding in bindings:
            filtered_binding = {var[1:]: binding.get(var[1:], None) for var in selected_vars}
            filtered_results.append(filtered_binding)
        
        return filtered_results



# =============================================================================
#  Base Unit Test
# =============================================================================

if __name__ == "__main__":

    merger = ResultMerger()
    
    res1 = {
        'columns': [Variable('animal'), Variable('species')],
        'rows': [
            {Variable('animal'): {'type': 'uri', 'value': 'http://example.org/baby1'},
             Variable('species'): {'type': 'uri', 'value': 'http://example.org/species1'}},
            {Variable('animal'): {'type': 'uri', 'value': 'http://example.org/baby2'},
             Variable('species'): {'type': 'uri', 'value': 'http://example.org/species2'}},
            {Variable('animal'): {'type': 'uri', 'value': 'http://example.org/baby3'},
             Variable('species'): {'type': 'uri', 'value': 'http://example.org/species3'}}
        ]
    }
    
    res2 = {
        'columns': ['animal', 'webpage'],
        'rows': [
            {'animal': {'type': 'uri', 'value': 'http://example.org/baby1'},
             'webpage': {'type': 'url', 'value': 'http://example.org/webpage/animal1'}},
            {'animal': {'type': 'uri', 'value': 'http://example.org/baby2'},
             'webpage': {'type': 'url', 'value': 'http://example.org/webpage/animal2'}}
        ]
    }
    
    res3 = {
        'columns': ['age', 'webpage', 'name'],
        'rows': [
            {'age': {'type': 'literal', 'value': '1 year'},
             'webpage': {'type': 'uri', 'value': 'http://example.org/webpage/animal1'},
             'name': {'type': 'literal', 'value': 'Baby Animal 1'}},
            {'age': {'type': 'literal', 'value': '2 years'},
             'webpage': {'type': 'uri', 'value': 'http://example.org/webpage/animal2'},
             'name': {'type': 'literal', 'value': 'Baby Animal 2'}}
        ]
    }
    
    res3 = None
    
    merger.add_result(res1)
    merger.add_result(res2)
    merger.add_result(res3)
    
    # merge and selection
    select_clause = "?animal ?species ?webpage ?age ?name"
    merged_result = merger.merge_results(select_clause, join_type='inner')
    
    # result print
    print(json.dumps(merged_result, indent=2))