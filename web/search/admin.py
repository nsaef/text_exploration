from django.contrib import admin
from .models import Document, Query, Collection

# Register your models here.
admin.site.register(Document)
admin.site.register(Collection)