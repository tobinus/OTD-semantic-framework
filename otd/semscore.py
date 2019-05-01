import itertools
import statistics
import pandas as pd
from nltk.corpus import wordnet as wn

class SemScore:
    def __init__(self, extractor, navigator):
        self.extractor = extractor
        self.navigator = navigator

    def score_vector(self, query, sim_threshold):
        concepts = list(self.navigator.concepts())
        scoreDataFrame = pd.DataFrame(columns=concepts)
        scoreDataFrame.loc[query] = [0]*len(concepts)

        query_synsets = self.synsets_from_query(query)

        for concept in concepts:
            labels = self.synset_sets_from_concept(concept)

            label_scores = [SemScore.calculate_score_for_label(l, query_synsets)
                            for l in labels]

            concept_score = max(filter(None, label_scores), default=0.0)
            if concept_score < sim_threshold:
                concept_score = 0.0

            scoreDataFrame.loc[query][concept] = concept_score

        return scoreDataFrame

    @staticmethod
    def calculate_score_for_label(label_words, query_synsets):
        scores = [SemScore.calculate_score_for_label_word(w, query_synsets)
                  for w in label_words]
        try:
            return statistics.harmonic_mean(filter(None, scores))
        except statistics.StatisticsError:
            return 0.0

    @staticmethod
    def calculate_score_for_label_word(label_synsets, query_synsets):
        synset_pairs = itertools.product(query_synsets, label_synsets)
        scores = [q.wup_similarity(c) for q, c in synset_pairs]
        return max(filter(None, scores), default=0.0)

    def synsets_from_query(self, q):
        return self.synsets_from_str(q)

    def synset_sets_from_concept(self, c):
        label_synsets = []
        for label in self.navigator.pref_and_alt_labels(c):
            label_synsets.append(self.synset_sets_from_str(label))
        return label_synsets

    def synsets_from_str(self, s):
        synsets = []
        for word, pos in self.extractor.search(s):
            synsets.extend(self.synsets(word, pos))
        return synsets

    def synset_sets_from_str(self, s):
        synset_sets = []
        for word, pos in self.extractor.search(s):
            synset_sets.append(self.synsets(word, pos))
        return synset_sets

    def synsets(self, word, pos):
        return wn.synsets(word, pos=self.convert_to_wn_pos(pos))

    def convert_to_wn_pos(self, pos):
        if pos.startswith('NN'):
            return wn.NOUN
        elif pos.startswith('VB'):
            return wn.VERB
        elif pos.startswith('JJ'):
            return wn.ADJ
        elif pos.startswith('RB'):
            return wn.ADV
        else:
            return None

