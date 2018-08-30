from django import template
from django.conf import settings
from django.templatetags.static import static
from Preprocesser import Preprocesser
from SearchEngine import SearchEngine
from DocEmbedder import DocEmbedder
from CollectionExplorer.models import Collection, Document

register = template.Library()

static_path = settings.BASE_DIR + "/CollectionExplorer" + static("CollectionExplorer/")
index_path = static_path + "/index/"
model_path = static_path + "/models/"

@register.simple_tag
def ft_search(collection, query):
    se = SearchEngine(index_path=index_path, collection_id=collection.id)
    search_results = se.search(query, limit=100)

    res = search_results["result"]
    searcher = search_results["searcher"]

    results = []

    for hit in res[0:res.scored_length()]: #
        try:
            d = Document.objects.get(path=hit["path"])
        except Document.MultipleObjectsReturned:
            d = Document.objects.filter(path=hit["path"]).order_by('id').first()

        preview = hit.highlights("content")
        results.append((d, preview))

    searcher.close()

    return results

@register.simple_tag
def get_similar_words(query, collection_id):
    model_file = model_path + str(collection_id) + ".model"
    q = {1: query}

    pp = Preprocesser()
    pp.tokenize(q.items())
    query_tokenized = pp.corpus_tokenized

    embedder = DocEmbedder()
    model = embedder.run(path=model_file)

    words = {word: model.wv.most_similar(word, topn=10) for v_list in query_tokenized.values() for word in v_list if word in model.wv.vocab}
    return words.items()
