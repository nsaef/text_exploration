from django import template
from django.conf import settings
from django.templatetags.static import static
from Preprocesser import Preprocesser
from DocEmbedder import DocEmbedder
from Analyzer import Analyzer
from Serializer import Serializer
from CollectionExplorer.models import Document, Version
from CollectionExplorer.tasks import *
import pickle
import os
import networkx as nx
import numpy as np

register = template.Library()


static_path = settings.BASE_DIR + "/CollectionExplorer" + static("CollectionExplorer/")
corpora_path = static_path + "corpora/"
model_path = static_path + "models/"


@register.simple_tag
def get_highest_freq_words(doc, n=None, calc_n=True):
    preprocesser = Preprocesser()
    d = {doc.id: doc.content}
    preprocesser.tokenize(d.items(), remove_stopwords=True)
    doc_tokenized = preprocesser.corpus_tokenized

    analyzer = Analyzer()
    freqs = analyzer.get_frequencies(doc_tokenized, None)
    if calc_n is True:
        n = int(len(freqs)/20)
    elif n is None:
        n = len(freqs)
    return dict(freqs[:n])

@register.simple_tag
def get_named_entities(doc):
    get_named_entities_async.delay(type="document", id=doc.id) #.delay
    return


@register.simple_tag
def get_similar_docs(doc, n=50):
    #otherwise create them
    collection_id = str(doc.collection.id)
    model_file = model_path + collection_id + ".model"
    corpus_path = corpora_path + collection_id + "/" + collection_id + "_tokens_stopwords-included_cs.corpus"

    try:
        serializer = Serializer()
        corpus = serializer.load(corpus_path)
    except FileNotFoundError as e:
        print("Korpus 3 (tokenisiert, mit Stoppwörtern) nicht vorhanden.")
        return []

    embedder = DocEmbedder()
    model = embedder.run(path=model_file)

    vs = doc.version_candidates.count()
    dups = doc.duplicates.count()

    n2 = n + dups + vs
    sim_docs = embedder.show_similar_docs(corpus=corpus, doc_id=doc.id, topn=n2)

    results = []
    for id, score in sim_docs:
        d = Document.objects.get(pk=id)
        if d not in doc.duplicates.all() and d not in doc.version_candidates.all():
            version = Version(candidate=d, version_of=doc, similarity_measure="Word2Vec", similarity_score=score)
            version.save()

    return results


@register.simple_tag
def retrieve_version_candidates(doc):
    doc_id = str(doc.id)
    corpus_path = static_path + "similarities/" + doc_id + "/" + doc_id + "_similarities.corpus"
    candidates = {}

    if os.path.isfile(corpus_path):
        serializer = Serializer()
        corpus = serializer.load(corpus_path)

        for c_id, score in corpus.items():
            #score = hash.jaccard(c_id)
            if score > 0.5 and score < 0.9:
                candidate = Document.objects.get(pk=c_id)
                candidates[c_id] = (candidate, score)

    return candidates

@register.simple_tag
def create_graph_network(collection=None, document=None):
    if document is not None:
        docs = [document]
        docs.extend(document.duplicates.all())
        docs.extend(document.version_candidates.all())
    elif collection is not None:
        docs = list(collection.documents.all())
    else:
        return

    result = {"nodes": [], "links":[]}
    groups = {
        "interesting": 0,
        "not interesting": 1,
        "unrated": 2,
        "duplicate": 3,
        "version": 4
    }

    for doc in docs:
        g = None

        #if doc is duplicate of document: groups
        #elif doc is version_of document: groups
        if doc.interesting is True:
            g = groups["interesting"]
        elif doc.interesting is False:
            g = groups["not interesting"]
        else:
            g = groups["unrated"]

        d = {
            "title": doc.title,
            "id": doc.id,
            "group":g
        }

        result["nodes"].append(d)

        for dup in doc.duplicates.all():
            e = {
                "source": doc.id,
                "target": dup.id,
                "value": 100
            }
            result["links"].append(e)

         #hier brauche ich vermutlich eine query nach der class version mit
        versions = Version.objects.filter(version_of=doc.id)
        for rel in versions:
            e = {
                "source": doc.id,
                "target": rel.candidate.id,
                "value": rel.similarity_score,
                "measure": rel.similarity_measure
            }
            result["links"].append(e)
    return result


@register.simple_tag
def get_tf_idf(doc_id):
    doc = Document.objects.get(pk=doc_id)
    c_id = str(doc.collection.id)
    filename = c_id + "_tf-idf_stopwords-included_cs.corpus"
    filepath = corpora_path + c_id + "/" + filename

    try:
        serializer = Serializer()
        vectors = serializer.load(filepath)
        features =  serializer.load(filepath + ".features")
        idx = serializer.load(filepath + ".idx")
    except FileNotFoundError:
        return "Bitte auf der Hauptseite der Sammlung die Tf-idf-Repräsentation erzeugen. Dann werden an dieser Stelle die spezifischsten Worte angezeigt."
    pos = idx[doc_id]

    docvec = vectors[pos]

    feature_array = np.array(features)
    tfidf_sorting = np.argsort(docvec.toarray()).flatten()[::-1]

    n = 30
    top_n = feature_array[tfidf_sorting][:n]

    return top_n
