import os
from time import time
import random
import codecs

class Reader(object):

    def __init__(self, source="wikipedia"):
        self.source = source

        if source == "wikipedia":
            self.corpus = self.readWikiFiles()

    def readWikiFiles(self):
        articles = []
        wiki_path = r"D:/Uni/Masterarbeit/Beispieldaten/Wikipedia de plain text/text/20140616-wiki-de_001320"

        if os.path.exists(wiki_path):
            t0 = time()
            files = os.listdir(wiki_path)
            for file in files:
                path = wiki_path + "/" + file
                with open(path, "r", encoding="utf8") as f:
                    if file == "20140616-de-index.txt":
                        continue

                    text = f.read()
                    end = False
                    i = 0

                    while end == False:
                        add = True
                        start = text.find("[[", i)
                        next = text.find("[[", start+1)
                        blacklist = ["[[Kategorie:", "[[Vorlage:", "[[Datei:", "[[Benutzer:", "[[Wikipedia:", "[[Portal:",
"#redirect", "#REDIRECT", "#WEITERLEITUNG", "#weiterleitung"]
                        article = None

                        if next == -1:
                            end = True
                            article = text[start:-1]
                            #articles.append(text[start:-1])
                        else:
                            #articles.append(text[start:next-1])
                            article = text[start:next-1]
                            i = next

                        for word in blacklist:
                            if word in article:
                                add = False
                                break

                        if add == True:
                            articles.append(article)

            print("done in %fs" % (time() - t0))
            return articles
        else:
            print("Path not valid")

    def prepare_corpus(self, shuffle=True, size=0):
        if shuffle == True:
            print("shuffling...")
            random.shuffle(self.corpus)

        if size > 0:
            print("reducing corpus size to %d" % size)
            c = self.corpus[:size]
        else:
            c = self.corpus
        return c

    def write_reduced_corpus(self, corpus, directory):
        if not directory:
            directory = r"D:/Uni/Masterarbeit/Beispieldaten/Wiki_partial_corpus/"
        for doc in corpus:
            try:
                title = doc[2:doc.find("]]")].replace("/", " ")
                path = directory + title + ".txt"
                file = codecs.open(path, "w", "utf-8")
                file.write(doc)
                file.close()
            except(OSError):
                continue


