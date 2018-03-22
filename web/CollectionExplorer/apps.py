from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = 'CollectionExplorer'

    def ready(self):
        import CollectionExplorer.explorer_signals
