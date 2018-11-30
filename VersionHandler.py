from datasketch import *
from time import time
import os
import pickle
import gc

class VersionHandler(object):

    def __init__(self):
        self.version_candidates = {}
        self.duplicates = {}
        self.hashes = {}
        self.method = None
        self.lsh_ensemble = {}
        self.lsh_ensemble_setlen = {}
        self.similarities = {}
        return


    def clear_data(self, hashes=False, duplicates=False, versions=False):
        if hashes is True:
            del self.hashes
        if duplicates is True:
            del self.duplicates
        if versions is True:
            del self.version_candidates
        gc.collect()
        return


    def calc_hashes(self, corpus, hash_type="MinHash"):
        print("Calculating hash values for all documents...")
        t0 = time()
        self.method = hash_type
        hashes = {}
        output = None

        for id, doc in corpus.items():
            hash = MinHash()

            for word in doc:
                hash.update(word.encode("utf-8"))

            hash = LeanMinHash(hash)
            hashes[id] = hash

        print("created hash dict")

        print("done in %0.3fs." % (time() - t0))
        return hashes

    # hashes = dict of similarities, output of calc_hashes
    def calculate_similarities(self, threshold=0.9, hashes=None, lsh_ensemble=False, save_path=None, save_files=False):
        print("Calculating document similarities...")
        t0 = time()
        #sims = {}

        if hashes is None:
            hashes = self.hashes

        # comparisons are bidirectional (if I compare A to B I also compare B to A)
        # so I keep track of all finished comparisons and skip them in future runs
        skip = []

        for id, hash in hashes.items():
            #sims[id] = {i:hash.jaccard(h) for i, h in hashes.items() if id != i}
            #print("calculate similarities for doc ", id)
            sims = {i: hash.jaccard(h) for i, h in hashes.items() if id != i and i not in skip}

            #print("Comparing scores to find duplicates and version candidates...")
            candidates = [(doc_id, score) for doc_id, score in sims.items() if score > threshold]
            for doc_id, score in candidates:
                if score == 1.0:
                    if id not in self.duplicates:
                        self.duplicates[id] = []
                    self.duplicates[id].append(doc_id)
                else:
                    if id not in self.version_candidates:
                        self.version_candidates[id] = []
                    self.version_candidates[id].append((doc_id, score))
            skip.append(id)

            if save_files is True:
                folder_path = save_path + str(id)
                if not os.path.exists(folder_path):
                    os.mkdir(folder_path)
                filepath = folder_path + "/" + str(id) + "_similarities.corpus"
                pickle.dump(candidates, open(filepath, 'wb'))

            #print("pickle similarities")
            # for doc_id, values in sims.items():
            #     folder_path = save_path + str(doc_id)
            #     if not os.path.exists(folder_path):
            #         os.mkdir(folder_path)
            #
            #     filepath = folder_path + "/" + str(doc_id) + "_similarities.corpus"
            #     pickle.dump(values, open(filepath, 'wb'))
            del sims
            del candidates
            gc.collect()

        print("done in %0.3fs." % (time() - t0))
        return self.version_candidates


    def compare_docs(self):
        return