import itertools
import nltk


class QueryExtractor:
    def __init__(self):
        chunk_gram = r"""
            NBAR:
                {<NN.*|JJ.*>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns

            NP:
                {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
                {<NBAR>}
                {<FW|VB.*|JJ.*>}  # Experiment, trying to match more
        """
        self.chunk_parser = nltk.RegexpParser(chunk_gram)

    def normalize(self, word):
        return word.lower()

    def extract_terms(self, sentence):
        tokenized_sentence = nltk.word_tokenize(sentence)

        num_tokens = len(tokenized_sentence)
        if num_tokens == 0:
            # Short circuit
            return tuple()
        elif num_tokens == 1:
            # Let WordNet use any part of speech
            token = tokenized_sentence[0]
            return [(self.normalize(token), '')]

        pos_tag_tokens = nltk.tag.pos_tag(tokenized_sentence)
        tree = self.chunk_parser.parse(pos_tag_tokens)
        np_trees = tree.subtrees(filter=lambda t: t.label() == 'NP')
        leaves_per_tree = (t.leaves() for t in np_trees)
        leaves = itertools.chain.from_iterable(leaves_per_tree)
        words_per_leaf = ((self.normalize(w), pos)
                          for w, pos in leaves)
        return words_per_leaf

    def search(self, sentence):
        # TODO: Use extract_terms() directly instead of through this
        return self.extract_terms(sentence)
