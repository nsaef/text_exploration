import os, os.path
from whoosh import index
from whoosh.index import create_in
from whoosh.fields import *
from whoosh import qparser
from whoosh.qparser import QueryParser
from time import time
import datetime


class SearchEngine(object):
    def __init__(self):
        self.index_dir = "D:/Uni/Masterarbeit/index"
        self.schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT(stored=True), date=DATETIME(stored=True))
        self.ix = None
        if not os.path.exists(self.index_dir):
            os.mkdir(self.index_dir)

        if index.exists_in(self.index_dir):
            print("Loading index...")
            self.ix = index.open_dir(self.index_dir)
            self.writer = self.ix.writer()
        else:
            self.build_index(u"D:/Uni/Masterarbeit/Beispieldaten/Wiki_partial_corpus")
        self.searcher = self.ix.searcher()
        return

    def search(self, query):
        parser = QueryParser("content", self.ix.schema)
        parser.add_plugin(qparser.FuzzyTermPlugin())
        myquery = parser.parse(query)
        results = self.searcher.search(myquery)
        print(len(results), " results in total")
        #print(results[0:results.scored_length()])
        for hit in results[0:results.scored_length()]:
            print(hit["title"])
            # Assume "content" field is stored
            print(hit.highlights("content"))

    def build_index(self, file_dir):
        print("Creating a new index...")
        t0 = time()

        self.ix = index.create_in(self.index_dir, schema=self.schema)
        self.writer = self.ix.writer(limitmb=2048) #, procs=2, multisegment=True #check: AsyncWriter, BufferedWriter

        if os.path.exists(file_dir):
            files = os.listdir(file_dir)
            for file in files:
                path = file_dir + "/" + file
                if os.path.isdir(path) is True: continue
                self.add_doc(file, path)
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


