from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from .models import Document, Query, Collection
from django.urls import reverse
from django.views import generic

class IndexView(generic.ListView):
    template_name = "search/index.html"
    context_object_name = "collection_list"

    def get_queryset(self):
        return Collection.objects.order_by("title")

class DocumentDetail(generic.DetailView):
    model = Document
    #template_name = "search/document_detail.html"

class CollectionDetail(generic.DetailView):
    model = Collection

class ResultsView(generic.DetailView):
    model = Query
    template_name = "search/results.html"

def search_action(request):
    query = Query()
    query.text = request.GET["doc_search"]
    query.save()
    return HttpResponseRedirect(reverse("results", kwargs={"query_id": query.id}))


