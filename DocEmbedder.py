import gensim
import os.path
from time import time, localtime, strftime
from random import randint

class DocEmbedder(object):
    def __init__(self, size=100, window=8, min_count=1, workers=4):
        self.d2v_size = size
        self.d2v_window = window
        self.d2v_min_count = min_count
        self.d2v_workers = workers
        self.documents = None

    def saveDoc2Vec(self, path):
        f = open(path, 'w')
        self.model.save(path)
        f.close()
        print("Saved model in file "+path)

    def loadDoc2Vec(self, path):
        self.model = gensim.models.Doc2Vec.load(path)
        print("Model loaded")

    def run(self, filename=None):
        if filename != None:
            path = r".\resources\model_" + filename + ".mdl"

            if os.path.isfile(path):
                self.loadDoc2Vec(path)
            else:
                self.doc2vec()
                self.saveDoc2Vec(path)
        else:
            self.doc2vec()
        return self.model

    def prepare_corpus(self, corpus):
        print("Preparing corpus for doc2vec")
        t0 = time()
        taggedDocs = []
        for idx, doc in enumerate(corpus):
            d = gensim.models.doc2vec.TaggedDocument(doc, [idx])
            taggedDocs.append(d)
        self.documents = taggedDocs
        print("done in %fs" % (time() - t0))
        return

    def doc2vec(self):
        """ Run doc2vec on the dataset. Standard input: tokenized data. Other input data can be specified via the "input"-parameter."""
        print("Running doc2vec...")
        t0 = time()
        self.model = gensim.models.Doc2Vec(documents=self.documents, size=self.d2v_size, window=self.d2v_window, min_count=self.d2v_min_count, workers=self.d2v_workers)
        print("done in %fs" % (time() - t0))
        return self.model


    def show_similar_docs(self, corpus, doc_id=None, topn=30, print_results=False):
        if doc_id is None:
            doc_id = randint(0, len(corpus))

        if print_results is True:
            timestamp = strftime("%Y-%m-%d_%H-%M-%S", localtime())
            path = r".\results\similar_docs\similar_docs_" + str(doc_id) + "_" + timestamp + ".txt"
            f = open(path, 'w', encoding="utf-8")
        else:
            f = None

        print("Finding documents similar to index ", doc_id,  " in a corpus of size ", len(corpus), ":\n", file=f)

        most_sim = self.model.docvecs.most_similar(doc_id, topn=topn)

        print("Document:", file=f)
        print(corpus[doc_id][0:500], "...\n", file=f)

        print("Most similar ", topn, " documents from the corpus:\n", file=f)
        for i, result in enumerate(most_sim):
            print("doc nr. ", i, ", score: ", result[1], file=f)
            text = corpus[result[0]]
            print(text[0:300], "...\n", file=f)

        if print_results is True:
            f.close()
            print("result saved in " + path)
        return
