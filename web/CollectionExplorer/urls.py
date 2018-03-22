from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path("docs/<int:pk>/", views.DocumentDetail.as_view(), name="document_detail"),
    path("collections/<int:pk>/", views.CollectionDetail.as_view(), name="collection_detail"),
    #path("results", views.DocumentList.as_view(), name="results"),
    #path("results", views.results, name="results"),
    path("results", views.results, name="results"),
    path("add_collection/", views.add_collection, name="add_collection"),
    path("add_docs/<int:pk>/", views.add_docs_to_collection, name="add_docs")
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)