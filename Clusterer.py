from __future__ import print_function

import numpy as np
from time import time, localtime, strftime
from sklearn.cluster import KMeans, DBSCAN, FeatureAgglomeration
from sklearn.decomposition import PCA
#import hdbscan
from sklearn import metrics
import matplotlib.pyplot as plt
#import seaborn as sns
from sklearn.metrics import silhouette_samples, silhouette_score
import matplotlib.cm as cm
import os


### TO-DO: Dokumente den Clustern zuordnen ###

class Clusterer(object):
    def __init__(self, k=50):
        print("Clustering...")
        self.k = k

    def cluster_kmeans(self, vectors, reduced_vectors=None, console_output=True, file_output=True,feature_names=None):
        km = KMeans(n_clusters=self.k, init='k-means++', max_iter=100, n_init=1, verbose=False)
        print("Clustering sparse data with %s" % km)
        t0 = time()
        if reduced_vectors is not None: data = reduced_vectors
        else: data = vectors
        self.kmeans_result = km.fit_predict(data)
        self.kmeans_labels = km.labels_
        self.kmeans_centers = km.cluster_centers_
        print("done in %0.3fs" % (time() - t0), "\n")

        silhouette_avg = silhouette_score(vectors, self.kmeans_labels, sample_size=50000)
        print("For n_clusters =", self.k, "The average silhouette_score is :", silhouette_avg)

        if console_output == True: # and feature_names != None:
            self.kmeans_console_output(feature_names)
        if file_output == True: # and feature_names != None:
            self.kmeans_file_output(feature_names)
        return

    def kmeans_console_output(self, wv_index):
        doc_centroid_map = dict(zip(wv_index, self.kmeans_result))
        result = {}

        for cluster in range(0, self.k):
            # Find all of the words for that cluster number, and print them out
            docs = []

            for i in range(0, len(doc_centroid_map.values())):
                if list(doc_centroid_map.values())[i] == cluster:
                    docs.append(list(doc_centroid_map.keys())[i])
            result[cluster] = docs
        return result


    def kmeans_file_output(self, wv_index):
        doc_centroid_map = dict(zip(wv_index, self.kmeans_result))

        timestamp = strftime("%Y-%m-%d_%H-%M-%S", localtime())
        dir = "kmeans_" + timestamp
        os.mkdir(r"./results/clusters/" + dir)

        for cluster in range(0, self.k):
            path = r"./results/clusters/" + dir + "/" + str(cluster) + ".txt"
            f = open(path, 'w', encoding="utf-8")

            # Print the cluster number
            print("\nCluster %d" % cluster, file=f)

            # Find all of the documents for that cluster number, and print them out
            docs = []

            for i in range(0, len(doc_centroid_map.values())):
                if list(doc_centroid_map.values())[i] == cluster:
                    docs.append(list(doc_centroid_map.keys())[i][:100])

            print(str(len(docs)), " documents of total", len(doc_centroid_map), " in cluster\n", file=f)
            for doc in docs:
                print(doc, "\n", file=f)

            f.close()
            print("result saved in " + path)
        return


    def do_silhouette_analysis(self, X, min_clusters=3, max_clusters=10):
        range_n_clusters = list(range(min_clusters, max_clusters+1))
        t0 = time()

        for n_clusters in range_n_clusters:
            # Initialize the clusterer with n_clusters value and a random generator
            # seed of 10 for reproducibility.
            clusterer = KMeans(n_clusters=n_clusters, random_state=10, n_jobs=4)
            cluster_labels = clusterer.fit_predict(X)

            # The silhouette_score gives the average value for all the samples.
            # This gives a perspective into the density and separation of the formed
            # clusters
            silhouette_avg = silhouette_score(X, cluster_labels)
            print("For n_clusters =", n_clusters,
                  "The average silhouette_score is :", silhouette_avg)

            # # Compute the silhouette scores for each sample
            # sample_silhouette_values = silhouette_samples(X, cluster_labels)
            #
            # y_lower = 10
            # for i in range(n_clusters):
            #     # Aggregate the silhouette scores for samples belonging to
            #     # cluster i, and sort them
            #     ith_cluster_silhouette_values = \
            #         sample_silhouette_values[cluster_labels == i]
            #
            #     ith_cluster_silhouette_values.sort()
            #
            #     size_cluster_i = ith_cluster_silhouette_values.shape[0]
        print("done in %0.3fs" % (time() - t0), "\n")
        return


    def cluster_dbscan(self, vectors):
        print("clustering with dbscan")
        t0 = time()

        # Compute DBSCAN
        db = DBSCAN(eps=0.7, min_samples=10, n_jobs=4).fit(vectors)
        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        labels = db.labels_

        # Number of clusters in labels, ignoring noise if present.
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

        print('Estimated number of clusters: %d' % n_clusters_)
        print("Silhouette Coefficient: %0.3f"
              % metrics.silhouette_score(vectors, labels, sample_size=30000))

        ### Plot result ###
        # Black removed and is used for noise instead.
        unique_labels = set(labels)
        cmap = plt.cm.get_cmap('Spectral')

        #colors = [cmap(each) for each in np.linspace(0, 1, len(unique_labels))]
        colors = sns.color_palette('deep', 128)
        for k, col in zip(unique_labels, colors):
            if k == -1:
                # Black used for noise.
                col = [0, 0, 0, 1]

            class_member_mask = (labels == k)

            xy = vectors[class_member_mask & core_samples_mask]
            plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=col,
                     markeredgecolor='k', markersize=14)

            xy = vectors[class_member_mask & ~core_samples_mask]
            plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=col,
                     markeredgecolor='k', markersize=6)

        plt.title('Estimated number of clusters: %d' % n_clusters_)
        plt.show()

        print("done in %fs" % (time() - t0))
        return labels


    # def cluster_hdbscan(self, vectors):
    #     clusterer = hdbscan.HDBSCAN(min_cluster_size=5, min_samples=1, alpha=0.8) #cluster_selection_method="leaf"
    #
    #     print("clustering with hdbscan")
    #     t0 = time()
    #
    #     clusterer.fit(vectors)
    #
    #     labels = clusterer.labels_
    #
    #     # Number of clusters in labels, ignoring noise if present.
    #     n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    #
    #     print('Estimated number of clusters: %d' % n_clusters_)
    #     print("Silhouette Coefficient: %0.3f"
    #           % metrics.silhouette_score(vectors, labels, sample_size=30000))
    #
    #     # color_palette = sns.color_palette('deep', 128)
    #     # cluster_colors = [color_palette[x] if x >= 0
    #     #                   else (0.5, 0.5, 0.5)
    #     #                   for x in clusterer.labels_]
    #     # cluster_member_colors = [sns.desaturate(x, p) for x, p in
    #     #                          zip(cluster_colors, clusterer.probabilities_)]
    #     # plt.scatter(vectors, vectors.T, s=50, linewidth=0, c=cluster_member_colors, alpha=0.25)
    #     # plt.show()
    #
    #     print("done in %fs" % (time() - t0))
    #     return labels


    def get_clusters(self, data, labels):
        map = {"noise": []}
        n = len(set(labels)) - (1 if -1 in labels else 0)

        for idx in range(0, n):
            map[idx] = []

        for i, l in enumerate(labels):
            if l == -1: map["noise"].append(data[i])
            else: map[l].append(data[i])

        return map


    def decompose(self, data, n_components="mle", svd_solver="full"):
        print("Decomposing the matrix to reduce its dimensionality...")
        return PCA(n_components=n_components, svd_solver=svd_solver).fit_transform(data)


    def test_feature_agglomoration(self, n, data, corpus, docvecs):
        print("Using feature agglomoration to reduce the matrix' dimensionality...")
        affinities = ["euclidean", "l1", "l2", "manhattan", "cosine", "precomputed"]
        linkages = ["ward", "complete", "average"]
        agglos = []

        for linkage in linkages:
            if linkage is "ward":
                agglos.append(FeatureAgglomeration(n_clusters=n, affinity="euclidean", linkage=linkage))
            else:
                for affinity in affinities:
                    agglos.append(FeatureAgglomeration(n_clusters=n, affinity=affinity, linkage=linkage))

        for agglo in agglos:
            print(agglo.get_params)
            reduced_vectors = agglo.fit_transform(data)

            clusters_kmeans = self.cluster_kmeans(docvecs, reduced_vectors=reduced_vectors, feature_names=corpus)
            labels_db = self.cluster_dbscan(reduced_vectors)
            #labels_hdb = self.cluster_hdbscan(reduced_vectors)
            clusters_db = self.get_clusters(corpus, labels_db)
            #clusters_hdb = self.get_clusters(corpus, labels_hdb)
        #agglo = FeatureAgglomeration(n_clusters=n, affinity="euclidean", linkage="ward")
        #return agglo.fit_transform(data)
        return

    def do_feature_agglomoration(self, data):
        print("Using feature agglomoration to reduce the matrix' dimensionality...")
        if self.k:
            n = self.k
        else:
            n = 20

        agglo = FeatureAgglomeration(n_clusters=n, affinity="cosine", linkage="complete")
        return agglo.fit_transform(data)