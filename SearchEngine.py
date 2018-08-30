import os, os.path
from whoosh import index
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.writing import AsyncWriter
from whoosh import qparser
from whoosh.qparser import QueryParser
from time import time
import datetime


class SearchEngine(object):
    def __init__(self, index_path, collection_id, local=False, collection_path=None):
        self.index_dir = index_path + str(collection_id)
        self.schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True), date=DATETIME(stored=True))
        self.ix = None
        if not os.path.exists(self.index_dir):
            os.mkdir(self.index_dir)

        if index.exists_in(self.index_dir):
            print("Loading index...")
            self.ix = index.open_dir(self.index_dir)
            self.writer = AsyncWriter(self.ix)
        elif local is False:
            print("Build index from Django docs in separate step!")
            return
        else:
            self.build_index(collection_path)
        self.searcher = self.ix.searcher()
        return

    def search(self, query, limit=None):
        parser = QueryParser("content", self.ix.schema)
        parser.add_plugin(qparser.FuzzyTermPlugin())
        myquery = parser.parse(query)
        results = {"searcher": self.searcher}
        results["result"] = self.searcher.search(myquery, limit=limit)
        # print(len(results), " results in total")
        # #print(results[0:results.scored_length()])
        # for hit in results[0:results.scored_length()]:
        #     print(hit["title"])
        #     # Assume "content" field is stored
        #     print(hit.highlights("content"))
        return results

    def build_index(self, file_dir=None, files=None):
        print("Creating a new index...")
        t0 = time()

        self.ix = index.create_in(self.index_dir, schema=self.schema)
        self.writer = self.ix.writer(limitmb=2048) #, procs=2, multisegment=True #check: AsyncWriter, BufferedWriter

        if file_dir is not None and os.path.exists(file_dir):
            files = os.listdir(file_dir)
            for file in files:
                path = file_dir + "/" + file
                if os.path.isdir(path) is True: continue
                self.add_doc(file, path)

        elif files is not None:
            for doc in files:
                self.writer.add_document(title=doc["title"], path=doc["path"], content=doc["content"], date=doc["date"])
        self.writer.commit()

        print("done in %fs" % (time() - t0))
        return

    def add_doc(self, title, path):
        fileobj = open(path, "r", encoding="utf-8")
        content = fileobj.read()
        fileobj.close()
        modtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(path))
        #modtime = d.fromtimestamp(os.path.getmtime(path))
        self.writer.add_document(title=title, path=path, content=content, date=modtime) #if there are problems they're due to the modtime
        return


