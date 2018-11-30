# Create your tasks here
from __future__ import absolute_import, unicode_literals
import celery
from celery.task import task
from celery import shared_task
import importlib
import os
import sys
import pickle
import zipfile
import tarfile
import datetime
from django.utils import timezone
import gc
from itertools import islice
from collections import Counter
from time import time
from django.db import close_old_connections
from django.conf import settings
from django.templatetags.static import static
from CollectionExplorer.models import Collection, Document, Entity, Ngram, Version
import textract
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

serializer_module = importlib.import_module("Serializer")
serializer = getattr(serializer_module, "Serializer")

@shared_task(base=CeleryBasicTask)
def add(x, y):
    return x + y


### all long processes go in here
# initial reading of files, all corpora, named entities
### templatetags load if available and otherwise call the functions defined in here
@shared_task(base=CeleryBasicTask)
def process_collection_async(collection_id, corpus_path, tokens, sents, raw_frequencies, tf_idf, remove_stopwords, cs,
                             features_path=None):
    print("Running process collection asynchronously")
    close_old_connections()
    feature_names = None
    corpus = None
    preprocesser = prep()
    se = serializer()
    idx = None
    c = Collection.objects.get(pk=collection_id)
    docs_len = c.documents.count()
    docs = None

    start = 0
    # i = 100000
    i = 10000
    end = min(start + i, docs_len)

    if tokens:
        # print("Tokenizing corpus")
        while start < end:
            print("Tokenizing docs " + str(start) + " to " + str(end) + " of " + str(docs_len))
            docs_qs = c.documents.all()[start:end]
            docs = docs_qs.values_list("id", "content")

            docs = preprocesser.clean_corpus(docs, pattern="[\-_+#\*]{3,}")
            preprocesser.tokenize(docs, remove_stopwords=remove_stopwords, cs=cs)
            #corpus = preprocesser.corpus_tokenized

            se.save(preprocesser.corpus_tokenized, corpus_path, folder=True) #, overwrite=False
            #del corpus
            #gc.collect()

            start += i
            end = min(end+i, docs_len)

    elif sents:
        while start < end:
            print("Tokenizing docs " + str(start) + " to " + str(end) + " of " + str(docs_len))
            docs_qs = c.documents.all()[start:end]
            docs = docs_qs.values_list("id", "content")

            # print("Sentenizing corpus")
            docs = preprocesser.clean_corpus(docs, pattern="[\-_+#\*]{3,}")
            preprocesser.split_sentences(docs)
            #corpus = preprocesser.corpus_sentences
            se.save(preprocesser.corpus_sentences, corpus_path, folder=True)  # , overwrite=False

            start += i
            end = min(end + i, docs_len)

    elif raw_frequencies:
        while start < end:
            print("Processing frequencies in docs " + str(start) + " to " + str(end) + " of " + str(docs_len))
            docs_qs = c.documents.all()[start:end]
            docs = docs_qs.values_list("id", "content")

            # print("Getting raw frequencies")
            c = [x[1] for x in docs]
            corpus = preprocesser.vectorize_frequencies(c)
            feature_names = preprocesser.feature_names_raw

            se.save(corpus, corpus_path, folder=True, type="list")  # , overwrite=False

            start += i
            end = min(end + i, docs_len)

    elif tf_idf:
        while start < end:
            docs_qs = c.documents.all()[start:end]
            docs = docs_qs.values_list("id", "content")

            c = [x[1] for x in docs]
            idx = {x[0]:i for i, x in enumerate(docs)}
            corpus = preprocesser.vectorize_tfidf(c)
            feature_names = preprocesser.feature_names_tfidf
            se.save(corpus, corpus_path, folder=True, type="list")

            start += i
            end = min(end + i, docs_len)

    # if corpus is not None:
    #     #pickle.dump(corpus, open(corpus_path, "wb"))
    #     se.save(corpus, corpus_path, folder=True)
    #     pass

    if features_path and feature_names is not None:
        #pickle.dump(feature_names, open(features_path, "wb"))
        se.save(feature_names, features_path, folder=True)

    if idx is not None:
       # pickle.dump(idx, open(corpus_path + ".idx", "wb"))
        se.save(idx, corpus_path + ".idx", folder=True)

    print("Saved collection at " + corpus_path)
    return True


