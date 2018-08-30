from django import template
from django.conf import settings
from django.templatetags.static import static
from django.core.exceptions import ObjectDoesNotExist
from CollectionExplorer.models import Collection, Entity, Ngram
from CollectionExplorer.tasks import *
#from Preprocesser import Preprocesser
from Analyzer import Analyzer
#from DocEmbedder import DocEmbedder
from TopicModeller import TopicModeller
from Clusterer import Clusterer
import pickle
import os
from time import time

register = template.Library()

static_path = settings.BASE_DIR + "/CollectionExplorer" + static("CollectionExplorer/")
corpora_path = static_path + "corpora/"
model_path = static_path + "models/"

@register.simple_tag
def check_corpus_status(collection_id, type, name=None):
    id = str(collection_id)
    if type == "index":
        dir = static_path + type + "/" + id
        return os.path.exists(dir) and len(os.listdir(dir)) > 0
    else:
        if type == "corpora":
            path = static_path + type + "/" + id + "/" + id +"_" + name + ".corpus"
        else:
            path = static_path + type + "/" + id + ".model"
        return os.path.exists(path)


@register.simple_tag
def process_collection(collection, raw_frequencies=False, tokens=False, sents=False, tf_idf=False, cs=True, remove_stopwords=False, async=False):
    name = get_filename(collection.id, tokens, sents, tf_idf, cs, remove_stopwords, raw_frequencies)
    folder_path = corpora_path + str(collection.id)

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    if os.path.exists(folder_path + "/" + name) and async is False:
        corpus = pickle.load(open(folder_path + "/" + name, "rb"))

    else:
        corpus = None
        path = folder_path + "/" + name
        features_path = None
        docs = list(collection.documents.values_list("id", "content"))

        if raw_frequencies:
            features_path = folder_path + "/" + name + ".features"

        process_collection_async.delay(docs, path, tokens, sents, raw_frequencies, tf_idf, remove_stopwords, cs, features_path=features_path) #
    return corpus


def get_filename(id, tokens, sents, tf_idf, cs, remove_stopwords, raw_frequencies):
    name = str(id)
    if sents:
        name += "_sents.corpus"
        return name
    elif tokens:
        name += "_tokens"
    elif raw_frequencies:
        name += "_rf"
    elif tf_idf:
        name += "_tf-idf"
    if remove_stopwords:
        name += "_stopwords-excluded"
    else:
        name += "_stopwords-included"
    if cs:
        name += "_cs"
    else:
        name += "_ci"
    name += ".corpus"
    return name


@register.simple_tag
def get_highest_freq_words(id, n=50):
    name = str(id) + "_tokens_stopwords-excluded_cs.corpus"
    corpus_tokenized =  pickle.load(open(corpora_path + str(id) + "/" + name, "rb"))

    analyzer = Analyzer()
    return analyzer.get_frequencies(corpus_tokenized, n)


@register.simple_tag
def get_named_entities(id, n=20):
    get_named_entities_async.delay("collection", id, corpora_path)
    return


@register.simple_tag
def get_doc2vec_model(collection, recreate=False):
    model_file = model_path + str(collection.id) + ".model"
    if os.path.isfile(model_file) and recreate is False:
       return get_doc2vec_model_async(model_path, str(collection.id))
    elif os.path.isfile(model_file) and recreate is True:
        models = os.listdir(model_path)
        needle = str(collection.id) + ".model"
        del_list = [m for m in models if m.startswith(needle)]
        for f in del_list:
            os.remove(model_path + f)
        print("removed old model")
    return get_doc2vec_model_async.delay(model_path, str(collection.id), corpora_path)
    #return model


@register.simple_tag
def find_ngrams(collection, bigrams=True, trigrams=True):
    id = str(collection.id)
    corpus_path = corpora_path + id + "/" + id + "_tokens_stopwords-excluded_cs.corpus"

    get_ngrams_async.delay(collection.id, corpus_path, bigrams, trigrams)
    return


@register.simple_tag
def create_topic_models(collection, n_topics=30):
    id = str(collection.id)
    corpus_path = corpora_path + id + "/" + id + "_rf_stopwords-included_cs.corpus"
    feature_path =corpus_path + ".features"

    corpus_rf = pickle.load(open(corpus_path, "rb"))
    feature_names = pickle.load(open(feature_path, "rb"))
    #corpus = list(collection.documents.values_list("content", flat=True))
    docs = list(collection.documents.values_list("id", flat=True))

    lda = TopicModeller(n_topics=n_topics)
    lda.create_topic_models(corpus_rf, feature_names) #randomstate? currently 0
    topic_data = lda.documents_per_topic(corpus_rf, docs, feature_names) #list of dicts {"desc", "doc_ids"}

    topics = []

    for topic in topic_data:
        t = {"desc":"", "docs":[]}
        t["desc"] = topic["desc"]

        for id in topic["doc_ids"]:
            t["docs"].append(collection.documents.get(pk=id))

        topics.append(t)

    return topics


@register.simple_tag
def get_clusters(collection_id, corpus=None, doc2vec=False, tf_idf=False, k=30):
    collection = Collection.objects.get(pk=collection_id)
    features = None
    vectors = features = list(collection.documents.values_list("id", flat=True))

    if doc2vec is True:
        #features = list(collection.documents.values_list("id", flat=True))
        vectors = corpus.wv.vectors

    elif tf_idf is True:
        c_id = str(collection_id)
        v_path = corpora_path + c_id + "/" + c_id + "_tf-idf_stopwords-included_cs.corpus"
        vectors = pickle.load(open(v_path, "rb"))
        #features = pickle.load(open(v_path + ".features", "rb"))

    clusterer = Clusterer(k=k)
    clusters_kmeans = clusterer.cluster_kmeans(vectors, file_output=False, console_output=True,
    reduced_vectors=None, feature_names=features)

    clusters = {}

    for key, doc_ids in clusters_kmeans.items():
        clusters[key] = []

        for id in doc_ids:
            clusters[key].append(collection.documents.get(pk=id))

    return clusters


def find_versions(id):
    c_id = str(id)
    name = c_id + "_tokens_stopwords-included_cs.corpus"
    corpus_tokenized = pickle.load(open(corpora_path + c_id + "/" + name, "rb"))
    #save_path = corpora_path + c_id + "/" + c_id + "_similarities.corpus"
    save_path = static_path + "similarities/"

    find_versions_async.delay(corpus_tokenized, save_path)

    return
