from django import template
from Preprocesser import Preprocesser
from Analyzer import Analyzer

register = template.Library()

@register.simple_tag
def get_highest_freq_words(doc, n=20):
    preprocesser = Preprocesser()
    preprocesser.tokenize([doc], remove_stopwords=True)
    doc_tokenized = preprocesser.corpus_tokenized

    analyzer = Analyzer()
    return analyzer.get_frequencies(doc_tokenized, n)

@register.simple_tag
def get_named_entities(doc):
    preprocesser = Preprocesser()
    preprocesser.split_sentences([doc])
    sents = preprocesser.corpus_sentences

    analyzer = Analyzer()
    entities = analyzer.get_named_entities_sents(sents)

    output = {"locations": [], "persons": [], "organizations": [], "others": []}
    for idx, counter in enumerate(entities):
        if idx is 0:
            output["locations"].extend(counter.most_common())
        elif idx is 1:
            output["persons"].extend(counter.most_common())
        elif idx is 2:
            output["organizations"].extend(counter.most_common())
        elif idx is 3:
            output["others"].extend(counter.most_common())
    return output

