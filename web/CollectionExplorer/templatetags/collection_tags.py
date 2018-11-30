from django import template
from django.conf import settings
from django.templatetags.static import static
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from CollectionExplorer.models import Collection, Entity, Ngram
from CollectionExplorer.tasks import *
#from Preprocesser import Preprocesser
from Analyzer import Analyzer
#from DocEmbedder import DocEmbedder
from TopicModeller import TopicModeller
from Clusterer import Clusterer
from Serializer import Serializer
import pickle
import os
from time import time
import statistics
import random

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
        serializer = Serializer()
        corpus = serializer.load(folder_path + "/" + name)

    else:
        corpus = None
        path = folder_path + "/" + name
        features_path = None
        #docs = list(collection.documents.values_list("id", "content"))

        if raw_frequencies or tf_idf:
            features_path = folder_path + "/" + name + ".features"

        process_collection_async.delay(collection.id, path, tokens, sents, raw_frequencies, tf_idf, remove_stopwords, cs, features_path=features_path) #.delay
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
def get_highest_freq_words(id, n=500, calc_m=True):
    serializer = Serializer()
    name = str(id) + "_tokens_stopwords-excluded_cs.corpus"
    corpus_tokenized =  serializer.load(corpora_path + str(id) + "/" + name)

    analyzer = Analyzer()
    freqs = analyzer.get_frequencies(corpus_tokenized, n)

    # if calc_m is True:
    #     m = int(len(freqs)/2)
    # elif n is None:
    #     m = len(freqs)
    # return dict(freqs[:m])
    return dict(freqs)


@register.simple_tag
def get_named_entities(id, n=20):
    get_named_entities_async.delay("collection", id, corpora_path) #.delay
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
    return get_doc2vec_model_async.delay(model_path, str(collection.id), corpora_path) #.delay
    #return model


@register.simple_tag
def find_ngrams(collection, bigrams=True, trigrams=True):
    id = str(collection.id)
    corpus_path = corpora_path + id + "/" + id + "_tokens_stopwords-excluded_cs.corpus"

    get_ngrams_async.delay(collection.id, corpus_path, bigrams, trigrams) #.delay
    return


@register.simple_tag
def create_topic_models(collection, n_topics=30):
    id = str(collection.id)
    corpus_path = corpora_path + id + "/" + id + "_rf_stopwords-included_cs.corpus"
    feature_path =corpus_path + ".features"

    serializer = Serializer()
    corpus_rf = serializer.load(corpus_path, type="csr_matrix")
    feature_names = serializer.load(feature_path, type="list")
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
    #features = None
    vectors = None
    features = list(collection.documents.values_list("id", flat=True))

    if doc2vec is True:
        #features = list(collection.documents.values_list("id", flat=True))
        vectors = corpus.wv.vectors

    elif tf_idf is True:
        serializer = Serializer()
        c_id = str(collection_id)
        v_path = corpora_path + c_id + "/" + c_id + "_tf-idf_stopwords-included_cs.corpus"
        vectors = serializer.load(v_path, type="csr_matrix")
        #features = serializer.load(v_path + ".features")

    clusterer = Clusterer(k=k)
    clusters_kmeans = clusterer.cluster_kmeans(vectors, file_output=False, console_output=True,
    reduced_vectors=None, feature_names=features)

    print("Sorting docs by cluster")
    clusters = {}
    limit = 5000

    for key, doc_ids in clusters_kmeans.items():
        clusters[key] = []
        random.shuffle(doc_ids)

        for id in doc_ids[:limit]:
            clusters[key].append(collection.documents.get(pk=id))

    # if collection.documents.count() > 15000:
    #     print("Creating excerpts from clusters...")
    #     for i, cluster in clusters:
    #         if len(cluster) > limit:
    #             random.shuffle(cluster)
    #             clusters[i] = cluster[:limit]

    return clusters

@register.simple_tag
def find_versions(id):
    c_id = str(id)
    name = c_id + "_tokens_stopwords-included_cs.corpus"
    path = corpora_path + c_id + "/" + name
    #corpus_tokenized = pickle.load(open(corpora_path + c_id + "/" + name, "rb"))
    #corpus_tokenized = joblib.load(corpora_path + c_id + "/" + name)

    serializer = Serializer()
    corpus_tokenized = serializer.load(path)

    #save_path = corpora_path + c_id + "/" + c_id + "_similarities.corpus"
    save_path = static_path + "similarities/"

    find_versions_async.delay(corpus_tokenized, save_path) #
    #make_versions_from_similarities(id)

    return


@register.simple_tag
def analyze_collection(id):
    c = Collection.objects.get(pk=id)

    #anzahl dateien insgesamt
    num_docs = c.documents.count()

    if num_docs == 0:
        return "<p>Keine Dokumente in der Sammlung</p>"

    #gruppiert nach typ: doc/docx/txt, pdf, xlsx/xls, html/htm, epub, json, pptx
    text = c.documents.filter(Q(title__iendswith=".txt") | Q(title__iendswith=".doc") | Q(title__iendswith=".docx")).count()
    pub = c.documents.filter(Q(title__iendswith=".pdf") | Q(title__iendswith=".epub")).count()
    table = c.documents.filter(Q(title__iendswith=".xls") | Q(title__iendswith=".xlsx")).count()
    web = c.documents.filter(Q(title__iendswith=".htm") | Q(title__iendswith=".html")).count()
    pres = c.documents.filter(title__iendswith=".pptx").count()
    data = c.documents.filter(title__iendswith=".json").count()

    #dokumentlänge: durchschnitt und median?
    docs = list(c.documents.all().values("content"))
    doc_len = [len(x["content"]) for x in docs]

    mean = statistics.mean(doc_len)
    median = statistics.median(doc_len)

    result = "<ul>"

    if num_docs > 0:
        result  += "<li>Gesamtzahl Dokumente: " + str(num_docs) + "</li>"

    if text > 0:
        result += "<li>Textdokumente (DOC, DOCX, TXT): " + str(text) + "</li>"

    if pub > 0:
        result += "<li>Publikationen (PDF/EPUB): " + str(pub) + "</li>"

    if pres > 0:
        result += "<li>Präsentationen (PPTX): " + str(pres) + "</li>"

    if web > 0:
        result += "<li>Webdokumente (HTML, HTM): " + str(web) + "</li>"

    if table > 0:
        result += "<li>Tabellen (XLS, XLSX): " + str(table) + "</li>"

    if data > 0:
        result += "<li>Daten (JSON): " + str(data) + "</li>"
    result += "<li>Durchschnittliche Dokumentlänge: " + str(mean) + " Zeichen inkl. Leerzeichen</li>"
    result += "<li>Median (50th percentile): " + str(median) + " Zeichen inkl. Leerzeichen</li>"

    result += "</ul>"

    return result

