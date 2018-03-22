from django import template
from django.conf import settings
from django.templatetags.static import static
from CollectionExplorer.models import Collection, Entity
from Preprocesser import Preprocesser
from Analyzer import Analyzer
import pickle
import os

register = template.Library()
path = settings.BASE_DIR + "/CollectionExplorer" + static("CollectionExplorer/corpora/")

@register.simple_tag
def process_collection(collection, tokens=True, sents=False, cs=True, remove_stopwords=False):
    docs = list(collection.documents.values_list("content", flat=True))
    name = get_filename(collection.id, tokens, sents, cs, remove_stopwords)
    folder_path = path + str(collection.id)

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    if os.path.exists(folder_path + "/" + name):
        corpus = pickle.load(open(folder_path + "/" + name, "rb"))
    else:
        preprocesser = Preprocesser()
        if tokens is True:
            preprocesser.tokenize(docs, remove_stopwords=remove_stopwords, cs=cs)
            corpus = preprocesser.corpus_tokenized

           # plus parameters, somehow
        if sents is True:
            preprocesser.split_sentences(docs)
            corpus = preprocesser.corpus_sentences

        pickle.dump(corpus, open(folder_path + name, 'wb'))
    return corpus


def get_filename(id, tokens, sents, cs, remove_stopwords):
    name = str(id)
    if sents is True:
        name += "_sents.corpus"
        return name
    elif tokens is True:
        name += "_tokens"
    if remove_stopwords is True:
        name += "_stopwords-excluded"
    else:
        name += "_stopwords-included"
    if cs is True:
        name += "_cs"
    else:
        name += "_ci"
    name += ".corpus"
    return name


@register.simple_tag
def get_highest_freq_words(id, n=50):
    name = str(id) + "_tokens_stopwords-excluded_cs.corpus"
    corpus_tokenized =  pickle.load(open(path + str(id) + "/" + name, "rb"))

    analyzer = Analyzer()
    return analyzer.get_frequencies(corpus_tokenized, n)



@register.simple_tag
def get_named_entities(id, n=20):
    name = str(id) + "_sents.corpus"
    sents = pickle.load(open(path + str(id) + "/" + name, "rb"))

    analyzer = Analyzer()
    entities = analyzer.get_named_entities_sents(sents)
    col = Collection.objects.get(pk=id)

    #output = {"locations": [], "persons": [], "organizations": [], "others": []}
    for idx, counter in enumerate(entities):
        for el in counter.most_common():
            e = Entity(name=el[0], frequency=el[1])

            if idx is 0:
                #output["locations"].extend(counter.most_common(n))
                e.type = "location"
            elif idx is 1:
                #output["persons"].extend(counter.most_common(n))
                e.type = "person"
            elif idx is 2:
                #output["organizations"].extend(counter.most_common(n))
                e.type = "organization"
            elif idx is 3:
                #output["others"].extend(counter.most_common(n))
                e.type = "other"
            e.save()
            col.entities.add(e)
        col.save()
    return #output