from time import time
import os
from collections import Counter
from nltk.tag import StanfordNERTagger
import nltk
nltk.internals.config_java(options='-xmx6g')
from collections import Counter
from nltk.collocations import *
import itertools
from itertools import groupby
from nltk.corpus import stopwords

class Analyzer(object):
    def __init__(self):
        self.word_frequencies = None
        self.named_entities = []
        self.stopwords = nltk.corpus.stopwords.words('german')
        self.stopwords.extend(nltk.corpus.stopwords.words('english'))
        self.stopwords.extend(
            ["==", "===", "====", "s.", "dass", "the", "of", "de", "wurde", "**", "ab", "sowie", "etwa", "i.", '"',
             "...", "…", '“', '”', "'", "=", "»", "«", "'“'", "'„'", "'...'"])

    ### gets word frequencies, prints n most common words. Input: A list of tokenized articles ###
    def get_frequencies(self, corpus, n=20):
        counter = Counter()

        for article in corpus.values():
            counter.update(Counter(article))

        self.word_frequencies = counter
        most_frequent = counter.most_common(n)
        #print(most_frequent)
        return most_frequent

    ### Find named entities and sort them by type. Input: sentenized corpus ###
    def get_named_entities_sents(self, sents):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        #print("ner: current working directory is ", dir_path)
        ner_tagger_path = dir_path + r"/resources/stanford-ner.jar"
        german_model = dir_path + r"/resources/german.conll.hgc_175m_600.crf.ser.gz"
        #print(ner_tagger_path)
        tagger = StanfordNERTagger(german_model, ner_tagger_path, encoding="UTF-8")  # iso-8859-15
        tagger.java_options = '-mx2048 -Xmx2048m -Xms2048m'
        nltk.internals.config_java(options='-xmx2G')

        print("Running named entity recognition on sentences")
        t0 = time()

        self.named_entities = tagger.tag_sents(sents)
        print(len(self.named_entities), " named entitites found")

        print("done in %0.3fs" % (time() - t0))
        return self.sort_named_entities()


    ### helper function: Take the list of named entities and create a dict with all named entities of a type (location, person, organization, miscellaneous) and its frequency ###
    def sort_named_entities(self):
        print("Counting and sorting the named entities...")
        t0 = time()

        entities = []
        entities_grouped = groupby(self.named_entities, lambda x: x[1])
        for tag, chunk in entities_grouped:
            if tag != "O":
                chunk = tuple((" ".join(w for w, t in chunk), tag))
                if "," in chunk[0]:
                    chunks = chunk[0].split(",")
                    [entities.append((c.strip(), tag)) for c in chunks if c != '']
                else:
                    entities.append(chunk)

        named_entity_list = [[], [], [], []]
        tags = {"I-LOC": 0, "I-PER": 1, "I-ORG": 2, "I-MISC": 3, "B-LOC": 0, "B-PER":1, "B-ORG": 2, "B-MISC":3}

        [named_entity_list[tags[word[1]]].append(word[0]) for word in entities if word[1] is not 'O'] #for word in sentence
        counts = []
        [counts.append(Counter(list)) for list in named_entity_list]
        self.named_entities = counts

        #for counter in self.named_entities:
            #print(counter.most_common(5))

        print("done in %0.3fs" % (time() - t0))
        return self.named_entities


    def find_ngrams(self, tokenized_corpus, bigrams=True, trigrams=True, min_frequency=100, n_best=20):
        print("Finding ngrams...")

        all_docs = list(itertools.chain.from_iterable(tokenized_corpus.values()))
        ngrams = {}

        if bigrams is True:
            print("Analyzing bigrams...")
            t0 = time()
            bigram_measures = nltk.collocations.BigramAssocMeasures()
            finder = BigramCollocationFinder.from_words(all_docs)
            bigrams = self.analyze_ngrams(finder, bigram_measures, min_frequency, n_best)
            ngrams["bigrams"] = bigrams
            print("done in %0.3fs" % (time() - t0))

        if trigrams is True:
            print("Analyzing trigrams...")
            t0 = time()
            trigram_measures = nltk.collocations.TrigramAssocMeasures()
            finder = TrigramCollocationFinder.from_words(all_docs)
            trigrams = self.analyze_ngrams(finder, trigram_measures, min_frequency, n_best)
            ngrams["trigrams"] = trigrams
            print("done in %0.3fs" % (time() - t0))
        return ngrams

    def analyze_ngrams(self, finder, measure, min_frequency, n_best):
        print("Best-ranked ngrams")
        finder.apply_freq_filter(min_frequency)
        finder.apply_word_filter(lambda w: w in self.stopwords)

        results = {}

        print("Chi square:")
        #print(finder.nbest(measure.chi_sq, n_best))
        results["chi_square"] = finder.nbest(measure.chi_sq, n_best)

        print("Likelihood ratio:")
        #print(finder.nbest(measure.likelihood_ratio, n_best))
        results["likelihood_ratio"] = finder.nbest(measure.likelihood_ratio, n_best)

        print("Pointwise mutual information:")
        ngrams_pmi = finder.nbest(measure.pmi, n_best)
        #print(ngrams_pmi)
        results["pmi"] = ngrams_pmi

        print("Most frequent n-grams")
        scored = finder.score_ngrams(measure.raw_freq)
        scored_list = sorted(ngram for ngram, score in scored)
        ngrams_frequent = sorted(finder.nbest(measure.raw_freq, n_best))
        #print(ngrams_frequent)
        results["most_frequent"] = ngrams_frequent
        return results




