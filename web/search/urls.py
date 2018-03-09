from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path("docs/<int:pk>/", views.DocumentDetail.as_view(), name="document_detail"),
    path("collections/<int:pk>/", views.CollectionDetail.as_view(), name="collection_detail"),
    path("search_action/<int:query_id>/results.html", views.ResultsView.as_view(), name="results"),
    path("search_action/", views.search_action, name="search_action")
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)