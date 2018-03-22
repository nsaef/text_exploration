from django.db import models
import os, os.path
import datetime
import codecs

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


class Entity(models.Model):
    name = models.CharField(max_length=500)
    frequency = models.IntegerField(default=0)

    PERSON = "person"
    LOCATION = "location"
    ORGANIZATION = "organization"
    OTHER = "other"
    TYPE_CHOICES = (
        (PERSON, "Person"),
        (LOCATION, "Ort"),
        (ORGANIZATION, "Organisation"),
        (OTHER, "Weitere")
    )

    type = models.CharField(max_length=50, choices=TYPE_CHOICES)

    def __str__(self):
        return str(self.name)


class Collection(models.Model):
    title = models.CharField(max_length=200)
    path = models.FilePathField(path=r"D:\Uni\Masterarbeit", recursive=True, allow_files=False, allow_folders=True)
    documents = models.ManyToManyField(Document, blank=True)
    entities = models.ManyToManyField(Entity, blank=True)


    def __str__(self):
        return str(self.title)

    def add_docs_to_collection(self):
        if os.path.exists(self.path):
            files = os.listdir(self.path)
            for file in files:
                filepath = self.path + "/" + file
                if os.path.isdir(filepath) is True:
                    continue
                if self.documents.filter(path=filepath).count() > 0:
                    continue
                with codecs.open(filepath, "r", encoding="utf-8") as fileobj:
                    content = fileobj.read()
                    date = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                    d = Document(title=file, content=content, path=filepath, date=date)
                    d.save()
                    self.documents.add(d)
            self.save()

