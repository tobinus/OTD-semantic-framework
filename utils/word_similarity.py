class WordComparator:
    def __init__(self):
        self.__corpus_instance = None

    def load_corpus(self):
        _ = self._corpus_instance

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

        all_pairs = itertools.product(one_synonyms, another_synonyms)
        similarities = map(
            lambda words: words[0].wup_similarity(words[1]),
            all_pairs
        )
        return max(similarities, default=0.0)


LANGUAGES = {
    'no': NorwegianWordComparator,
    'en': EnglishWordComparator,
}


def get_comparator(language):
    return LANGUAGES[language]()


def get_available_languages():
    return tuple(LANGUAGES.keys())
