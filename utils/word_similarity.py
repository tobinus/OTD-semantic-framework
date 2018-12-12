class WordComparator:
    def __init__(self):
        self.__corpus_instance = None

    def ensure_loaded_corpus(self):
        _ = self.compare('helicopter', 'bird')

    @property
    def _corpus_instance(self):
        if self.__corpus_instance is None:
            self.__corpus_instance = self._init_corpus()
        return self.__corpus_instance

    def compare(self, one, another):
        return self._compare_words(one, another, self._corpus_instance)

    def _init_corpus(self):
        raise NotImplementedError(
            'Method _init_corpus must be implemented by more specified word '
            'comparator.'
        )

    def _compare_words(self, one, another, corpus_instance):
        raise NotImplementedError(
            'Method _compare_words must be implemented by more specific word '
            'comparator.'
        )


class NorwegianWordComparator(WordComparator):
    def _init_corpus(self):
        from ordvev.ordvev import OrdVev
        return OrdVev()

    def _compare_words(self, one, another, corpus_instance):
        return corpus_instance.sim_wup(one, another)


class EnglishWordComparator(WordComparator):
    def _init_corpus(self):
        from nltk.corpus import wordnet
        _ = wordnet.synsets('helicopter')
        return wordnet

    def _compare_words(self, one, another, corpus_instance):
        import itertools

        one_synonyms = corpus_instance.synsets(one)
        another_synonyms = corpus_instance.synsets(another)

        valid_one_synonyms = filter(None, one_synonyms)
        valid_another_synonyms = filter(None, another_synonyms)
        all_pairs = itertools.product(
            valid_one_synonyms,
            valid_another_synonyms
        )
        similarities = map(
            lambda words: words[0].wup_similarity(words[1]),
            all_pairs
        )
        valid_similarities = itertools.filterfalse(
            lambda s: s is None,
            similarities
        )
        return max(valid_similarities, default=0.0)


LANGUAGES = {
    'nb': NorwegianWordComparator,
    'en': EnglishWordComparator,
}


def get_comparator(language):
    return LANGUAGES[language]()
