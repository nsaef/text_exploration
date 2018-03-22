from django import template
from django.conf import settings
from django.templatetags.static import static
from SearchEngine import SearchEngine
from CollectionExplorer.models import Collection, Document

register = template.Library()

static_path = settings.BASE_DIR + "/CollectionExplorer" + static("CollectionExplorer/index/")

@register.simple_tag
def ft_search(collection, query):
    se = SearchEngine(collection_path=collection.path, index_path=static_path, collection_id=collection.id)
    search_results = se.search(query, limit=100)
    results = []

    #print(results[0:results.scored_length()])
    for hit in search_results[0:search_results.scored_length()]: #
        d = Document.objects.get(path=hit["path"])
        preview = hit.highlights("content")
        results.append((d, preview))
        #print(hit["title"])
        ## Assume "content" field is stored
        #print(hit.highlights("content"))

    return results