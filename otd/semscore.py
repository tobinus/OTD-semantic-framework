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
            # TODO: Use caching to avoid processing concepts for each query
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
        synset_sets = self.synset_sets_from_str(s)
        return tuple(itertools.chain.from_iterable(synset_sets))

    def synset_sets_from_str(self, s):
        words = tuple(self.extractor.search(s))
        return self.synset_sets_from_words(words)

    def synset_sets_from_words(self, words):
        words = list(words)
        synset_sets = []

        def handle_grams(i):
            for gram_contents in SemScore.ngrams(words, i):
                # Don't construct connected words that didn't exist in the
                # original text. We do this by using placeholders where used
                # words used to be. Skip if we have one of those.
                if (None, None) in gram_contents:
                    continue
                gram_words = tuple(word for word, pos in gram_contents)
                combined = '_'.join(gram_words)
                synsets = self.synsets(combined, '')
                if synsets:
                    # These words have been matched, don't look up afterwards
                    for tagged_word in gram_contents:
                        try:
                            index = words.index(tagged_word)
                            # TODO: Pass indices instead of contents from ngrams, so array updates here are reflected in the next iteration while still inside of handle_grams()
                            words[index] = (None, None)
                        except ValueError:
                            # ValueError triggered by words.index; not found.
                            # The word was probably removed by an earlier ngram
                            # with the same n, so we don't need to remove it
                            # again
                            pass

                    # Add the result
                    synset_sets.append(synsets)

        handle_grams(3)
        handle_grams(2)

        # Lookup any remaining single-words
        for word, pos in words:
            if word is not None:
                synset_sets.append(self.synsets(word, pos))

        return synset_sets

    @staticmethod
    def ngrams(iterator, n):
        iterator = tuple(iterator)

        def get_ngram_at(offset):
            return tuple(iterator[offset + i] for i in range(n))

        return tuple(get_ngram_at(i) for i in range(0, (len(iterator) - n) + 1))

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