# TODO: Test subdirectories
@shared_task(base=CeleryBasicTask)
def add_docs_to_collection_async(collection_id, file=None, remote=True, path=None):
    close_old_connections()
    collection = Collection.objects.get(pk=collection_id)
    #skip_formats = (".jpg", ".jpeg", ".png", ".ps", ".tiff", ".tif", ".zip", ".tar", ".gif", ".exe", ".db", ".edb")
    valid_formats = (".txt", ".doc", ".docx", ".csv", ".json", ".xlsx", ".pptx", "pdf", ".epub", ".htm", ".html", ".tsv", ".xls", ".odt")
    file_data = []
    t0 = time()

    if file is not None and remote is True:
        with zipfile.ZipFile(file, "r") as zip_file:
            # get the list of files
            names = zip_file.namelist()
            main_dir = names[0]

            start = 0
            i = 100
            end = min(len(names), i)

            while start < end:
                file_data = []

                # handle your files as you need. You can read the file with:
                for name in names[start:end]:
                    name_pos = name.rfind("/")
                    fname = name[name_pos + 1:]

                    if name.lower().endswith(valid_formats):
                        data = process_textract(name, fname, remote=True, zip=zip_file)
                        file_data.append(data)
                    elif name.lower().endswith(".zip"):
                        fs = handle_zip(name, fname, collection_id)
                        file_data.extend(fs)
                    elif name.lower().endswith(".tar"):
                        fs = handle_tar(name, collection_id)
                        file_data.extend(fs)

                create_objects(collection.id, file_data)
                start = min(start + i, end)
                del file_data
                gc.collect()
    elif file is None and remote is False:
        if path is None:
            path = collection.path
        if os.path.exists(path):
            # files is a list
            files = os.listdir(path)
            start = 0
            i = 10000
            end = min(len(files), i)
            #x = 0

            while start < len(files):
                print("reading files " + str(start) + " to " + str(end) + " of (currently) " + str(len(files)))
                file_data = []
                for filename in files[start:end]:
                    filepath = path + "/" + filename
                    if os.path.isdir(filepath) is True:
                        fs = [filename + "/" + f for f in os.listdir(filepath)]
                        files.extend(fs)
                        continue

                    #upload was interrupted; continue here
                    #if x > 359869:
                    #use textract for all file formats, as it also reads txt/docx/pdf
                    if filename.lower().endswith(valid_formats):
                        f = process_textract(filepath, filename, remote=False, path=filepath)
                        file_data.append(f)
                    elif filename.lower().endswith(".zip"):
                        fs = handle_zip(filepath, filename, collection_id)
                        #file_data.extend(fs)
                    elif filename.lower().endswith(".tar"):
                        fs = handle_tar(filepath, collection_id)
                        #file_data.extend(fs)
                    #x += 1

                create_objects(collection.id, file_data)
                start = end
                end = min (end+i, len(files))
                del file_data
                gc.collect()

        else:
            print("Path not found. Tried: " + path)
            return False
    print("Done creating documents in %0.3fs." % (time() - t0))
    return True


def create_objects(id, file_data):
    collection = Collection.objects.get(pk=id)

    objs = [Document(title=f["title"], content=f["content"], path=f["path"], date=f["date"], collection=collection) for f in file_data if f is not None and isinstance(f["date"], datetime.datetime)]

    print("\n\n* * * * * * * * * *\nCreating " + str(len(objs)) + " Documents...\n* * * * * * * * * *\n\n")

    try:
        Document.objects.bulk_create(objs)
    except ValueError:
        nul = '\x00'
        objs = [Document(title=f["title"], content=f["content"], path=f["path"], date=f["date"], collection=collection)
                for f in file_data if f is not None and isinstance(f["date"], datetime.datetime) and nul not in f["content"] and nul not in f["title"] and nul not in f["path"]]
        try:
            Document.objects.bulk_create(objs)
        except ValueError:
            for f in file_data:
                try:
                    Document(title=f["title"], content=f["content"], path=f["path"], date=f["date"],                              collection=collection)
                except Exception as e:
                    print("Couldn't create document " + f["title"] + "due to error:")
                    print(e)
    except Exception:
        for f in file_data:
            try:
                Document(title=f["title"], content=f["content"], path=f["path"], date=f["date"], collection=collection)
            except Exception as e:
                print("Couldn't create document " + f["title"] + "due to error:")
                print(e)

    return

