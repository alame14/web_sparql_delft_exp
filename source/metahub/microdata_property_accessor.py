import re
from rdflib import ConjunctiveGraph, URIRef


# =============================================================================
#  MicrodataPropertyAccessor Class
# =============================================================================

class MicrodataPropertyAccessor:
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
        
    def __init__(self, file_path, file_format="turtle"):
        self.file_path = file_path
        self.file_format = file_format
        self.graph = ConjunctiveGraph()
        self.blank_node_map = {}  # Mapping blank nodes identifiers to URIs
        self.microdata_property_dict = {}
        self._preprocess_and_load_graph()
        

    def _preprocess_and_load_graph(self):
        """ Pre-process the Turtle file to replace blank nodes with URIs """
        with open(self.file_path, "r") as infile:
            modified_content = []
            for line in infile:
                # Search for blank nodes in the format _:xxx
                matches = re.findall(r"(_:\w+)", line)
                for blank_node in matches:
                    if blank_node not in self.blank_node_map:
                        # Create a unique URI for each blank node and add to the mapping
                        self.blank_node_map[blank_node] = f"https://bnode.microdata.flamelis.org/{blank_node[2:]}"
                    # Replace blank node with URI in line
                    line = line.replace(blank_node, f"<{self.blank_node_map[blank_node]}>")
        
                # Write the modified line in the new file
                modified_content.append(line)
                
        # Charger le contenu modifié dans le graphe en mémoire
        self.graph.parse(data="".join(modified_content), format=self.file_format)
            
    
    # -------------------------------------------------------------------------
    # Method to update the properties dictionary
    # -------------------------------------------------------------------------
    
    def update_properties(self):
        uri_dict = self._compute_dict_with_uri_as_key()
        self._recalculate_keys_from_uri_dict(uri_dict)
        
        
    def _compute_dict_with_uri_as_key(self):
        """Intermediate dictionary with URI as key"""
        uri_dict = {}
        for s, p, o in self.graph:
            local_name = self._get_local_name(p)
            namespace = str(p).rsplit(local_name, 1)[0]
            uri_dict[str(p)] = {
                'uri': str(p),
                'namespace': namespace,
                'local_name': local_name
            }
        return uri_dict
    
    
    def _recalculate_keys_from_uri_dict(self, uri_dict):
        """Recalculate keys to ensure the uniqueness of local names"""
        self.microdata_property_dict.clear()
        for uri, details in uri_dict.items():
            local_name = details['local_name']
            key = local_name
            index = 1
            while key in self.microdata_property_dict:
                if self.microdata_property_dict[key]['uri'] == uri:
                    break
                key = f"{local_name}_{index}"
                index += 1
            self.microdata_property_dict[key] = details
            
            
    def _get_local_name(self, uri):
        """Helper method to extract the local name"""
        if '#' in uri:
            return uri.split('#')[-1]
        return uri.split('/')[-1]


    def _convert_subject(self, subject):
        """Convert subject to URIRef based on blank node mapping or treat as URI if not a blank node"""
        if not subject.startswith("http"):
            # Checks the identifier of blank node with or without underscore
            with_underscore = f"_:{subject}"
            if with_underscore in self.blank_node_map:
                return URIRef(self.blank_node_map[with_underscore])
            if subject in self.blank_node_map:
                return URIRef(self.blank_node_map[subject])
        # Treat as a regular URI
        return URIRef(subject)
    
    
    # -------------------------------------------------------------------------
    # Accessor methods
    # -------------------------------------------------------------------------
    
    def get_property_keys(self, subject=None):
        """Retrieve all property keys, optionally filtered by a subject"""
        if subject:
            subject = self._convert_subject(subject)
            return [key for key, details in self.microdata_property_dict.items()
                    if (subject, URIRef(details['uri']), None) in self.graph]
        return list(self.microdata_property_dict.keys())
    
    
    def get_property_namespace(self, key, subject=None):
        """Get the namespace of a property by its key"""
        if key in self.microdata_property_dict:
            if subject:
                subject = self._convert_subject(subject)
                if (subject, URIRef(self.microdata_property_dict[key]['uri']), None) not in self.graph:
                    return None
            return self.microdata_property_dict[key]['namespace']
        return None
    
    
    def get_property_local_name(self, key, subject=None):
        """Get the local name of a property by its key"""
        if key in self.microdata_property_dict:
            if subject:
                subject = self._convert_subject(subject)
                if (subject, URIRef(self.microdata_property_dict[key]['uri']), None) not in self.graph:
                    return None
            return self.microdata_property_dict[key]['local_name']
        return None
    
    
    def get_property_uri(self, key, subject=None):
        """Get the URI of a property by its key"""
        if key in self.microdata_property_dict:
            if subject:
                subject = self._convert_subject(subject)
                if (subject, URIRef(self.microdata_property_dict[key]['uri']), None) not in self.graph:
                    return None
            return self.microdata_property_dict[key]['uri']
        return None
    
    
    def get_properties(self, subject=None):
        """Get all properties, optionally filtered by a subject"""
        if subject:
            subject = self._convert_subject(subject)
            return {key: details for key, details in self.microdata_property_dict.items()
                    if (subject, URIRef(details['uri']), None) in self.graph}
        return self.microdata_property_dict

