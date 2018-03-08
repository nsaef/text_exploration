from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.index, name='index'),
    path("docs/<int:doc_id>/", views.document_detail, name="document_detail"),
    path("collections/<int:collection_id>/", views.collection_detail, name="collection_detail"),
    path("search_action/<int:query_id>/results.html", views.results, name="results"),
    path("search_action/", views.search_action, name="search_action")
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)