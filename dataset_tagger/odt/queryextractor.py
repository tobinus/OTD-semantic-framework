import nltk
from nltk.tokenize import PunktSentenceTokenizer
from nltk.corpus import wordnet as wn

class QueryExtractor:
    def __init__(self, graph):
        self.graph = graph


    def filter_question(self, question):
        switcher = {
            "where": "location",
            "when": "event",
            "how": "abstraction",
            "what": "object",
            "who": "group"
        }
        return switcher.get(question.lower(), None)


    # Filter sentences with question words
    def is_question(self, tokenized_sentence):
        tagged = nltk.pos_tag(tokenized_sentence)
        chunk_gram = r"""
        QUESTION: 
        {<WP|WR.*>+}        
        """
        chunkParser = nltk.RegexpParser(chunk_gram)
        chunked = chunkParser.parse(tagged)    
        return filter_question(chunked[0][0][0])


    def noun_phrase_chunker(self, tokenized_sentence):    
        tagged = nltk.pos_tag(tokenized_sentence)
        chunk_gram = r"""
        NP: {<[CDJNP].*>+}
        """
        chunkParser = nltk.RegexpParser(chunk_gram)
        chunked = chunkParser.parse(tagged)
        #print chunked
        nps = [w for w in chunked if isinstance(w, nltk.tree.Tree)]
        return nps


    def artifact_chunker(self, tokenized_sentence):
        tagged = nltk.pos_tag(tokenized_sentence)
        chunk_gram = r"""
        artifact: {<NN|NNS>+}
        """
        chunkParser = nltk.RegexpParser(chunk_gram)
        chunked = chunkParser.parse(tagged)    
        
        artifacts = [w for w in chunked if isinstance(w, nltk.tree.Tree)]
        return artifacts


    def search(self, query):
        tokenized_sentence = nltk.word_tokenize(query)
        isquestion = is_question(tokenized_sentence)
        nps = noun_phrase_chunker(tokenized_sentence)
        artifacts = artifact_chunker(tokenized_sentence)

        # Purely artifact-based semantics
        for artifact in artifacts:
            yield artifact[:1][0][0]
        return None
