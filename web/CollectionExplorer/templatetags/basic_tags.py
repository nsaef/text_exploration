from django import template
import django.db
from CollectionExplorer.models import Collection
from CollectionExplorer.tasks import add

register = template.Library()

@register.simple_tag
def get_collection_list():
    return Collection.objects.all()

@register.simple_tag
def async_add(a, b):
    res = add.delay(a, b)
    return res.get()

@register.simple_tag
def clear_old_connections():
    django.db.close_old_connections()
    return

@register.simple_tag
def get_item(dict, key):
    item = dict.get(key, None)
    return item