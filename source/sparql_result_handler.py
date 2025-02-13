from requests.models import Response
import xml.etree.ElementTree as ET
from xml.dom import minidom

from rdflib import Variable



class SPARQLResultHandler:
     
    @staticmethod
    def remove_null_values(data):
        for row in data['rows']:
            keys_to_remove = [key for key, value in row.items() if value is None]
            for key in keys_to_remove:
                del row[key]
        return data
    
     
    @staticmethod
    def remove_null_rows(data):
        """
        Supprime les lignes qui contiennent au moins une valeur None.
        """
        filtered_rows = [
            row for row in data['rows']
            if all(value is not None for value in row.values())
        ]
        return {"columns": data["columns"], "rows": filtered_rows}

    
    @staticmethod
    def dict_to_sparql_xml(data):
        if not SPARQLResultHandler._is_valid_dict(data):
            raise ValueError("Invalid dictionary format")
    
        sparql = ET.Element('sparql', xmlns="http://www.w3.org/2005/sparql-results#")
        
        # Create head element
        head = ET.SubElement(sparql, 'head')
        for col in data['columns']:
            ET.SubElement(head, 'variable', name=col)
        
        # Create results element
        results = ET.SubElement(sparql, 'results', distinct="false", ordered="true")
        for row in data['rows']:
            result = ET.SubElement(results, 'result')
            for col, value in row.items():
                binding = ET.SubElement(result, 'binding', name=col)
                uri = ET.SubElement(binding, 'uri')
                uri.text = value['value']
        
        # Convert the ElementTree to a string
        rough_string = ET.tostring(sparql, 'utf-8')
        
        # Parse the rough string into a DOM
        reparsed = minidom.parseString(rough_string)
        
        # Return a pretty-printed XML string
        pretty_xml = reparsed.toprettyxml(indent="  ")
        return pretty_xml
    
    @staticmethod
    def _is_valid_dict(data):
        if isinstance(data, dict):
            if 'columns' in data and 'rows' in data:
                if isinstance(data['columns'], list) and all(isinstance(col, str) for col in data['columns']):
                    if isinstance(data['rows'], list) and all(isinstance(row, dict) for row in data['rows']):
                        return True
        return False
    
    @staticmethod
    def create_response_from_xml(xml_data, status_code=200, headers=None):
        if headers is None:
            headers = {'Content-Type': 'application/xml'}
        
        response = Response()
        response.status_code = status_code
        response.headers = headers
        response._content = xml_data.encode('utf-8')  # Convert XML string to bytes
        response.encoding = 'utf-8'
        
        return response
    
    
    
    @staticmethod
    def is_valid_result_xml(result):
        if isinstance(result, (bytes, str)):
            try:
                # print('----- try to parse the result data as XML')
                root = ET.fromstring(result)
                return root.tag == "{http://www.w3.org/2005/sparql-results#}sparql"
            except ET.ParseError:
                return False
        return False

    @staticmethod
    def is_valid_result_dict(data):
        if isinstance(data, dict):
            if 'columns' in data and 'rows' in data:
                if isinstance(data['columns'], list) and all(isinstance(col, str) for col in data['columns']):
                    if isinstance(data['rows'], list) and all(isinstance(row, dict) for row in data['rows']):
                        return True
        return False        
   
    
    @staticmethod        
    def convert_result_xml_to_dict(result_xml):
        try:
            # print('----- convert result xml to result dict')
            # print('----- result_xml: ', result_xml)
            
            # Parse the XML data
            root = ET.fromstring(result_xml)
            
            # Extract column names from the <head> section
            columns = []
            for variable in root.find("{http://www.w3.org/2005/sparql-results#}head"):
                columns.append(variable.attrib['name'])
            
            # Extract rows from the <results> section
            rows = []
            for result in root.find("{http://www.w3.org/2005/sparql-results#}results"):    
                row = {}
                for binding in result:
                    name = binding.attrib['name']
                    uri = binding.find("{http://www.w3.org/2005/sparql-results#}uri")
                    if uri is not None:
                        row[name] = {'type': 'uri', 'value': uri.text}
                rows.append(row)  
            
            # Create the final dictionary
            result_dict = {
                'columns': columns,
                'rows': rows
            }            
            
            return result_dict
                
        except Exception as e:
            print(f'----- (!) Exception ({str(e)})')
            raise Exception(f'SPARQLResultHandler.convert_result_xml_to_dict >> {str(e)}')
            
    
    @staticmethod   
    def convert_columns(data):
        columns = [str(col) if isinstance(col, Variable) else col for col in data['columns']]
        # columns = [col.lower() for col in columns]
        result = {
            'columns': columns,
            'rows': []
        }
        
        for row in data['rows']:
            new_row = {}
            for key, value in row.items():
                new_key = str(key) if isinstance(key, Variable) else key
                # new_key = new_key.lower()
                new_row[new_key] = value
            result['rows'].append(new_row)
        
        return result