def handle_zip(zip_path, id, zip_name):
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            # get the list of files
            names = zip_file.namelist()
            filedata = process_archive(zip_file, names, id)
        return filedata
    except Exception as e:
        print("Error! Zip could not be processed:")
        print(e)
        return [None]


def handle_tar(tar_path, id):
    try:
        with tarfile.TarFile(tar_path, "r") as tar_file:
            # get the list of files
            names = tar_file.getnames()
            filedata = process_archive(tar_file, names, id)
        return filedata
    except Exception as e:
        print("Error! Zip could not be processed:")
        print(e)
        return [None]

def process_archive(archive, names, id):
    filedata = []
    valid_formats = (
    ".txt", ".doc", ".docx", ".csv", ".json", ".xlsx", ".pptx", "pdf", ".epub", ".htm", ".html", ".tsv", ".xls",
    ".odt")

    dir_path = "/home/nsaef/projects/CollectionExplorer/tmp/"
    start = 0
    i = 10000
    end = min(start + i, len(names))

    while start < len(names):
        print("reading files " + str(start) + " to " + str(end) + " of " + str(len(names)) + " of files in archive")
        filedata = []
        # handle your files as you need. You can read the file with:
        for name in names[start:end]:
            if name.lower().endswith(valid_formats):
                archive.extract(name, path=dir_path)
                name_pos = name.rfind("/")
                fname = name[name_pos + 1:]
                path = dir_path + "/" + name
                dname = dir_path + name[:name_pos]

                data = process_textract(path, fname, remote=False, path=path)
                filedata.append(data)

                try:
                    os.remove(path)
                except OSError:
                    if os.path.isdir(path) and not os.listdir(path):
                        os.rmdir(path)
                except Exception as e:
                    print("Couldn't delete tmp files.")
                    print(e)
                try:
                    if os.path.exists(path) and os.path.isdir(dname) and not os.listdir(dname):
                        os.rmdir(dname)
                except Exception as e:
                    print("Couldn't remove folder.")
                    print(e)
            elif name.lower().endswith(".zip"):
                dir_path = "/home/nsaef/projects/CollectionExplorer/tmp/"
                path = dir_path + "/" + name
                archive.extract(name, path=dir_path)

                fs = handle_zip(path, name, id)
            elif name.lower().endswith(".tar"):
                dir_path = "/home/nsaef/projects/CollectionExplorer/tmp/"
                path = dir_path + "/" + name
                archive.extract(name, path=dir_path)

                fs = handle_tar(path, id)
        create_objects(id, filedata)
        start = end
        end = min(end + i, len(names))

        del filedata
        gc.collect()
    name_pos = names[0].rfind("/")
    dname = dir_path + names[0][:name_pos]
    try:
        shutil.rmtree(dname, ignore_errors=True)
    except Exception as e:
        print("Couldn't delete directory:")
        print(e)
    return

# def process_uploaded_file(fileobj, name, path, date):
#     data = None
#     name_low = name.lower()
#     if name_low.endswith(".txt"):
#         data = get_plain_text(fileobj, name, path, date)
#     elif name_low.endswith(".pdf"):
#         data = get_pdf_content(fileobj, path, name)
#     elif name_low.endswith(".docx"):  # what about dox?
#         data = get_docx_content(fileobj, path, name)
#     else:  # not a supported file format
#         print(name + " is not a supported file format")
#     #data["content"] = do_postprocessing(data["content"])
#     return data

