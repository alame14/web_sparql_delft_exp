import os
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS
import urllib.parse
import json
import warnings

from metahub.url_converter import URLConverter


# =============================================================================
# Namespace/schema Definitions
# =============================================================================

FILE_PATH = os.path.abspath(__file__)
FILE_DIR = os.path.dirname(FILE_PATH)

SCHEMA = Namespace("https://schema.org/")
NS1 = Namespace("http://schema.org/")
MD = Namespace("http://mekano.org/")
SCHEMA_FILE_PATH = f"{FILE_DIR}/schemaorg_schema_27_02.ttl"


# =============================================================================
# GraphBuilder Class
# =============================================================================

class GraphBuilder:
    
    # -------------------------------------------------------------------------
    # Constructor
    # -------------------------------------------------------------------------
    
    def __init__(self):
        self.graph = Graph()
        self.graph.bind("schema", SCHEMA)
        self.graph.bind("md", MD)
        # self.schema_classes = self._load_schema_org_classes(SCHEMA_FILE_PATH)
        self.url_converter = URLConverter(cache_enabled=True)
        
        
    def _load_schema_org_classes(self, schema_file_path):
        schema_classes = set()
        schema_graph = Graph()
        schema_graph.parse(schema_file_path, format='turtle')
        for s, p, o in schema_graph.triples((None, RDF.type, RDFS.Class)):
            schema_classes.add(URIRef(s))
        return schema_classes

    # -------------------------------------------------------------------------
    # Accesor
    # -------------------------------------------------------------------------

    def get_graph(self):
        return self.graph


    # -------------------------------------------------------------------------
    # Update Methods
    # -------------------------------------------------------------------------
    
    # ***** URL adding *****
    
    def add_url(self, url):
        webpage = self.url_converter.url_to_uriref(url)   # self._url_to_uriref(url)
        self.graph.add((webpage, RDF.type, SCHEMA["WebSite"]))
        self.graph.add((webpage, SCHEMA["url"], Literal(url)))
        

    def add_contains_thing(self, url, things):
        webpage = self.url_converter.url_to_uriref(url)   # self._url_to_uriref(url)
        for thing in things:
            if isinstance(thing, str) and (thing.startswith("http://") or thing.startswith("https://")):
                self.graph.add((webpage, MD.containsThing, URIRef(thing)))
            else:
                self.graph.add((webpage, MD.containsThing, Literal(thing)))
    
    
    def add_contains_word(self, url, words):
        webpage = self.url_converter.url_to_uriref(url)   # self._url_to_uriref(url)
        for word in words:
            self.graph.add((webpage, MD.containsWord, Literal(word)))


    # ***** Microdata adding *****

    def add_json_microdata(self, url, json_microdata):
        json_microdata = self._check_json_microdata(json_microdata)
        webpage_uriref = self.url_converter.url_to_uriref(url)   # self._url_to_uriref(url)
        self._add_json_ld(webpage_uriref, [json_microdata])

    def _check_json_microdata(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "target" and isinstance(value, str):
                    data[key] = self._check_uri(value)
                elif isinstance(value, (dict, list)):
                    self._check_json_microdata(value)
        elif isinstance(data, list):
            for item in data:
                self._check_json_microdata(item)
        return data
                
    def _check_uri(self, uri):
        if "?" in uri:
            base, query = uri.split("?", 1)
            query = urllib.parse.quote_plus(query)
            return f"{base}?{query}"
        return uri

    def _add_json_ld(self, webpage, json_ld_data):
        for item in json_ld_data:
            if isinstance(item, dict):
                json_ld_str = json.dumps(item)
                print('*************************')
                temp_graph = Graph().parse(data=json_ld_str, format='json-ld')
                # Ajouter tous les triplets du graphe temporaire au graphe principal
                self.graph += temp_graph
                print(len(temp_graph))
    
                # Ajouter les liens vers les microdonnées si `s` a un type RDF
                for s in temp_graph.subjects(RDF.type, None):
                    self.graph.add((webpage, MD.hasMicrodata, s))
                # for s, p, o in temp_graph:
                #     print(s, p, o)
                #     print(len(self.graph))
                #     self.graph.add((s, p, o))
                #     print(len(self.graph))
                #     if (s, RDF.type, None) in temp_graph:
                #         self.graph.add((webpage, MD.hasMicrodata, s))
                self._fix_schema_prefix_error()
               


    def _add_json_ld(self, webpage: URIRef, json_ld_data: list):
        """
        Ajoute les données JSON-LD au graphe RDF, en ignorant les éléments mal encodés.
    
        Les microdatas principales sont identifiées comme les sujets avec un type RDF explicite
        qui ne sont pas déjà des objets dans le graphe final.
    
        Args:
            webpage (URIRef): L'URI de la page web associée.
            json_ld_data (list): Liste des objets JSON-LD à traiter.
        """
        microdata_index = 0  # Initialiser l'index pour les URI explicites

        for item in json_ld_data:
            if isinstance(item, dict):
                try:
                    with warnings.catch_warnings(record=True) as caught_warnings:
                        warnings.simplefilter("always")
                        json_ld_str = json.dumps(item)
                        temp_graph = Graph().parse(data=json_ld_str, format='json-ld')
    
                        if caught_warnings:
                            warning_messages = [str(warning.message) for warning in caught_warnings]
                            print(f"Warning lors du traitement de l'élément JSON-LD : {warning_messages}")
                            continue
                        
                        # Ajouter les triplets au graphe principal
                        for s, p, o in temp_graph:
                            self.graph.add((s, p, o))
                        
                        # Identifier les sujets avec un type RDF explicite
                        subjects_with_type = {
                            s for s in temp_graph.subjects() if (s, RDF.type, None) in temp_graph
                        }
    
                        # Ajouter le triplet pour les microdatas principales
                        existing_objects = set(self.graph.objects())
                        for s in subjects_with_type:
                            if s not in existing_objects:
                                self.graph.add((webpage, MD.hasMicrodata, s))
                                
                        # for s in subjects_with_type:
                        #     if s not in existing_objects:
                        #         # Générer l'URI explicite
                        #         microdata_uri = URIRef(f"{webpage}/microdata/{microdata_index}")
                        #         microdata_index += 1
                                
                        #         # Ajouter le triplet liant l'URI explicite à la microdonnée principale
                        #         self.graph.add((webpage, MD.hasMicrodata, microdata_uri))
                        #         self.graph.add((microdata_uri, MD.represents, s))
                        
                        # Identifier les sujets avec un type RDF explicite
                        
                        # subjects_with_type = {
                        #     s for s in temp_graph.subjects() if (s, RDF.type, None) in temp_graph
                        # }
                        
                        # existing_objects = set(temp_graph.objects())
                        
                        # microdata_list = []
                        # for s in subjects_with_type:
                        #     # Générer l'URI explicite
                        #     microdata_uri = URIRef(f"{webpage}/microdata/{microdata_index}")
                        #     microdata_list.append(microdata_uri)
                        #     microdata_index += 1
                            
                        #     # Copier tous les triplets du sujet principal en remplaçant `s` par `microdata_uri`
                        #     for p, o in temp_graph.predicate_objects(subject=s):
                        #         self.graph.add((microdata_uri, p, o))
                            
                        #     # Ajouter le type à l'URI explicite (si présent dans le graphe temporaire)
                        #     for o in temp_graph.objects(subject=s, predicate=RDF.type):
                        #         self.graph.add((microdata_uri, RDF.type, o))
                                
                        #     if s not in existing_objects:
                        #         self.graph.add((webpage, MD.hasMicrodata, microdata_uri))
                            
                        # Lier la page web à l'URI explicite
                        # existing_objects = set(self.graph.objects())
                        # for microdata_uri in microdata_list:
                        #     if microdata_uri not in existing_objects:
                        #         self.graph.add((webpage, MD.hasMicrodata, microdata_uri))
                                                                        
                        # Correction des erreurs éventuelles sur les préfixes du schéma
                        self._fix_schema_prefix_error()
    
                except Exception as e:
                    print(f"Erreur lors de l'analyse d'un élément JSON-LD : {e}")
                continue


                        
    def _fix_schema_prefix_error(self):
        for s, p, o in self.graph.triples((None, None, None)):
            if isinstance(p, URIRef) and str(p).startswith("http://schema.org/"):
                self.graph.remove((s, p, o))
                fixed_p = URIRef(str(p).replace("http://schema.org/", "https://schema.org/"))
                self.graph.add((s, fixed_p, o))
            if isinstance(o, URIRef) and str(o).startswith("http://schema.org/"):
                self.graph.remove((s, p, o))
                fixed_o = URIRef(str(o).replace("http://schema.org/", "https://schema.org/"))
                self.graph.add((s, p, fixed_o))


    # ***** Refinement *****

    def declare_classes_and_properties(self):  
        declaration_graph = Graph()
        
        for subj, pred, obj in self.graph:
            if pred == RDF.type:
                declaration_graph.add((obj, RDF.type, RDFS.Class))
            declaration_graph.add((pred, RDF.type, RDF.Property))
        
        self.graph += declaration_graph


    # -------------------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------------------
    
    def run_query(self, query):
        try:
            result = self.graph.query(query)
        except Exception as e:
            print(f"An error occurred while running query: {e}")
            return None
        else:
            return result
    
    def save_graph(self, file_path, format="turtle"):
        try:
            self.graph.serialize(destination=file_path, format=format)
        except Exception as e:
            print(f"An error occurred while saving the graph: {e}")

    def serialize_graph(self, format="turtle"):
        return self.graph.serialize(format=format)
    
    def merge_graph(self, other_graph):
        self.graph += other_graph

    def merge_with_builder(self, other_builder):
        self.merge_graph(other_builder.get_graph())


    # -------------------------------------------------------------------------
    # Helpful Method(s)
    # -------------------------------------------------------------------------   
            
    # def _url_to_uriref(self, url: str) -> URIRef:
    #     """
    #     Convertit une URL en URIRef après validation et encodage des composants problématiques.
    
    #     Cette méthode gère également les cas où des accolades '{}' sont utilisées dans le chemin,
    #     comme pour des modèles d'URL dynamiques.
    
    #     Args:
    #         url (str): L'URL à valider et encoder.
    
    #     Returns:
    #         URIRef: L'URI validé et encodé.
    
    #     Raises:
    #         ValueError: Si l'URL est invalide ou si une erreur survient lors du traitement.
    #     """
    #     if not isinstance(url, str) or not url.strip():
    #         raise ValueError("L'argument 'url' doit être une chaîne non vide.")
    
    #     try:
    #         # Analyse de l'URL
    #         parsed_url = urlparse(url)
            
    #         # Vérification des composants essentiels
    #         if not parsed_url.scheme or not parsed_url.netloc:
    #             raise ValueError(f"L'URL '{url}' est invalide. Schéma ou netloc manquant.")
            
    #         # Encodage des composants
    #         encoded_path = quote(parsed_url.path, safe="/{}")  # On inclut '{}' comme sûr pour les modèles
    #         encoded_query = quote(parsed_url.query, safe="=&")
    #         encoded_params = quote(parsed_url.params, safe="")
    
    #         # Reconstruction de l'URL encodée
    #         sanitized_url = urlunparse((
    #             parsed_url.scheme,
    #             parsed_url.netloc,
    #             encoded_path,
    #             encoded_params,
    #             encoded_query,
    #             parsed_url.fragment
    #         ))
    
    #         # Conversion en URIRef
    #         return URIRef(sanitized_url)
    
    #     except ValueError as ve:
    #         raise ValueError(f"Erreur de validation pour l'URL '{url}': {ve}")
    #     except Exception as e:
    #         raise ValueError(f"Erreur inattendue lors du traitement de l'URL '{url}': {e}")




# =============================================================================
#  Base Use Test
# =============================================================================

def test_1():
    builder = GraphBuilder()
    
    url = "https://url-test.fr"
    json_microdata = {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "TEST",
                "url": "https://url-test.fr",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://url-test.fr/img/logo.png"
                }
            }
    
    builder.add_url(url)
    builder.add_json_microdata(url, json_microdata)
    
    print("\n -- Built Graph: ", builder.serialize_graph())


def test_2():
    builder = GraphBuilder()
    
    url = "https://url-test.fr"
    json_microdata = {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "TEST",
                "url": "https://url-test.fr",
                "potentialAction": {
                            "@type": "SearchAction",
                            "target": "https://bourgoisediteur.fr/?s={search_term_string}",
                            "query-input": "required name=search_term_string"
                        }
            }
    
    builder.add_url(url)
    builder.add_json_microdata(url, json_microdata)
    
    print("\n -- Built Graph: ", builder.serialize_graph())


def test_3():
    builder = GraphBuilder()
    
    url = 'https://www.wordplays.com/crossword-solver/"Baudolino"-author'
    json_microdata = {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "TEST",
                "url": "https://url-test.fr",
                "potentialAction": {
                            "@type": "SearchAction",
                            "target": "https://bourgoisediteur.fr/?s={search_term_string}",
                            "query-input": "required name=search_term_string"
                        }
            }
    
    builder.add_url(url)
    builder.add_json_microdata(url, json_microdata)
    
    print("\n -- Built Graph: ", builder.serialize_graph())
    

if __name__ == "__main__":
    print("\n ***** GraphBuilder Use Test ***** \n")  
    
    test_1()
    test_2()
    test_3()
    
    
