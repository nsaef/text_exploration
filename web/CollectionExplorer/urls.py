from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path("collections/<int:collection_id>/docs/<int:pk>/", views.DocumentDetail.as_view(), name="document_detail"),
    path("collections/<int:pk>/statistics", views.collection_statistics, name="collection_statistics"),
    path("collections/<int:pk>/semantics", views.collection_semantics, name="collection_semantics"),
    path("collections/<int:pk>/", views.CollectionDetail.as_view(), name="collection_detail"),
    path("results", views.results, name="results"),
    path("add_collection/", views.add_collection, name="add_collection"),
    path("add_docs/<int:pk>/", views.add_docs_to_collection, name="add_docs"),
    path("upload_files/<int:pk>/", views.upload_files, name="upload_files"),
    path("create_file/<int:pk>/", views.create_file, name="create_file"),
    path("find_versions/<int:pk>/", views.find_versions_duplicates, name="find_versions"),
    path("edit_favorite/<int:pk>/", views.edit_favorite, name="edit_favorite"),
    path("save_note/<int:pk>/", views.save_note, name="save_note"),
    path("vocabulary/<int:pk>/", views.analyse_vocabulary, name="analyse_vocabulary"),
    path("network/<int:pk>/", views.network, name="network")
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)