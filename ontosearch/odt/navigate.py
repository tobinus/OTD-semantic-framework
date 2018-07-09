from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDFS, OWL, DC, XSD, RDF

DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCT = Namespace('http://purl.org/dc/terms/')
DCTYPE = Namespace('http://purl.org/dc/dcmitype/')
ODT = Namespace('http://www.example.org/ODT#')

class GraphNavigate:
    def __init__(self, graph):        
        self.graph = graph


    def find_parents(self, node):
        """
        Search all parent items in the vocabulary are return as a list
        """
        return self.graph.objects(node, RDFS.subClassOf)


    def find_parent(self, node):
        """
        Search all parent items in the vocabulary are return as a list
        """
        return self.graph.objects(node, RDFS.subClassOf).next()

    
    def find_children(self,node):
        """
        Search all children of a given entity
        """
        return self.graph.subjects(RDFS.subClassOf, node)

    
    def find_all_children(self, node):
        """
        Recursively search and return all children
        """
        ns = [node]
        for n in self.graph.subjects(RDFS.subClassOf, node):                        
            ns = ns + self.find_all_children(n)
        return ns

    
    def find_siblings(self,node):
        """
        Find all siblings of a given entity 
        """
        for obj in self.graph.objects(node, RDFS.subClassOf):        
            for subject in self.graph.subjects(RDFS.subClassOf, obj):
                if subject != node:
                    yield subject

                    
    def parent_path(self, node):
        d = node
        while True:
            yield d
            d = next(self.graph.objects(d, RDFS.subClassOf), None)
            if d is None:
                return
            

    def depth(self, node):
        return len([p for p in self.parent_path(node)])

    
    def least_common_subsumer(self, concept1, concept2):
        """
        Search the ontology to find the least common sumsumer (common
        """
        for concept_x in self.parent_path(concept1):
            for concept_y in self.parent_path(concept2):
                if concept_x == concept_y:
                    return concept_x
        return None

    def sim_wup(self, concept1, concept2):
        """ Wu & Palmer similarity """
        score = 0.0
        lcs = self.least_common_subsumer(concept1, concept2)
        if lcs:
            score = 2.0 * float(self.depth(lcs)) / float((self.depth(concept1) + self.depth(concept2)))

        return score
