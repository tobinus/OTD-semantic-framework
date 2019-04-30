import itertools
import nltk
from nltk.corpus import stopwords


class QueryExtractor:
    def __init__(self):
        chunk_gram = r"""
            COMBN: 
                {<VB.*>+<NN.*>}     # Verbs and Nouns

            NBAR:
                {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns

            NP:
                {<NBAR>}
                {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
                {<COMBN>}
                {<FW|VB.*|JJ.*>}  # Experiment, trying to match more
        """
        self.lemmatizer = nltk.WordNetLemmatizer()        
        self.chunk_parser = nltk.RegexpParser(chunk_gram) 
        self.stopwords = stopwords.words('english')
        
    def acceptable(self, word):        
        return word.lower() not in self.stopwords
    
    def normalize(self, word):                
        return self.lemmatizer.lemmatize(word.lower())
    
    def extract_terms(self, sentence):
        tokenized_sentence = nltk.word_tokenize(sentence)
        pos_tag_tokens = nltk.tag.pos_tag(tokenized_sentence)
        tree = self.chunk_parser.parse(pos_tag_tokens)
        np_trees = tree.subtrees(filter=lambda t: t.label() == 'NP')
        leaves_per_tree = (t.leaves() for t in np_trees)
        leaves = itertools.chain.from_iterable(leaves_per_tree)
        words_per_leaf = ((self.normalize(w), pos)
                          for w, pos in leaves if self.acceptable(w))
        return words_per_leaf

    def search(self, sentence):
        return self.extract_terms(sentence)
