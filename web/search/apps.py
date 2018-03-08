from django.apps import AppConfig




class SearchConfig(AppConfig):
    name = 'search'

    def ready(self):
        import search.search_signals
