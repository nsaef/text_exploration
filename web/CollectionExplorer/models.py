from django.db import models
import os, os.path
import datetime
import codecs

# Create your models here.
def create_upload_filename(self):
    return "collections/" + str(self.id)

class Collection(models.Model):
    title = models.CharField(max_length=512)
    path = models.FilePathField(path=r"D:\Uni\Masterarbeit", recursive=True, allow_files=False, allow_folders=True, max_length=1024)

    class Meta:
        db_table = "collectionexplorer_collection"

    def __str__(self):
        return str(self.title)

    @property
    def unique_docs(self):
        dups = []
        uniques = []
        result = {}

        for doc in self.documents.all():
            if doc not in dups:
                uniques.append(doc)
                dups.extend(doc.duplicates.all())
        result["unique_docs"] = uniques
        result["duplicates"] = dups
        return result

    @property
    def most_frequent_entities(self, type=None):
        if not type:
            results = self.entities.order_by("type", "-frequency")[0:10000]
        else:
            results = self.entities.filter(type=type).order_by("-frequency")[0:10000]
        return results

    @property
    def bigrams_frequent(self):
        return self.ngrams.filter(type="bigram", method="most_frequent").order_by("-score")

    @property
    def bigrams_pmi(self):
        return self.ngrams.filter(type="bigram", method="pmi").order_by("-score")

    @property
    def trigrams_frequent(self):
        return self.ngrams.filter(type="trigram", method="most_frequent").order_by("-score")

    @property
    def trigrams_pmi(self):
        return self.ngrams.filter(type="trigram", method="pmi").order_by("-score")

#TODO: Property "interesting"/appraisal status
class Document(models.Model):
    title = models.TextField()
    content = models.TextField(default="")
    path = models.FilePathField(max_length=1024, recursive=True)
    date = models.DateTimeField('date created', blank=True, null=True)
    collection = models.ForeignKey(Collection, related_name='documents', on_delete=models.CASCADE)
    duplicates = models.ManyToManyField("self")
    version_candidates = models.ManyToManyField("self", through="Version", symmetrical=False)
    interesting = models.BooleanField(blank=True, null=True)
    note = models.TextField(default="")

    class Meta:
        db_table = "collectionexplorer_document"

    def __str__(self):
        return self.title

    @property
    def most_frequent_entities(self, type=None):
        if not type:
            results = self.entities.order_by("type", "-frequency")[0:10000]
        else:
            results = self.entities.filter(type=type).order_by("-frequency")[0:10000]
        return results

class Version(models.Model):
    candidate = models.ForeignKey(Document, related_name="original", on_delete=models.PROTECT)
    version_of = models.ForeignKey(Document, related_name="version", on_delete=models.PROTECT)
    similarity_measure = models.CharField(max_length=100, blank=True, null=True)
    similarity_score = models.DecimalField(max_digits=3, decimal_places=2)


class Entity(models.Model):
    name = models.TextField()
    frequency = models.IntegerField(default=0)
    collection = models.ForeignKey(Collection, related_name='entities', on_delete=models.CASCADE, blank=True, null=True)
    document = models.ForeignKey(Document, related_name='entities', on_delete=models.CASCADE, blank=True, null=True)

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

    class Meta:
        db_table = "collectionexplorer_entity"

    def __str__(self):
        return str(self.name)


class Ngram(models.Model):
    BIGRAM = "bigram"
    TRIGRAM = "trigram"
    TYPE_CHOICES = (
        (BIGRAM, "Bigram"),
        (TRIGRAM, "Trigram")
    )

    PMI = "pmi"
    MOST_FREQ = "most_frequent"
    METHOD_CHOICES = (
        (PMI, "Pointwise Mutual Information"),
        (MOST_FREQ, "Häufigste N-Gramme")
    )

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    word1 = models.CharField(max_length=512)
    word2 = models.CharField(max_length=512)
    word3 = models.CharField(max_length=512, blank=True)
    score = models.FloatField()
    collection = models.ForeignKey(Collection, related_name='ngrams', on_delete=models.CASCADE, blank=True, null=True)
    document = models.ForeignKey(Document, related_name='ngrams', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = "collectionexplorer_ngram"

    def __str__(self):
        result = self.word1 + " " + self.word2
        if self.word3:
            result += " " + self.word3
        return result
