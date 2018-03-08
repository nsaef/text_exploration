from __future__ import print_function

from sklearn.decomposition import NMF, LatentDirichletAllocation
from time import time


class TopicModeller(object):

    def __init__(self, n_topics):
        print("starting topic modelling process")
        self.n_topics = n_topics
        self.model = None

    # obj: raw term frequency vectorized version
    # feature_names: vectorizer.get_feature_names()
    def create_topic_models(self, obj, feature_names, method="lda"):
        if method == "lda":
            lda = LatentDirichletAllocation(n_topics=self.n_topics, max_iter=5,
                                            learning_method='online',
                                            learning_offset=50.,
                                            random_state=0)
            t0 = time()
            lda.fit(obj)
            print("done in %0.3fs." % (time() - t0))
            self.model = lda

            #print("\nTopics in LDA model:")
            #self.print_top_words(lda, feature_names, self.n_top_words)
        elif method == "nmf":
            nmf = NMF(n_components=self.n_topics, random_state=1,
                      alpha=.1, l1_ratio=.5).fit(obj)
            self.model = nmf

            #print("\nTopics in NMF model:")
            #self.print_top_words(nmf, feature_names, self.n_top_words)
        return

    ## get the documents in each topic ###
    # topicModeller: lda or nfm/the object used to create the topic models
    # vector: tfidf or tf representation of the input data
    # input: the original inout data
    def documents_per_topic(self, vector, input, threshold=0.33):
        docs_per_topic = self.model.transform(vector)
        collection = []

        for i in range(docs_per_topic.shape[1]):
            collection.append([])

        for n in range(docs_per_topic.shape[0]):
            topic_most_pr = docs_per_topic[n].argmax()
            if docs_per_topic[n, topic_most_pr] > threshold:
                collection[topic_most_pr].append(input[n])

        print(len(collection))

        #for topic in collection:
            #print(topic[:10])
        return collection


### TO-DO: statt print: top words per topic in objekt speichern
    def print_top_words(self, feature_names, n_top_words=20, collection=None):
        print("\nTopics in model:")
        for topic_idx, topic in enumerate(self.model.components_):
            print("Topic #%d:" % topic_idx)
            print(" ".join([feature_names[i]
                            for i in topic.argsort()[:-n_top_words - 1:-1]]))

            if collection != None:
                c = 0
                for article in collection[topic_idx]:
                    if c == 5: break
                    print(article[:50])
                    c += 1
        print()