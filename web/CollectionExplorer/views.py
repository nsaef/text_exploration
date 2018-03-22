from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from .models import Document, Query, Collection
from django.urls import reverse
from django.views import generic

class IndexView(generic.ListView):
    template_name = "CollectionExplorer/index.html"
    context_object_name = "collection_list"

    def get_queryset(self):
        return Collection.objects.order_by("title")

class DocumentDetail(generic.DetailView):
    model = Document
    #template_name = "CollectionExplorer/document_detail.html"

class DocumentList(generic.ListView):
    model = Document
    template_name = "CollectionExplorer/results.html"

class CollectionDetail(generic.DetailView):
    model = Collection


def results(request):
    query = request.POST["query"]
    id = request.POST["collection_id"]
    c = Collection.objects.get(pk=id)
    return render(request, "CollectionExplorer/results.html", {"query": query, "collection": c})


def add_collection(request):
    c = Collection()
    c.title = request.POST["col_title"]
    c.path = request.POST["col_path"]
    c.save()
    c.add_docs_to_collection()
    c.save()
    return HttpResponseRedirect(reverse("collection_detail", kwargs={"pk": c.id}))

def add_docs_to_collection(request, pk):
    c = Collection.objects.get(pk=pk)
    c.add_docs_to_collection()
    c.save()
    return HttpResponseRedirect(reverse("collection_detail", kwargs={"pk": c.id}))


