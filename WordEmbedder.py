import gensim
import os.path

class WordEmbedder(object):
    def __init__(self, type="word2vec", size=100, window=7, min_count=2, workers=4):
        self.embedder = type
        if type == "word2vec":
            self.w2v_size = size
            self.w2v_window = window
            self.w2v_min_count = min_count
            self.w2v_workers = workers

    def saveWord2Vec(self, path):
        f = open(path, 'w')
        self.model.save(path)
        f.close()
        print("Saved model in file "+path)

    def loadWord2Vec(self, path):
        self.model = gensim.models.Word2Vec.load(path).wv
        print("Model loaded")

    def run(self, input, filename=None):
        if self.embedder == "word2vec":
            if filename != None:
                path = r"D:\Dropbox\Uni\Python\text_processing_wiki\resources\model_" + filename + ".mdl"

                if os.path.isfile(path):
                    self.loadWord2Vec(path)
                else:
                    self.word2vec(input)
                    self.saveWord2Vec(path)
            else:
                self.word2vec(input)
        return self.model


    def word2vec(self, input):
        """ Run word2vec on the dataset. Standard input: tokenized data. Other input data can be specified via the "input"-parameter."""
        print("Running word2vec...")
        self.model = gensim.models.Word2Vec(input, size=self.w2v_size, window=self.w2v_window, min_count=self.w2v_min_count, workers=self.w2v_workers)
        return self.model.wv