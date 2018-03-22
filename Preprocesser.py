from time import time
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
import nltk
from nltk.corpus import stopwords
from nltk.tag import StanfordNERTagger
import nltk.data
import string



### To add: at least stopword removal ###

class Preprocesser(object):
    def __init__(self):
        print("preprocessing...")
        self.feature_names_raw = None
        self.feature_names_tfidf = None
        self.corpus_cleaned_string = []
        self.corpus_tokenized = []
        self.corpus_sentences = []

        self.stopwords = nltk.corpus.stopwords.words('german')
        self.stopwords.extend(["==", "===", "====", "s.", "dass", "the", "of", "de", "wurde", "**", "ab", "sowie", "etwa", "i."])

    def tokenize(self, corpus, remove_stopwords=True, cs=True):
        # NLTK's default German stopwords
        self.split_sentences(corpus)

        print("running tokenize...")
        t0 = time()

        # steps apparently: tokenize using the nltk
        for article in corpus:
            #article_str = ""
            article_list = []
            sent_tokenizer = nltk.data.load("tokenizers/punkt/german.pickle")

            for sentence in sent_tokenizer.tokenize(article):
                for token in nltk.tokenize.word_tokenize(sentence):
                    if token not in string.punctuation and (remove_stopwords is False or token.lower() not in self.stopwords):
                        if cs is True:
                            article_list += [token]
                        else:
                            article_list += [token.lower()]
            self.corpus_tokenized.append(article_list)
        print("done in %0.3fs" % (time() - t0))
        return

    def split_sentences(self, corpus):
        print("splitting corpus into sentences...")
        t0 = time()

        tokenizer = nltk.data.load("tokenizers/punkt/german.pickle")

        for doc in corpus:
            test = "test"
            self.corpus_sentences.append(tokenizer.tokenize(doc)) #nltk.tokenizer.tag_sents(doc)
        print("done in %0.3fs" % (time() - t0))
        return


    def vectorize_tfidf(self, obj):
        # parameters configurable?
        print("creating tf-idf representation")

        tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2,
                                           max_features=1000,
                                           stop_words=self.stopwords)
        t0 = time()
        tfidf = tfidf_vectorizer.fit_transform(obj)
        print("done in %0.3fs." % (time() - t0))
        self.feature_names_tfidf = tfidf_vectorizer.get_feature_names()
        return tfidf

    # eventuell so anpassen, dass eine liste zurückgegeben wird: [0] ist tf_vectorizer.get_feature_names, [1] die tf-repräsentation
    def vectorize_frequencies(self, obj):
        print("creating raw frequency representation")

        tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2,
                                        max_features=1000,
                                        stop_words=self.stopwords)
        t0 = time()
        tf = tf_vectorizer.fit_transform(obj)
        print("done in %0.3fs." % (time() - t0))
        self.feature_names_raw = tf_vectorizer.get_feature_names()
        return tf
