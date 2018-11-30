from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from django.db import connections
from .models import Document, Collection, Version
from .forms import *
from django.urls import reverse
from django.views import generic
from django.conf import settings
from django.templatetags.static import static
from django.contrib.auth.decorators import login_required
from CollectionExplorer.templatetags.collection_tags import process_collection, get_doc2vec_model, find_versions
from CollectionExplorer.templatetags.search_tags import ft_search
from CollectionExplorer.tasks import *
from DocEmbedder import DocEmbedder


class IndexView(generic.ListView):
    template_name = "CollectionExplorer/index.html"
    context_object_name = "collection_list"

    def get_queryset(self):
        collections = Collection.objects.order_by("title")
        return collections

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        if not self.request.session.get('collection_id'):
            self.request.session["collection_id"] = None
        return context


class DocumentDetail(generic.DetailView):
    model = Document

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['collection'] = self.object.collection #Collection.objects.get(pk=self.kwargs.get("collection_id", None))
        context["versions_minhash"] = Version.objects.filter(version_of=self.object.id, similarity_measure="MinHash")
        context["versions_word2vec"] = Version.objects.filter(version_of=self.object.id, similarity_measure="Word2Vec", similarity_score__gte=0.1)
        context["note_form"] = TextForm()
        return context


class DocumentList(generic.ListView):
    model = Document
    template_name = "CollectionExplorer/results.html"


class CollectionDetail(generic.DetailView):
    model = Collection

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        self.request.session["collection_id"] = self.object.id
        return context


def upload_files(request, pk):
    c = Collection.objects.get(pk=pk)

    # Handle file upload
    if request.method == 'POST':
        upload_form = UploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            try:
                file = request.FILES["doc_file"]
            except Exception:
                file = None
            r = request.POST.get("remote", True)
            path = None

            if r == 'on':
                remote = True
            else:
                remote = False
                path = request.POST.get("remote_path")

            add_docs_to_collection_async(c.id, file=file, remote=remote, path=path)
            #add_docs_to_collection_async.delay(c.id, files)
            return HttpResponseRedirect(reverse("collection_detail", kwargs={"pk": c.id}))
    else:
        upload_form = UploadForm()  # A empty, unbound form
        return render(request, "CollectionExplorer/add_docs_to_collection.html", {"pk": pk, "collection": c, "upload_form": upload_form})
        #return HttpResponseRedirect(reverse("upload_docs", kwargs={"pk": c.id}))


def find_versions_duplicates(request, pk):
    find_versions(pk)
    return HttpResponseRedirect(reverse("collection_detail", kwargs={"pk": pk}))


def collection_statistics(request, pk):
    c = Collection.objects.get(pk=pk)
    return render(request, "CollectionExplorer/statistical_analysis.html", {"pk": pk, "collection": c})


def collection_semantics(request, pk):
    c = Collection.objects.get(pk=pk)

    n = request.GET.get("n_clusters")
    if n is not None: n_clusters = int(n)
    else:
        n_clusters = n

    d2v = request.GET.get("doc2vec", False)
    tf_idf = request.GET.get("tf_idf", False)
    topics = request.GET.get("topics", False)

    return render(request, "CollectionExplorer/semantic_analysis.html", {"pk": pk, "collection": c, "n_clusters": n_clusters, "doc2vec": d2v, "tf_idf": tf_idf, "topics": topics})


def results(request):
    query = request.GET.get("query")
    if query is None:
        query = request.POST.get("query")

    id = request.GET.get("col")
    if id is None:
        id = request.POST.get("collection_id")
        if id is None:
            if Collection.objects.count() is 1:
                c = Collection.objects.all()[0]
            elif Collection.objects.count() > 1:
                c = None
                # error message: select a collection
                # OR: search across all collections
            elif Collection.objects.count() is 0:
                c = None
                # error message: No collections available

    c = Collection.objects.get(pk=id)
    return render(request, "CollectionExplorer/results.html", {"query": query, "collection": c})


def add_collection(request):
    c = Collection()
    c.title = request.POST["col_title"]
    c.path = request.POST["col_path"]
    c.save()
    #add_docs_to_collection_async.delay(c.id)
    return HttpResponseRedirect(reverse("upload_files", kwargs={"pk": c.id}))


def add_docs_to_collection(request, pk):
    c = Collection.objects.get(pk=pk)
    add_docs_to_collection_async.delay(c.id)
    return HttpResponseRedirect(reverse("collection_detail", kwargs={"pk": c.id}))


def create_file(request, pk):
    c = Collection.objects.get(pk=pk)
    static_path = settings.BASE_DIR + "/CollectionExplorer" + static("CollectionExplorer/")
    index_path = static_path + "/index/"

    raw_frequencies = request.POST.get("raw_frequencies", False)
    tokens = request.POST.get("tokens", False)
    sents = request.POST.get("sents", False)
    tf_idf = request.POST.get("tf_idf", False)
    cs = request.POST.get("cs", True)
    remove_stopwords = request.POST.get("remove_stopwords", False)
    fulltext = request.POST.get("fulltext", False)
    model = request.POST.get("model", False)

    if model:
        get_doc2vec_model(c, recreate=True)
    elif fulltext:
        instantiate_ft_search.delay(c, index_path, recreate=True) #.delay
    else:
        process_collection(c, raw_frequencies=raw_frequencies, tokens=tokens, sents=sents, tf_idf=tf_idf, cs=cs,
                           remove_stopwords=remove_stopwords, async=True)
    return HttpResponseRedirect(reverse("collection_detail", kwargs={"pk": c.id}))


def edit_favorite(request, pk):
    doc = Document.objects.get(pk=pk)

    if doc.interesting is not True:
        doc.interesting = True
    else:
        doc.interesting = False

    doc.save()
    return HttpResponse(doc.interesting)


def save_note(request, pk):
    doc = Document.objects.get(pk=pk)

    note = request.POST.get("note")

    if note is not False:
        doc.note = note
        doc.save()

    return HttpResponse(note)


def analyse_vocabulary(request, pk):
    c = Collection.objects.get(pk=pk)

    if request.method == 'POST':
        result = None
        type = request.POST.get("type")
        source = request.POST.get("source")
        embedder = DocEmbedder()

        if source == "current_collection":
            model = get_doc2vec_model(c)
        else:
            path = settings.BASE_DIR + "/CollectionExplorer" + static("CollectionExplorer/") + "models/model_d2v_200k_with_stopwords.mdl"
            print(path)
            model = embedder.run(path=path)

        if type == "similarity":
            word = request.POST.get("word")
            n = int(request.POST.get("n"))

            if word in model.wv.vocab:
                result = model.wv.most_similar(word, topn=n)

        elif type == "comparison":
            a = request.POST.get("word_a")
            b = request.POST.get("word_b")
            c = request.POST.get("word_c")

            if all (word in model.wv.vocab for word in (a, b, c)):
                result = model.wv.most_similar(positive=[b, c], negative=a, topn=10)

        if result is not None:
            res_string = "<ol>"

            for item in result:
                res_string += "<li>" + item[0] + " (" + str(item[1]) + ")</li>"
            res_string += "</ol>"

            result = res_string

        return HttpResponse(result)
    else:
        return render(request, "CollectionExplorer/vocabulary.html", {"pk": pk, "collection": c})


def network(request, pk):
    collection = Collection.objects.get(pk=pk)
    return render(request, "CollectionExplorer/network.html", {"pk": pk, "collection": collection})


def delete_content(request, pk):
    c = Collection.objects.get(pk=pk)
    c.documents.all().delete()
    return HttpResponseRedirect(reverse("collection_detail", kwargs={"pk": c.id}))
