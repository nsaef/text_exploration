from search.models import Collection, Document
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import os, os.path
import datetime


@receiver(post_save, sender=Collection)
def add_docs_to_collection(sender, **kwargs):
    def on_commit():
        if sender.changes is True:
            if os.path.exists(sender.path):
                files = os.listdir(sender.path)
                for file in files:
                    filepath = sender.path + "/" + file
                    if os.path.isdir(filepath) is True:
                        continue
                    fileobj = open(filepath, "r", encoding="utf-8")
                    content = fileobj.read()
                    fileobj.close()
                    date = datetime.datetime.utcfromtimestamp(os.path.getmtime(filepath))
                    d = Document.objects.create_document(title=file, content=content, path=filepath, date=date)
                    d.save()
                    print(d)
                    sender.documents.add(d)
                sender.save()

    transaction.on_commit(on_commit)