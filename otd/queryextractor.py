import nltk


class QueryExtractor:
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
        return ((self.normalize(w), pos) for w, pos in pos_tag_tokens)

    def search(self, sentence):
        return self.extract_terms(sentence)