def do_postprocessing(content):
    nul = '\x00'
    if content.find(nul):
        cleaned = content.replace(nul, " ")
        text = cleaned.strip()
        return text
    else:
        return content


def process_textract(name, fname, remote=True, zip=None, path=None):
    if remote is True:
        dir_path = "/home/nsaef/projects/CollectionExplorer/tmp/"
        zip.extract(name, path=dir_path)
        name_pos = name.rfind("/")
        dname = dir_path + name[:name_pos]
        path = dir_path + name

    f = {}
    date = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    f["date"] = timezone.make_aware(date, timezone.get_current_timezone(), is_dst=True)
    try:
        content = textract.process(path).decode("utf-8")
        f["content"] = do_postprocessing(content)
    except Exception as e:
        print("textract couldn't process file " + name)
        print(e)
        return None
    f["path"] = do_postprocessing(path)
    f["title"] = do_postprocessing(fname)

    if remote is True:
        os.remove(path)
        if not os.listdir(dname):
            os.rmdir(dname)
    if content != "":
        return f
    else: return None

# def get_plain_text(fileobj, name, path, date):
#     f = {}
#     try:
#         f["content"] = fileobj.read().decode('utf8')
#     except Exception as e:
#         print(e)
#         return None
#     f["date"] = date
#     f["path"] = path
#     f["title"] = name
#
#     return f
#
#
# def get_pdf_content(fileobj, path, title=None):
# #    try:
#     fo = BytesIO(fileobj.read())
#     # except UnicodeDecodeError:
#     #     fo = BytesIO(fileobj.read().decode("utf-8"))
#     date = False
#     doc_title = False
#
#     rsrc_mgr = PDFResourceManager()
#     retstr = StringIO()
#     codec = 'utf-8'
#     device = TextConverter(rsrc_mgr, retstr, codec=codec)
#     interpreter = PDFPageInterpreter(rsrc_mgr, device)
#     caching = True
#     pagenos = set()
#
#     try:
#         for page in PDFPage.get_pages(fo, pagenos, caching=caching,check_extractable=True):
#             if date is False:
#                 date = page.doc.info[0].get("CreationDate")
#             if doc_title is False:
#                 doc_title = page.doc.info[0].get("Title")
#             interpreter.process_page(page)
#         text = retstr.getvalue()
#     except Exception as e:
#         print(e)
#         return None
#
#     device.close()
#     retstr.close()
#
#     #D:20161231184921-07'00'
#     try:
#         #date = fileReader.documentInfo["/ModDate"]
#         year = int(date[2:6])
#         month = int(date[6:8])
#         day = int(date[8:10])
#         hour = int(date[10:12])
#         minute = int(date[12:14])
#         second = int(date[14:16])
#
#         # tz_indicator = date[16]
#         tz_hour = int(date[16:19])
#         tz_minute = int(date[20:-1])
#
#         tz_delta = datetime.timedelta(hours=tz_hour, minutes=tz_minute)
#         tz = datetime.timezone(tz_delta)
#         d = datetime.datetime(year, month, day, hour, minute, second, tzinfo=tz)
#     except Exception as e:
#         print(e)
#         d = datetime.datetime.now()
#
#     f = {}
#     f["date"] = d
#     f["title"] = determine_title(doc_title, title)
#     f["path"] = path
#     f["content"] = text
#
#     return f
#
#
# def get_docx_content(fileobj, path, title=None):
#     try:
#         fo = BytesIO(fileobj.read())
#     except UnicodeDecodeError as e:
#         print(e)
#         return None
#     try:
#         doc = DocX(fo)
#     except ValueError as e:
#         print(e)
#         return None
#
#     content = ""
#
#     for paragraph in doc.paragraphs:
#         content += paragraph.text + "\n"
#
#     f = {}
#     f["date"] = doc.core_properties.created
#     f["path"] = path
#     f["title"] = determine_title(doc.core_properties.title, title)
#     f["content"] = content
#
#     return f
#
#
# def determine_title(t1, t2):
#     title = "unbekannt"
#
#     if t1 is not None and t1 is not "":
#         title = t1
#     elif t2 is not None and t2 is not "":
#         title = t2
#     return title


