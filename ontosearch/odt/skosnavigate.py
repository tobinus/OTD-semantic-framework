from rdflib import Graph, URIRef, BNode, Literal
from rdflib import Namespace
from rdflib.namespace import RDF, RDFS, OWL, DC, FOAF, XSD, SKOS


ODT = Namespace('http://www.quaat.com/ontologies#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCT = Namespace('http://purl.org/dc/terms/')
ODTX = Namespace('http://www.quaat.com/ontology/ODTX#')
QEX = Namespace('http://www.quaat.com/extended_skos#')
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')

def first(xs):
    """
        Returns the first element of a list, or None if the list is empty
    """
    if not xs:
        return None
    return xs[0]


def second(xs):
    """
        Returns the second element of a list, or None if the list is empty
    """
    if not xs:
        return None
    return xs[1]


class SKOSNavigate:
    """
    Helper class to navigate and search in a SKOS-based ontology
    """
    def __init__(self, graph):
        self.graph = graph


    def find_root(self):
        # Assuming we have at least one concept scheme
        scheme = next(self.graph.subjects(RDF.type, SKOS.ConceptScheme))

        # Assuming only one top level node
        node = next(self.graph.subjects(SKOS.topConceptOf, scheme))
        return node


    def concepts(self):
        return self.graph.subjects(RDF.type, SKOS.Concept)


    def linked_concepts(self, dataset):
        return self.graph.objects(dataset, SKOS.relatedMatch)


    def datasets(self):
        return self.graph.subjects(RDF.type, DCAT.Dataset)


    def concepts_label(self):
        for concept in self.concepts():
            label = str(second(first(self.graph.preferredLabel(concept, lang='en'))))
            yield label

    def pref_and_alt_labels(self, concept):
        pref = [p for p in self.graph.objects(concept, SKOS.prefLabel) if p.language == 'en']
        alt  = [l for l in self.graph.objects(concept, SKOS.altLabel) if l.language == 'en']
        return pref+alt

    def find_parents(self, node):
        return self.graph.objects(node, SKOS.broader)


    def find_children(self, node):
        return self.graph.subjects(SKOS.broader, node)


    def find_siblings(self, node):
        for parent in self.find_parents(node):
            for child in self.find_children(parent):
                if child != node:
                    yield child


    def find_all_children(self, node):
        ns = [node]
        for n in self.graph.subjects(SKOS.broader, node):
            ns = ns + self.find_all_children(n)
        return ns


    def parent_path(self, node):
        d = node
        while True:
            yield d
            try:
                d = next(self.find_parents(d))
            except:
                return


    def depth(self, node):
        return len([p for p in self.parent_path(node)])


    def least_common_subsumer(self, concept1, concept2):
        for concept_x in self.parent_path(concept1):
            for concept_y in self.parent_path(concept2):
                if concept_x == concept_y:
                    return concept_x
        return None


    def sim_wup(self, concept1, concept2):
        lcs = self.least_common_subsumer(concept1, concept2)
        return 2.0 * float(self.depth(lcs)) / float((self.depth(concept1) + self.depth(concept2)))
