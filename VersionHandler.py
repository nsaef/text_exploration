from datasketch import *
from time import time

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


    def calc_hashes(self, corpus, hash_type="MinHash"):
        print("Calculating hash values for all documents...")
        t0 = time()
        self.method = hash_type
        output = None

        for id, doc in corpus.items():
            hash = MinHash()

            if hash_type is "LSHEnsemble":
                doc = set(doc)
                self.lsh_ensemble_setlen[id] = len(doc)

            for word in doc:
                hash.update(word.encode("utf-8"))

            if hash_type is "MinHash":
                hash = LeanMinHash(hash)

            self.hashes[id] = hash

        print("created hash dict")
        output = self.hashes

        if hash_type is "LSHEnsemble":
            print("Using MinHash values to create an LSH Ensemble index...")
            lshensemble = MinHashLSHEnsemble(threshold=0.8, num_perm=128)
            items = [(id, hash, self.lsh_ensemble_setlen[id]) for id, hash in self.hashes.items()]
            lshensemble.index(items)
            self.lsh_ensemble = lshensemble
            output = self.lsh_ensemble

        print("done in %0.3fs." % (time() - t0))
        return output


    # hashes = dict of similarities, output of calc_hashes
    def calculate_similarities(self, threshold=0.9, hashes=None, lsh_ensemble=False):
        print("Calculating document similarities...")
        t0 = time()
        sims = {}

        if hashes is None:
            hashes = self.hashes

        if lsh_ensemble is True:
            for id in self.hashes.keys():
                #sims[id] = {id:key for key in hash.query(id, self.hashes[str(id) + "_len"])}
                doc_len = self.lsh_ensemble_setlen.get(id)
                min_hash = self.hashes.get(id)
                test = self.lsh_ensemble.query(min_hash, doc_len)
                for key in test:
                    sims[id] = {id:key}
        else:
            for id, hash in hashes.items():
                sims[id] = {i:hash.jaccard(h) for i, h in hashes.items() if id != i}

        self.similarities = sims

        for id, doc in sims.items():
            for doc_id, score in doc.items():
                if score == 1.0:
                    if id not in self.duplicates:
                        self.duplicates[id] = []
                    self.duplicates[id].append(doc_id)
                elif score > threshold:
                    if id not in self.version_candidates:
                        self.version_candidates[id] = []
                    self.version_candidates[id].append((doc_id, score))

        print("done in %0.3fs." % (time() - t0))
        return self.version_candidates


    def compare_docs(self):
        return