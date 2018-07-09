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
        for subtree in tree.subtrees(filter = lambda t: t.label()=='NP'):
            leaf = subtree.leaves()            
            term = [self.normalize(w) for w,t in leaf if self.acceptable(w)]
            yield term
            
    def search(self, sentence):
        terms = self.extract_terms(sentence)
        for term in terms:
            for word in term:
                yield word
        
