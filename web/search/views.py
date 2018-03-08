from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from .models import Document, Query, Collection
from django.urls import reverse

def index(request):
    if request.method == "POST":
        if request.POST.get("collection_title"):
            c_title = request.POST.get("collection_title")
        if request.POST["collection_path"]:
            c_path = request.POST["collection_path"]
        if c_title and c_path:
            c = Collection.objects.create_collection(title=c_title, path=c_path)
            c.save()
    document_list = Document.objects.order_by("title")
    collection_list = Collection.objects.order_by("title")
    context = {
        "collection_list": collection_list,
        "document_list": document_list
    }
    return render(request, 'search/index.html', context)

def document_detail(request, doc_id):
    document = get_object_or_404(Document, pk=doc_id)
    return render(request, "search/document_detail.html", {"document": document})

def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id)
    return render(request, "search/collection_detail.html", {"collection":collection})

def results(request, query_id):
    query = get_object_or_404(Query, pk=query_id)
    return render(request, "search/results.html", {"query": query})

def search_action(request):
    query = Query()
    query.text = request.GET["doc_search"]
    query.save()
    return HttpResponseRedirect(reverse("results", kwargs={"query_id": query.id}))