@shared_task(base=CeleryBasicTask)
def get_doc2vec_model_async(model_path, str_collection_id, corpora_path=None):
    model_name = model_path + str_collection_id + ".model"
    embedder = doc_embedder()
    se = serializer()

    if corpora_path is not None:
        # get the tokenized model
        corpus_path = corpora_path + "/" + str_collection_id + "/" + str_collection_id + \
                      "_tokens_stopwords-included_cs.corpus"
        corpus_tokenized = se.load(corpus_path)
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
    docs_len = collection.documents.count()

    start = 0
    # i = 100000
    i = 10000
    end = min(start + i, docs_len)
    create_ix = True

    while end <= docs_len:
        if start > end:
            break
        if start > 0:
            create_ix = False
        print("Indexing docs " + str(start) + " to " + str(end) + " of " + str(docs_len))
        docs_qs = collection.documents.all()[start:end]
        docs = list(docs_qs.values())

        se.build_index(files=docs, create_ix=create_ix)

        start += i
        end = min(end + i, docs_len)

    #docs = list(collection.documents.values())
    #se.build_index(files=docs)
    return True


@shared_task(base=CeleryBasicTask)
def get_named_entities_async(type, id, corpora_path=None, n=20):
    ana = analyzer()
    se = serializer()
    type_map = ["location", "person", "organization", "other"]

    t0 = time()
    if type == "collection":
        name = str(id) + "_sents.corpus"
        sents = se.load(corpora_path + str(id) + "/" + name, type="list")
        col = Collection.objects.get(pk=id)

        i = 1000
        start = 0
        end = min(len(sents), i)

        entity_list = [Counter(), Counter(), Counter(), Counter()]

        while end < len(sents):
            if start > end: break
            print("Processing documents " + str(start) + "-" + str(end) + " of " + str(len(sents)))
            try:
                entities = ana.get_named_entities_sents(sents[start:end])

                print("Updating list of entities...")
                for idx, counter in enumerate(entities):
                    entity_list[idx] += counter
                start += i
                end = min(end+i, len(sents))
                #print("Done with batch")
            except Exception as e:
                print(e)
                break

        print("Bulk creating new entities...")
        for idx, counter in enumerate(entity_list):
            counter_len = len(counter)

            i = 50000
            start = 0
            end = min(counter_len, i)

            while start < end:
                objs = [Entity(name=el[0], frequency=el[1], type=type_map[idx], collection=col) for el in counter.most_common()[start:end]]
                Entity.objects.bulk_create(objs)
                del objs
                gc.collect()

                start += i
                end = min(end+i, counter_len)

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
    se = serializer()
    corpus_tokenized = se.load(corpus_path)
    collection = Collection.objects.get(pk=id)

    ana = analyzer()
    ngrams = ana.find_ngrams(corpus_tokenized, bigrams=bigrams, trigrams=trigrams)

    if bigrams is True:
        objs_bg = [Ngram(type="bigram", method=method, word1=item[0], word2=item[1], score=idx, collection=collection) for
                   method, word_list in ngrams["bigrams"].items() for idx, item in enumerate(word_list)]
        Ngram.objects.bulk_create(objs_bg)
        del objs_bg
        gc.collect()

    if trigrams is True:
        objs_tg = [Ngram(type="trigram", method=method, word1=item[0], word2=item[1], word3=item[2], score=idx,
                         collection=collection) for
                   method, word_list in ngrams["trigrams"].items() for idx, item in enumerate(word_list)]
        Ngram.objects.bulk_create(objs_tg)
        del objs_tg
        gc.collect()

    print("Done collection ngrams")
    return True

