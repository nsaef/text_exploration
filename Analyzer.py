from time import time
from collections import Counter
from nltk.tag import StanfordNERTagger
import nltk
nltk.internals.config_java(options='-xmx6g')
from collections import Counter
from nltk.collocations import *
import itertools
from nltk.corpus import stopwords

class Analyzer(object):
    def __init__(self):
        self.word_frequencies = None
        self.named_entities = None
        self.stopwords = nltk.corpus.stopwords.words('german')
        self.stopwords.extend(
            ["==", "===", "====", "s.", "dass", "the", "of", "de", "wurde", "**", "ab", "sowie", "etwa", "i."])

    ### gets word frequencies, prints n most common words. Input: A list of tokenized articles ###
    def get_frequencies(self, corpus, n=20):
        counter = Counter()

        for article in corpus:
            counter.update(Counter(article))

        self.word_frequencies = counter
        most_frequent = counter.most_common(n)
        print(most_frequent)
        return

    ### Find named entities and sort them by type. Input: sentenized corpus ###
    def get_named_entities_sents(self, sents):
        ner_tagger_path = r"D:\Stanford Core NLP\stanford-ner-2017-06-09\stanford-ner.jar"
        german_model = r"D:\Stanford Core NLP\stanford-ner-2017-06-09\classifiers\stanford-german-corenlp-2017-06-09-models\edu\stanford\nlp\models\ner\german.conll.hgc_175m_600.crf.ser.gz"
        tagger = StanfordNERTagger(german_model, ner_tagger_path, encoding="UTF-8")  # iso-8859-15
        tagger.java_options = '-mx4096m'

        print("Running named entity recognition on sentences")
        t0 = time()

        result = tagger.tag_sents(sents)
        self.named_entities = result

        print("done in %0.3fs" % (time() - t0))

        self.sort_named_entities()
        return

    ### helper function: Take the list of named entities and create a dict with all named entities of a type (location, person, organization, miscellaneous) and its frequency ###
    def sort_named_entities(self):
        print("Counting and sorting the named entities...")
        t0 = time()

        named_entity_list = [[], [], [], []]
        tags = {"I-LOC": 0, "I-PER": 1, "I-ORG": 2, "I-MISC": 3, "B-LOC": 0, "B-PER":1, "B-ORG": 2, "B-MISC":3}

        [named_entity_list[tags[word[1]]].append(word[0]) for sentence in self.named_entities for word in sentence if word[1] is not 'O']
        counts = []
        [counts.append(Counter(list)) for list in named_entity_list]
        self.named_entities = counts

        for counter in self.named_entities:
            print(counter.most_common(50))

        print("done in %0.3fs" % (time() - t0))
        return

    def find_ngrams(self, tokenized_corpus, bigrams=True, trigrams=True, min_frequency=20, n_best=10):
        print("Finding ngrams...")

        all_docs = list(itertools.chain.from_iterable(tokenized_corpus))

        if bigrams is True:
            print("Analyzing bigrams...")
            t0 = time()
            bigram_measures = nltk.collocations.BigramAssocMeasures()
            finder = BigramCollocationFinder.from_words(all_docs)
            self.analyze_ngrams(finder, bigram_measures, min_frequency, n_best)
            print("done in %0.3fs" % (time() - t0))

        if trigrams is True:
            print("Analyzing trigrams...")
            t0 = time()
            trigram_measures = nltk.collocations.TrigramAssocMeasures()
            finder = TrigramCollocationFinder.from_words(all_docs)
            self.analyze_ngrams(finder, trigram_measures, min_frequency, n_best)
            print("done in %0.3fs" % (time() - t0))
        return

    def analyze_ngrams(self, finder, measure, min_frequency, n_best):
        print("Best-ranked ngrams")
        finder.apply_freq_filter(min_frequency)
        finder.apply_word_filter(lambda w: w in self.stopwords)

        # print("Chi square:")
        # print(finder.nbest(measure.chi_sq, n_best))
        #
        # print("Likelihood ratio:")
        # print(finder.nbest(measure.likelihood_ratio, n_best))

        print("Pointwise mutual information:")
        print(finder.nbest(measure.pmi, n_best))

        print("Most frequent n-grams")
        scored = finder.score_ngrams(measure.raw_freq)
        scored_list = sorted(ngram for ngram, score in scored)
        print(sorted(finder.nbest(measure.raw_freq, n_best)))
        return









