from rdflib import URIRef, BNode, RDF
from urllib.parse import urlparse, urlunparse

class GraphRefiner:
    """ Class for refining the Microdata RDF graph. """
        
    # -------------------------------------------------------------------------
    # Class attribute(s) / method(s)
    # -------------------------------------------------------------------------

    BNODE_MD_URI = "https://bnode.microdata.flamelis.org/"

    def __init__(self, graph):
        self.graph = graph
        self.bnode_mapping = {}  # Mapping of original blank nodes to their new URIs
        self.converted_bnode_uris = set()  # Set of URIs that used to be blank nodes
        self.unknown_count = 0
        self.cleaned_references_count = 0
        self.renamed_uris_count = 0

    def replace_blank_nodes(self):
        """Replace all blank nodes with unique URIs and keep track of their mappings."""
        # Step 1: Identify all blank nodes and create a mapping
        for subj, pred, obj in self.graph:
            if isinstance(subj, BNode) and subj not in self.bnode_mapping:
                uri = self._generate_bnode_uri()
                self.bnode_mapping[subj] = uri
                self.converted_bnode_uris.add(uri)
            if isinstance(obj, BNode) and obj not in self.bnode_mapping:
                uri = self._generate_bnode_uri()
                self.bnode_mapping[obj] = uri
                self.converted_bnode_uris.add(uri)

        # Step 2: Replace all occurrences of blank nodes with their corresponding URIs
        for subj, pred, obj in list(self.graph):
            # Replace subject if it's a blank node
            new_subj = self.bnode_mapping.get(subj, subj)
            # Replace object if it's a blank node
            new_obj = self.bnode_mapping.get(obj, obj)
            
            # If replacements are needed, modify the graph
            if new_subj != subj or new_obj != obj:
                self.graph.remove((subj, pred, obj))
                self.graph.add((new_subj, pred, new_obj))

    def remove_unknown_typed_triples(self):
        """Remove triples where the subject has only a type <Unknown> and is in converted_bnode_uris."""
        for uri in list(self.converted_bnode_uris):
            triples = list(self.graph.predicate_objects(uri))
            if len(triples) == 1 and triples[0][0] == RDF.type and str(triples[0][1]).endswith("Unknown"):
                self.graph.remove((uri, RDF.type, triples[0][1]))
                self.unknown_count += 1

    def remove_dangling_references(self):
        """Remove triples that point to URIs of former blank nodes that have no properties."""
        for uri in list(self.converted_bnode_uris):
            if not list(self.graph.predicate_objects(uri)):
                # If the URI has no remaining triples, remove all references to it
                for subj, pred in list(self.graph.subject_predicates(uri)):
                    self.graph.remove((subj, pred, uri))
                    self.cleaned_references_count += 1

    def rename_bnode_uris(self):
        """Rename former blank node URIs to have local names as md1, md2, etc."""
        for idx, old_uri in enumerate(sorted(self.converted_bnode_uris), start=1):
            new_local_name = f"md{idx}"
            new_uri = self._replace_local_name(old_uri, new_local_name)
            
            # Replace old_uri with new_uri in the graph
            for subj, pred, obj in list(self.graph):
                if subj == old_uri:
                    self.graph.remove((subj, pred, obj))
                    self.graph.add((new_uri, pred, obj))
                if obj == old_uri:
                    self.graph.remove((subj, pred, obj))
                    self.graph.add((subj, pred, new_uri))
                    
            # Update the URI in the set and counter
            self.converted_bnode_uris.remove(old_uri)
            self.converted_bnode_uris.add(new_uri)
            self.renamed_uris_count += 1

    def _generate_bnode_uri(self):
        """Generate a unique URI for a former blank node."""
        uri = URIRef(f"{GraphRefiner.BNODE_MD_URI}{len(self.converted_bnode_uris) + 1}")
        return uri

    def _replace_local_name(self, uri, new_local_name):
        """Replace the local name of an existing URI with a new local name."""
        parsed_uri = urlparse(uri)
        new_path = f"/{new_local_name}"
        return URIRef(urlunparse((parsed_uri.scheme, parsed_uri.netloc, new_path, "", "", "")))

    def adapt_graph(self):
        """Run all refinement operations on the graph."""
        self.replace_blank_nodes()
        self.remove_unknown_typed_triples()
        self.remove_dangling_references()
        self.rename_bnode_uris()
        print(f"Graph adapted: {self.unknown_count} <Unknown> typed triples removed, {self.cleaned_references_count} dangling references cleaned, {self.renamed_uris_count} URIs renamed.")