@shared_task(base=CeleryBasicTask)
def find_versions_async(corpus, save_path):
    vh = version_handler()

    #RISIKO: Hash dict wird zu groß für RAM
    hash_dict_list = []

    i = 1000
    start = 0
    end = min(len(corpus), i)

    while end < len(corpus):
        print("Processing documents " + str(start) + "-" + str(end) + " of " + str(len(corpus)))
        try:
            chunk = {k: corpus[k] for k in islice(corpus, start, end)}
            hashes = vh.calc_hashes(chunk)
            hash_dict_list.append(hashes)
            del hashes
            del chunk
            gc.collect()

            start += i
            end = min(end+i, len(corpus))
        except Exception as e:
            print(e)
            break

    hashes = {}
    for l in hash_dict_list:
        hashes.update(l)

    vh.calculate_similarities(hashes=hashes, threshold=0.5, save_path=save_path)
    vh.clear_data(hashes=True)

    create_version_relationships(vh.version_candidates, vh.duplicates)
    vh.clear_data(duplicates=True, versions=True)
    return

def create_version_relationships(version_candidates, duplicates, method="MinHash"):
    print("Creating duplicate relationships...")
    t0 = time()
    for src_doc_id, duplicates in duplicates.items():
        src_doc = Document.objects.get(pk=int(src_doc_id))

        for dup_id in duplicates:
            d = Document.objects.get(pk=int(dup_id))
            src_doc.duplicates.add(d)
            src_doc.save()
    print("done in %0.3fs." % (time() - t0))
    del duplicates
    gc.collect()

    print("Creating possible version relationships...")
    t0 = time()
    for src_doc_id, versions in version_candidates.items():
        src_doc = Document.objects.get(pk=int(src_doc_id))

        for v_id, score in versions:
            v_doc = Document.objects.get(pk=int(v_id))

            version = Version(candidate=v_doc, version_of=src_doc, similarity_measure=method, similarity_score=score)
            version.save()
    del version_candidates
    gc.collect()
    print("done in %0.3fs." % (time() - t0))


# def pickle_similarities(sims, path):
#     for doc_id, values in sims.items():
#         folder_path = path + str(doc_id)
#         if not os.path.exists(folder_path):
#             os.mkdir(folder_path)
#
#         filepath = folder_path + "/" + str(doc_id) + "_similarities.corpus"
#         pickle.dump(values, open(filepath, 'wb'))


def make_versions_from_similarities(id, collection=True, document=False, filter_existing=False):
    if collection is True:
        c = Collection.objects.get(pk=id)
        if filter_existing is False:
            docs = c.documents.all()
        else:
            #TODO: filter_existing in make_versions
            #duplicates and versions count == 0
            docs = c.documents.filter()
        for doc in docs:
            process_saved_similarities(doc.id)
    elif document is True:
        process_saved_similarities(id)
    return

def process_saved_similarities(id, threshold=0.5, method="MinHash"):
    doc_id = str(id)
    static_path = settings.BASE_DIR + "/CollectionExplorer" + static("CollectionExplorer/")
    sims_path = static_path + "similarities/" + doc_id

    if os.path.exists(sims_path):
        duplicates = {}
        version_candidates = {}

        filepath = sims_path + "/" + doc_id + "_similarities.corpus"
        candidates = pickle.load(open(filepath, 'rb'))

        #candidates = [(doc_id, score) for doc_id, score in sims.items() if score > threshold]
        for doc_id, score in candidates:
            if score == 1.0:
                if id not in duplicates:
                    duplicates[id] = []
                duplicates[id].append(doc_id)
            else:
                if id not in version_candidates:
                    version_candidates[id] = []
                version_candidates[id].append((doc_id, score))

        #add duplicate and version relationships
        src_doc = Document.objects.get(pk=id)

        for dup_id in duplicates:
            d = Document.objects.get(pk=int(dup_id))
            src_doc.duplicates.add(d)
            src_doc.save()

        for v_id, score in version_candidates:
            v_doc = Document.objects.get(pk=int(v_id))

            version = Version(candidate=v_doc, version_of=src_doc, similarity_measure=method,
                              similarity_score=score)
            version.save()
    return




























