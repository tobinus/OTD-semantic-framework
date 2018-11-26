import requests
from rdflib import URIRef
from rdflib import plugin, Graph, Literal, URIRef
from rdflib.store import Store
from utils.graph import DN_SCHEMA, WN20SCHEMA, RDFS


class OrdVev:
    def __init__(self):
        self.graph = Graph()
        self.wordgraph = Graph()
        self.sensesgraph = Graph()
        self.wordgraph.parse('ordvev/rdf/words.rdf')
        self.sensesgraph.parse('ordvev/rdf/wordsenses.rdf')
        self.graph.parse('ordvev/rdf/synsets.rdf')
        self.graph.parse('ordvev/rdf/hyponymOf_taxonomic.rdf')

    def synsets(self, term):
        for word in self.wordgraph.subjects(WN20SCHEMA.lexicalForm,Literal(term, lang='nb')):
            for sense in self.sensesgraph.subjects(WN20SCHEMA.word, word):
                for synset in self.sensesgraph.subjects(WN20SCHEMA.containsWordSense, sense):
                    yield synset
        
    def hypernyms(self, synset):
        return self.graph.objects(synset, DN_SCHEMA.hyponymOf_taxonomic)


    def hyponyms(self, synset):
        return self.graph.subjects(DN_SCHEMA.hyponymOf_taxonomic, synset)


    def hypernyms_path(self, synset):    
        h = next(self.hypernyms(synset), None)    
        if not h is None:
            yield h
            for hyp in self.hypernyms_path(h):                    
                yield hyp

            
    def synset_name(self, synset):
        return next(self.graph.objects(synset, RDFS.label), None)


    def hypernym_path(self, node):
        d = node
        while True:
            yield d        
            d = next(self.hypernyms(d), None)
            if d is None:
                return

    def depth(self, node):
        return len([p for p in self.hypernym_path(node)])


    def least_common_subsumer(self, concept1, concept2):
        for concept_x in self.hypernym_path(concept1):
            for concept_y in self.hypernym_path(concept2):
                if concept_x == concept_y:
                    return concept_x
        return None


    def sim_wup(self, word1, word2):
        """
        Wu&Palmer edge-based similarity 
        """
        s = []
        for w1 in self.synsets(word1):
            for w2 in self.synsets(word2):    
                lcs = self.least_common_subsumer(w1, w2)
                if lcs:
                    score = 2.0 * float(self.depth(lcs)) / float(self.depth(w1) + self.depth(w2))
                    s.append((score, w1, w2))

        s.sort(key=lambda tup: tup[0], reverse=True)
        if s:
            return (s[0][0])
        return 0.0
