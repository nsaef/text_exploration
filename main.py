from Reader import Reader
from Preprocesser import Preprocesser
from TopicModeller import TopicModeller
from Clusterer import Clusterer
from Analyzer import Analyzer
from WordEmbedder import WordEmbedder
from DocEmbedder import DocEmbedder
from SearchEngine import SearchEngine
from helpers import *
from time import localtime, strftime
import pickle

# TODO: automatische zusammenfassung?
# TODO: frontend/web interface,
# TODO: find useful ways to combine functionalities

if __name__ == '__main__':
    time = strftime("%Y-%m-%d %H:%M:%S", localtime())
    print("starting program at ", time)

    ##### Instantiate the search engine and index all files #####
    # search = SearchEngine()
    #search.search("Köln AND Universität OR Fachhochschule")


    #### Create a test corpus from the wikipedia dump and save it to disk #####
    # reader = Reader()
    # corpus = reader.prepare_corpus(shuffle=True, size=200000)
    # pickle.dump(corpus, open('resources/corpus_300k_filtered.c', 'wb'))

    ### Load the previously created corpus ###
    corpus = pickle.load(open("resources/corpus_10k_filtered.c", "rb"))


    ### Tokenize, remove stopwords, save the result ###
    # preprocesser = Preprocesser()
    # preprocesser.tokenize(corpus, remove_stopwords=False)
    # corpus_tokenized = preprocesser.corpus_tokenized
    #pickle.dump(corpus_tokenized, open('resources/corpus_300k_filtered_tokenized_with_stopwords_cs.c', 'wb'))
    #save_file(corpus_tokenized, "corpus_300k_filtered_tokenized_with_stopwords_cs")
    #save_file(corpus_tokenized, "corpus_10k_test")

    corpus_tokenized = pickle.load(open("resources/corpus_10k_filtered_tokenized_with_stopwords_cs.c", "rb"))

    ##### Topic Modelling #####

    # ### Vectorize the corpus using raw frequencies for lda ###
    #processer_rf = Preprocesser()
    #corpus_rf = processer_rf.vectorize_frequencies(corpus)
    #feature_names = processer_rf.feature_names_raw

    # ### Create topic models using LDA ###
    # lda = TopicModeller(n_topics=30)
    # lda.create_topic_models(corpus_rf, feature_names)
    # topics = lda.documents_per_topic(corpus_rf, corpus)
    # lda.print_top_words(feature_names, n_top_words=20, collection=topics)


    ##### Get highest frequency words and find out in which document they are #####
    # analyzer = Analyzer()
    # analyzer.get_frequencies(corpus_tokenized, n=50)


    ##### Get collocations #####
    # analyzer = Analyzer()
    # analyzer.find_ngrams(corpus_tokenized)


    ##### Get named entities #####
    #analyzer.get_named_entities(corpus_tokenized)
    #pickle.dump(analyzer, open('resources/analyzer_named_entities', 'wb'))

    ### save named entities to disk for further usage ###
    #pickle.dump(analyzer, open('resources/analyzer_named_entities', 'wb'))
    # analyzer = pickle.load(open("resources/analyzer_named_entities", "rb"))
    # analyzer.sort_named_entities()


    ##### Clustering ######

    ### Vectorize the corpus using tf-idf ###
    # processer_tfidf = Preprocesser()
    # corpus_tfidf = processer_tfidf.vectorize_tfidf(corpus)
    # features_tfidf = processer_tfidf.feature_names_tfidf

    ### Cluster documents ###
    # clusterer = Clusterer()
    # clusterer.cluster_kmeans(corpus_tfidf, feature_names=features_tfidf)


    ##### Word Embeddings ####
    # vectorizer = WordEmbedder()
    # model = vectorizer.run(corpus_tokenized, filename="w2v_model_corpus100k_tokenized")
    # wv = model.wv
    # print(wv.most_similar(positive=['Frau', 'König'], negative=['Mann'], topn=5))
    #model.most_similar(positive=['woman', 'king'], negative=['man'], topn=1)
    # man is to king as woman to X

    ##### Doc Embeddings ####
    vectorizer = DocEmbedder()
    #taggedDocs = vectorizer.prepare_corpus(corpus_tokenized)
    model = vectorizer.run("d2v_10k_with_stopwords") #
    wv = model.wv

    #use the model to infer the vectors for a smaller collection
    #taggedDocs = vectorizer.prepare_corpus(corpus_tokenized)
    vectors = []
    for doc in corpus_tokenized:
        vectors.append(model.infer_vector(doc))

    vectorizer.show_similar_docs(corpus, print_results=False)

    #clusterer = Clusterer(k=30)
    # reduced_vectors = clusterer.decompose(model.docvecs.doctag_syn0, n_components=50)
    # clusterer.test_feature_agglomoration(50, model.docvecs.doctag_syn0, corpus, model.docvecs)
    # reduced_vectors = clusterer.do_feature_agglomoration(model.docvecs.doctag_syn0)

    #clusters_kmeans = clusterer.cluster_kmeans(model.docvecs, file_output=True, console_output=False, reduced_vectors=None, feature_names=corpus)
    #clusters_kmeans = clusterer.cluster_kmeans(vectors, file_output=False, console_output=False, feature_names=corpus)

    # for i, center in enumerate(clusterer.kmeans_centers):
    #     print("Cluster Nr. ", i+1)
    #     c = [center]
    #     model.docvecs.most_similar(c, topn=3)
    #     print("\n")

    #
    # labels_db = clusterer.cluster_dbscan(reduced_vectors)
    # labels_hdb = clusterer.cluster_hdbscan(reduced_vectors)
    #
    # clusters_db = clusterer.get_clusters(corpus, labels_db)
    # clusters_hdb = clusterer.get_clusters(corpus, labels_hdb)

    #clusterer.do_silhouette_analysis(model.docvecs.doctag_syn0, min_clusters=5, max_clusters=10)
    #ergebnis: k=5 oder 7

    time = strftime("%Y-%m-%d %H:%M:%S", localtime())
    print("Done at ", time)


### hdbscan findet nur winzige cluster
### dbscan ebenso. das einzige cluster, was wirklich zuverlässig gefunden wird, ist ein Teil von Sport
