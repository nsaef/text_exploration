from django.apps import AppConfig
from django.conf import settings
from django.templatetags.static import static
import os


class SearchConfig(AppConfig):
    name = 'CollectionExplorer'

    def ready(self):
        static_path = settings.BASE_DIR + "/CollectionExplorer" + static("CollectionExplorer/")
        dirs = ["corpora", "img", "index", "js", "models", "similarities", "style"]

        if not os.path.exists(static_path):
            os.mkdir(static_path)

        for dir in dirs:
            path = static_path + dir
            if not os.path.exists(path):
                os.mkdir(path)

