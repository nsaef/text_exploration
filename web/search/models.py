from django.db import models
import os, os.path
import datetime

# Create your models here.
class Query(models.Model):
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text

class Document(models.Model):
    title = models.CharField(max_length=500)
    content = models.TextField(default="")
    path = models.FilePathField(path=r"D:\Uni\Masterarbeit\Beispieldaten\Wiki_partial_corpus", recursive=True)
    date = models.DateTimeField('date created')

    def __str__(self):
        return self.title

class Result(models.Model):
    count = models.IntegerField(default=0)
    document = models.ManyToManyField(Document)
    query = models.ManyToManyField(Query)

    def __str__(self):
        return str(self.count)

class History(models.Model):
    length = models.IntegerField(default=10)
    query = models.ManyToManyField(Query)


# class Collection(models.Model):
#     title = models.CharField(max_length=200)
#     documents = models.ManyToManyField(Document)
#
#     def __str__(self):
#         return self.title
#
#     def create_collection(self, *args, **kwargs):
#         self.title = kwargs.pop("title", None)
#         #self.documents = {}

# class: Data_source mit title und path
# enthält Funktion, die aus data source automatisch eine collection erstellt - ohne path, mit documents
class Collection(models.Model):
    title = models.CharField(max_length=200)
    path = models.FilePathField(path=r"D:\Uni\Masterarbeit", recursive=True, allow_files=False, allow_folders=True)
    documents = models.ManyToManyField(Document, blank=True)
    changes = models.BooleanField()

    def add_docs_to_collection(self):
        if os.path.exists(self.path):
            files = os.listdir(self.path)
            for file in files:
                filepath = self.path + "/" + file
                if os.path.isdir(filepath) is True:
                    continue
                fileobj = open(filepath, "r", encoding="utf-8")
                content = fileobj.read()
                fileobj.close()
                date = datetime.datetime.utcfromtimestamp(os.path.getmtime(filepath))
                d = Document(title=file, content=content, path=filepath, date=date)
                d.save()
                print(d)
                self.documents.add(d)
            self.save()






