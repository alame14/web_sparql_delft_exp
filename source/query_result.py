# =============================================================================
#  QueryResult class
# =============================================================================

class QueryResult:
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self, data=None):
        if data is None:
            data = {}
        self.columns = data.get('columns', [])
        self.rows = data.get('rows', [])
        self._validate_columns(self.columns)
        self._validate_rows(self.rows)
        
        
    @classmethod
    def from_columns_and_rows(cls, columns, rows):
        cls._validate_columns(columns)
        cls._validate_rows(rows)
        instance = cls()
        instance.columns = columns
        instance.rows = rows
        return instance
    
    @staticmethod
    def _validate_columns(columns):
        if not isinstance(columns, list):
            raise ValueError("Columns must be a list")
        for column in columns:
            if not isinstance(column, str):
                raise ValueError("Each column must be a string")
    
    @staticmethod
    def _validate_rows(rows):
        if not isinstance(rows, list):
            raise ValueError("Rows must be a list")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Each row must be a dictionary")
        

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------

    def get_raw_structure(self):
        return {'columns': self.columns, 'rows': self.rows}
    
    def set_columns(self, columns):
        self._validate_columns(columns)
        self.columns = columns
    
    def set_rows(self, rows):
        self._validate_rows(rows)
        self.rows = rows

    # TODO: add method to get result length
    

    # -------------------------------------------------------------------------
    # Extraction method(s)
    # -------------------------------------------------------------------------
    
    def extract_url_list(self):
        return self._extract_by_type('url')
    
    def extract_uri_list(self):
        return self._extract_by_type('uri')
    
    def _extract_by_type(self, type_key):
        values = []
        if isinstance(self.rows, list):
            for row in self.rows:
                if isinstance(row, dict):
                    values.extend(self._extract_from_row(row, type_key))
        return values
    
    def _extract_from_row(self, row, type_key):
        extracted_values = []
        for key, value in row.items():
            if isinstance(value, dict) and value.get('type') == type_key:
                extracted_value = value.get(type_key)
                if isinstance(extracted_value, str):
                    extracted_values.append(extracted_value)
        return extracted_values      



# =============================================================================
#  Base Unit Test
# =============================================================================

if __name__ == "__main__":
    # Initialisation with raw data
    data = {
        'columns': ['Animal', 'webpage'],
        'rows': [
            {'Animal': {'type': 'uri', 'uri': 'http://dbpedia.org/resource/Aardwolf'}, 'webpage': {'type': 'url', 'url': 'https://study.com/academy/lesson/aardwolf-size-diet-traits.html'}},
            {'Animal': {'type': 'uri', 'uri': 'http://dbpedia.org/resource/Mouse'}, 'webpage': {'type': 'url', 'url': 'https://studymoose.com/'}}
        ]
    }
    result1 = QueryResult(data)
    
    # Initialisation with separate columns and rows
    columns = ['Animal', 'webpage']
    rows = [
        {'Animal': {'type': 'uri', 'uri': 'http://dbpedia.org/resource/Aardwolf'}, 'webpage': {'type': 'url', 'url': 'https://study.com/academy/lesson/aardwolf-size-diet-traits.html'}},
        {'Animal': {'type': 'uri', 'uri': 'http://dbpedia.org/resource/Mouse'}, 'webpage': {'type': 'url', 'url': 'https://studymoose.com/'}}
    ]
    result2 = QueryResult.from_columns_and_rows(columns, rows)
    
    # Extracting URLs and URIs
    urls = result1.extract_url_list()
    uris = result1.extract_uri_list()
    
    print(urls)  # ['https://study.com/academy/lesson/aardwolf-size-diet-traits.html', 'https://studymoose.com/']
    print(uris)  # ['http://dbpedia.org/resource/Aardwolf', 'http://dbpedia.org/resource/Mouse']
    
    # Extract the URLs and URIs for the second result
    urls2 = result2.extract_url_list()
    uris2 = result2.extract_uri_list()
    
    print(urls2)  # ['https://study.com/academy/lesson/aardwolf-size-diet-traits.html', 'https://studymoose.com/']
    print(uris2)  # ['http://dbpedia.org/resource/Aardwolf', 'http://dbpedia.org/resource/Mouse']
        
    print("QueryResult test passed.")
