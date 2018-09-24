# Create your tasks here
from __future__ import absolute_import, unicode_literals
import celery
from celery.task import task
from celery import shared_task
import eventlet
import importlib
import os
import sys
import pickle
import zipfile
import datetime
import codecs
from time import time
from django.db import close_old_connections
from CollectionExplorer.models import Collection, Document, Entity, Ngram, Version
from pdfminer.converter import TextConverter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from docx import Document as DocX
import textract
from io import BytesIO, StringIO
import shutil


class CeleryBasicTask(celery.Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # exc (Exception) - The exception raised by the task.
        # args (Tuple) - Original arguments for the task that failed.
        # kwargs (Dict) - Original keyword arguments for the task that failed.
        print('{0!r} failed: {1!r}'.format(task_id, exc))

    def on_success(self, retval, task_id, args, kwargs):
        print('{0!r} succeeded'.format(task_id))


# eventlet.monkey_patch(MySQLdb=True)

# add your path to the sys path
cwd = os.getcwd()
root_dir = os.path.dirname(cwd)
sys.path.append(root_dir)

# import the class from the module
preprocessing_module = importlib.import_module("Preprocesser")
prep = getattr(preprocessing_module, "Preprocesser")

doc_embedding_module = importlib.import_module("DocEmbedder")
doc_embedder = getattr(doc_embedding_module, "DocEmbedder")

search_module = importlib.import_module("SearchEngine")
search = getattr(search_module, "SearchEngine")

analyzer_module = importlib.import_module("Analyzer")
analyzer = getattr(analyzer_module, "Analyzer")

version_handler_module = importlib.import_module("VersionHandler")
version_handler = getattr(version_handler_module, "VersionHandler")

@shared_task(base=CeleryBasicTask)
def add(x, y):
    return x + y


### all long processes go in here
# initial reading of files, all corpora, named entities
### templatetags load if available and otherwise call the functions defined in here

@shared_task(base=CeleryBasicTask)
def process_collection_async(docs, corpus_path, tokens, sents, raw_frequencies, tf_idf, remove_stopwords, cs,
                             features_path=None):
    print("Running process collection asynchronously")
    close_old_connections()
    feature_names = None
    corpus = None
    preprocesser = prep()
    idx = None

    if tokens:
        # print("Tokenizing corpus")
        preprocesser.tokenize(docs, remove_stopwords=remove_stopwords, cs=cs)
        corpus = preprocesser.corpus_tokenized

    elif sents:
        # print("Sentenizing corpus")
        preprocesser.split_sentences(docs)
        corpus = preprocesser.corpus_sentences

    elif raw_frequencies:
        # print("Getting raw frequencies")
        c = [x[1] for x in docs]
        corpus = preprocesser.vectorize_frequencies(c)
        feature_names = preprocesser.feature_names_raw

    elif tf_idf:
        c = [x[1] for x in docs]
        idx = {x[0]:i for i, x in enumerate(docs)}
        corpus = preprocesser.vectorize_tfidf(c)
        feature_names = preprocesser.feature_names_tfidf

    if corpus is not None:
        pickle.dump(corpus, open(corpus_path, "wb"))

    if features_path and feature_names is not None:
        pickle.dump(feature_names, open(features_path, "wb"))

    if idx is not None:
        pickle.dump(idx, open(corpus_path + ".idx", "wb"))

    print("Saved collection at " + corpus_path)
    return True


# TODO: Test subdirectories
@shared_task(base=CeleryBasicTask)
def add_docs_to_collection_async(collection_id, file=None, remote=True, path=None):
    close_old_connections()
    collection = Collection.objects.get(pk=collection_id)
    file_data = []

    if file is not None and remote is True:
        with zipfile.ZipFile(file, "r") as zip_file:
            # get the list of files
            names = zip_file.namelist()
            main_dir = names[0]
            # handle your files as you need. You can read the file with:
            for name in names:
                name_pos = name.rfind("/")
                fname = name[name_pos + 1:]

                if name.lower().endswith((".doc", ".rtf", ".eml", ".epub", ".json", ".html", ".htm", ".pptx", ".xlsx", ".xls")):
                    data = process_textract(name, fname, remote=True, zip=zip_file)
                else:
                    with zip_file.open(name, 'r') as f:
                        if f.name == main_dir:
                            continue

                        date = datetime.datetime.now()

                        data = process_uploaded_file(f, fname, name, date)
                file_data.append(data)

    elif file is None and remote is False:
        if path is None:
            path = collection.path
        if os.path.exists(path):
            files = os.listdir(path)

            for filename in files:
                filepath = path + "/" + filename
                if os.path.isdir(filepath) is True:
                    continue

                #use textract for all file formats, as it also reads txt/docx/pdf
                if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".ps", ".tiff", ".tif")):
                    f = process_textract(filepath, filename, remote=False, path=filepath)
                    file_data.append(f)
        else:
            print("Path not found. Tried: " + path)
            return False

    objs = [Document(title=f["title"], content=f["content"], path=f["path"], date=f["date"],
                                               collection=collection) for f in file_data if f is not None and isinstance(f["date"], datetime.datetime)]
    Document.objects.bulk_create(objs)
    print("Done creating documents")
    return True


