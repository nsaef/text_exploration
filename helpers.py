import pickle
import os

def save_file(object, name, path="D:/Drive/Uni/Python/text_processing_wiki/resources/corpora/"):
    p = path + name + ".pkl"
    try:
        pickle.dump(object, open(p), 'wb')
        print("Saved file in " + p)
    except MemoryError:
        dir = path + name
        os.mkdir(dir)
        for i in range(0, len(object)):
            p = dir + "/part_" + str(i)
            try:
                pickle.dump(object[i:i+100000], open(p), 'wb')
            except IndexError:
                pickle.dump(object[i:], open(p), 'wb' )
            i += 1000000
            print("Saved file in " + p)
    return


def load_file(name, path="resources/corpora/"):
    p = path + name
    if os.path.isfile(p):
        return pickle.load(open(p, "rb"))
    elif os.path.isdir(p):
        result = []
        files = os.listdir(p)
        for file in files:
            obj = pickle.load(open(p + "/" + file, "rb"))
            [result.extend(item) for item in obj]
        return result

