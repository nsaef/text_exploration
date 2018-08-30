import gensim
import os.path
from time import time, localtime, strftime
from random import randint

class DocEmbedder(object):
    #TODO: Always adapt to power of current machine
    def __init__(self, size=100, window=8, min_count=1, workers=10):
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

    def run(self, filename=None, path=None, corpus=None):
        if filename != None:
            path = r".\resources\model_" + filename + ".mdl"

        if path != None:
            if os.path.isfile(path):
                self.loadDoc2Vec(path)
            else:
                if self.documents is None and corpus is not None:
                    self.prepare_corpus(corpus)
                self.doc2vec()
                self.saveDoc2Vec(path)
        else:
            self.doc2vec()
        return self.model

    def prepare_corpus(self, corpus):
        print("Preparing corpus for doc2vec")
        t0 = time()
        taggedDocs = []
        for id, doc in corpus.items():
            d = gensim.models.doc2vec.TaggedDocument(doc, [id])
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

        print("Finding documents similar to document with the id ", doc_id,  " in a corpus of size ", len(corpus), ":\n", file=f)

        try:
            most_sim = self.model.docvecs.most_similar(doc_id, topn=topn)
        except KeyError as e:
            most_sim = []
            print(e)

        #print("Document:", file=f)
       # print(corpus[doc_id][0:150], "...\n", file=f)

        results = []
        print("Most similar ", topn, " documents from the corpus:\n", file=f)
        for i, result in enumerate(most_sim):
            #print("doc nr. ", i, ", score: ", result[1], file=f)
            id = result[0]
            score = result[1]
            #text = corpus[id]
            #print(text[0:300], "...\n", file=f)
            results.append((id, score))

        if print_results is True:
            f.close()
            print("result saved in " + path)
        return results

