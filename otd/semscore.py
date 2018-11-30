import pandas as pd
from nltk.corpus import wordnet as wn

class SemScore:
    def __init__(self, extractor, navigator):
        self.extractor = extractor
        self.navigator = navigator


    def similarity(self, word, concept):
        """
        Note that this function only considers concepts
        """
        score = 0.0
        for s0 in wn.synsets(word):
            for s1 in wn.synsets(concept):
                value = s0.wup_similarity(s1)
                if value:
                    if (value > score): 
                        score = value
        return score
    
    def score_vector(self, query):
        concepts = list(self.navigator.concepts())
        scoreDataFrame = pd.DataFrame(columns=concepts)
        scoreDataFrame.loc[query] = [0]*len(concepts)
        for artifact in self.extractor.search(query):
            for concept in concepts:
                for lbl in self.navigator.pref_and_alt_labels(concept):
                    score = self.similarity(artifact, lbl)                
                    scoreDataFrame.loc[query][concept] = max(score, scoreDataFrame.loc[query][concept])
        return scoreDataFrame
    