def process_uploaded_file(fileobj, name, path, date):
    data = None
    name_low = name.lower()
    if name_low.endswith(".txt"):
        data = get_plain_text(fileobj, name, path, date)
    elif name_low.endswith(".pdf"):
        data = get_pdf_content(fileobj, path, name)
    elif name_low.endswith(".docx"):  # what about dox?
        data = get_docx_content(fileobj, path, name)
    else:  # not a supported file format
        print(name + " is not a supported file format")
    return data

def process_textract(name, fname, remote=True, zip=None, path=None):
    if remote is True:
        dir_path = "/home/nsaef/projects/CollectionExplorer/tmp/"
        zip.extract(name, path=dir_path)
        name_pos = name.rfind("/")
        dname = dir_path + name[:name_pos]
        path = dir_path + name

    f = {}
    f["date"] = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    try:
        f["content"] = textract.process(path).decode("utf-8")
    except Exception as e:
        print("textract couldn't process file " + name)
        print(e)
        return None
    f["path"] = path
    f["title"] = fname

    if remote is True:
        os.remove(path)
        if not os.listdir(dname):
            os.rmdir(dname)
    return f

def get_plain_text(fileobj, name, path, date):
    f = {}
    try:
        f["content"] = fileobj.read().decode('utf8')
    except Exception as e:
        print(e)
        return None
    f["date"] = date
    f["path"] = path
    f["title"] = name

    return f


def get_pdf_content(fileobj, path, title=None):
#    try:
    fo = BytesIO(fileobj.read())
    # except UnicodeDecodeError:
    #     fo = BytesIO(fileobj.read().decode("utf-8"))
    date = False
    doc_title = False

    rsrc_mgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    device = TextConverter(rsrc_mgr, retstr, codec=codec)
    interpreter = PDFPageInterpreter(rsrc_mgr, device)
    caching = True
    pagenos = set()

    try:
        for page in PDFPage.get_pages(fo, pagenos, caching=caching,check_extractable=True):
            if date is False:
                date = page.doc.info[0].get("CreationDate")
            if doc_title is False:
                doc_title = page.doc.info[0].get("Title")
            interpreter.process_page(page)
        text = retstr.getvalue()
    except Exception as e:
        print(e)
        return None

    device.close()
    retstr.close()

    #D:20161231184921-07'00'
    try:
        #date = fileReader.documentInfo["/ModDate"]
        year = int(date[2:6])
        month = int(date[6:8])
        day = int(date[8:10])
        hour = int(date[10:12])
        minute = int(date[12:14])
        second = int(date[14:16])

        # tz_indicator = date[16]
        tz_hour = int(date[16:19])
        tz_minute = int(date[20:-1])

        tz_delta = datetime.timedelta(hours=tz_hour, minutes=tz_minute)
        tz = datetime.timezone(tz_delta)
        d = datetime.datetime(year, month, day, hour, minute, second, tzinfo=tz)
    except Exception as e:
        print(e)
        d = datetime.datetime.now()

    f = {}
    f["date"] = d
    f["title"] = determine_title(doc_title, title)
    f["path"] = path
    f["content"] = text

    return f


def get_docx_content(fileobj, path, title=None):
    try:
        fo = BytesIO(fileobj.read())
    except UnicodeDecodeError as e:
        print(e)
        return None
    try:
        doc = DocX(fo)
    except ValueError as e:
        print(e)
        return None

    content = ""

    for paragraph in doc.paragraphs:
        content += paragraph.text + "\n"

    f = {}
    f["date"] = doc.core_properties.created
    f["path"] = path
    f["title"] = determine_title(doc.core_properties.title, title)
    f["content"] = content

    return f


def determine_title(t1, t2):
    title = "unbekannt"

    if t1 is not None and t1 is not "":
        title = t1
    elif t2 is not None and t2 is not "":
        title = t2
    return title


