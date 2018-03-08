import os
from time import time



# path = r"D:/Uni/Masterarbeit/Beispieldaten/Wikipedia de plain text/text/20140616-wiki-de_001320/20140616-de-index.txt"
# titles = []
# blacklist = ["Kategorie:", "Vorlage:", "Datei:", "Benutzer:", "Wikipedia:", "Portal:", "|"]
#
# if os.path.exists(path):
#     t0 = time()
#     with open(path, "r", encoding="utf8", newline="\n") as f:
#         reader = csv.reader(f, delimiter='\t')
#         for row in reader:
#             add = True
#             for word in blacklist:
#                 if word in row[1]:
#                     add = False
#             if add == True: titles.append(row[1])
#
# titles.sort(key=len, reverse=True)
#
# print("done in %fs" % (time() - t0))
#
# for i, title in enumerate(titles[0:50]):
#     print("(", i+1, ")", len(title), " Zeichen: ", title)