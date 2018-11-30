import pickle
import os
from itertools import islice
import shutil
import math
import gc
import uuid
from scipy import sparse


class Serializer(object):
    def __init__(self):
        return

    def save(self, object, path, limit=10000, type="dict", folder=False, overwrite=False):
        print("Saving...")
        if os.path.exists(path) and overwrite is True:
            print("Removing old files...")
            try:
                os.remove(path)
            except OSError:
                shutil.rmtree(path, ignore_errors=True)
        try:
            gc.collect()

            if folder is True:
                if not os.path.exists(path):
                    os.mkdir(path)
                fname = str(uuid.uuid4())
                p = path + "/" + fname
                try:
                    pickle.dump(object, open(p, 'wb'))
                except MemoryError:
                    self.save(object, path, folder=False)
            else:
                pickle.dump(object, open(path, 'wb'))
            print("Saved file as " + path)
        except MemoryError:
            print("Object too big for pickle. Splitting the object...")
            os.remove(path)
            os.mkdir(path)
            start = 0

            if type is "dict":
                end = int(math.ceil(len(object)/limit))
                for i in range(0, end):
                    print("Saving part " + str(i + 1) + ": " + str(start) + "-" + str(limit))
                    chunk = {k: object[k] for k in islice(object, start, limit)}
                    fname = str(uuid.uuid4())
                    p = path + "/" + fname
                    try:
                        pickle.dump(chunk, open(p, 'wb'))
                        del chunk
                        gc.collect()
                    except Exception as e:
                        print(e)

                    start += limit
                    limit += limit
                    print("Saved file in " + p)

            elif type is "csr_matrix":
                fname = str(uuid.uuid4())
                p = path + "/" + fname
                sparse.save_npz(p, object)

        except Exception as e:
            print(e)

    def load(self, path, type="dict"):
        gc.collect()
        if os.path.isfile(path):
            return pickle.load(open(path, "rb"))
        elif os.path.isdir(path):
            files = os.listdir(path)
            result = None

            if type is "dict":
                result = {}
                for i, file in enumerate(files):
                    print("Loading partial file " + str(i) + " of " + str(len(files)))
                    fpath = path + "/" + file
                    try:
                        obj = pickle.load(open(fpath, "rb"))
                    except Exception as e:
                        print("Couldn't read file " + str(i) + ": " + fpath)
                        print(e)
                        obj = {}
                    result.update(obj)

            elif type is "list":
                result = []
                for file in files:
                    obj = pickle.load(open(path + "/" + file, "rb"))
                    result += obj

            elif type is "csr_matrix":
                if len(files) == 1:
                    p = path + "/" + files[0]
                    try:
                        result = sparse.load_npz(p)
                    except Exception:
                        result = pickle.load(open(p, "rb"))
            return result