@shared_task(base=CeleryBasicTask)
def get_doc2vec_model_async(model_path, str_collection_id, corpora_path=None):
    model_name = model_path + str_collection_id + ".model"
    embedder = doc_embedder()

    if corpora_path is not None:
        # get the tokenized model
        corpus_path = corpora_path + "/" + str_collection_id + "/" + str_collection_id + \
                      "_tokens_stopwords-included_cs.corpus"
        corpus_tokenized = pickle.load(open(corpus_path, "rb"))
        model = embedder.run(path=model_name, corpus=corpus_tokenized)
    else:
        model = embedder.run(path=model_name)

    return model


@shared_task(base=CeleryBasicTask)
def instantiate_ft_search(collection, index_path, recreate=False):
    idx_dir = index_path + str(collection.id)
    if recreate is True and os.path.exists(idx_dir):
        shutil.rmtree(idx_dir)
        print("removed old index")
    se = search(index_path=index_path, collection_id=collection.id)
    docs = list(collection.documents.values())
    se.build_index(files=docs)
    return True


@shared_task(base=CeleryBasicTask)
def get_named_entities_async(type, id, corpora_path=None, n=20):
    ana = analyzer()
    type_map = ["location", "person", "organization", "other"]

    t0 = time()
    if type == "collection":
        name = str(id) + "_sents.corpus"
        sents = pickle.load(open(corpora_path + str(id) + "/" + name, "rb"))
        entities = ana.get_named_entities_sents(sents)

        col = Collection.objects.get(pk=id)
        objs = [Entity(name=el[0], frequency=el[1], type=type_map[idx], collection=col) for idx, counter in
                enumerate(entities) for el in counter.most_common()]
    elif type == "document":
        doc = Document.objects.get(pk=id)
        preprocesser = prep()

        d = {doc.id: doc.content}
        preprocesser.split_sentences(d.items())

        sents = preprocesser.corpus_sentences
        entities = ana.get_named_entities_sents(sents)

        objs = [Entity(name=el[0], frequency=el[1], type=type_map[idx], document=doc) for idx, counter in
                enumerate(entities) for el in counter.most_common()]

    Entity.objects.bulk_create(objs)
    print("done in %0.3fs" % (time() - t0))
    return


@shared_task(base=CeleryBasicTask)
def get_ngrams_async(id, corpus_path, bigrams=True, trigrams=True):
    corpus_tokenized = pickle.load(open(corpus_path, "rb"))
    collection = Collection.objects.get(pk=id)

    ana = analyzer()
    ngrams = ana.find_ngrams(corpus_tokenized, bigrams=bigrams, trigrams=trigrams)

    objs_bg = [Ngram(type="bigram", method=method, word1=item[0], word2=item[1], score=idx, collection=collection) for
               method, word_list in ngrams["bigrams"].items() for idx, item in enumerate(word_list)]
    Ngram.objects.bulk_create(objs_bg)

    objs_tg = [Ngram(type="trigram", method=method, word1=item[0], word2=item[1], word3=item[2], score=idx,
                     collection=collection) for
               method, word_list in ngrams["trigrams"].items() for idx, item in enumerate(word_list)]
    Ngram.objects.bulk_create(objs_tg)

    print("Done collection ngrams")
    return True

@shared_task(base=CeleryBasicTask)
def find_versions_async(corpus, save_path):
    vh = version_handler()
    hash_dict = vh.calc_hashes(corpus)
    vh.calculate_similarities(threshold=0.5)
    #save_path += "_lsh"

    #pickle.dump(vh.similarities, open(save_path, 'wb'))
    pickle_similarities(vh.similarities, save_path)

    print("Creating duplicate relationships...")
    t0 = time()
    for src_doc_id, duplicates in vh.duplicates.items():
        src_doc = Document.objects.get(pk=int(src_doc_id))

        for dup_id in duplicates:
            d = Document.objects.get(pk=int(dup_id))
            src_doc.duplicates.add(d)
            src_doc.save()
    print("done in %0.3fs." % (time() - t0))

    print("Creating possible version relationships...")
    t0 = time()
    for src_doc_id, versions in vh.version_candidates.items():
        src_doc = Document.objects.get(pk=int(src_doc_id))

        for v_id, score in versions:
            v_doc = Document.objects.get(pk=int(v_id))

            version = Version(candidate=v_doc, version_of=src_doc, similarity_measure=vh.method, similarity_score=score)
            version.save()
    print("done in %0.3fs." % (time() - t0))
    return


def pickle_similarities(sims, path):
    for doc_id, values in sims.items():
        folder_path = path + str(doc_id)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        filepath = folder_path + "/" + str(doc_id) + "_similarities.corpus"
        pickle.dump(values, open(filepath, 'wb'))