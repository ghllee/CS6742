from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import AgglomerativeClustering
from collections import defaultdict
from gensim.models.doc2vec import Doc2Vec, LabeledSentence, LabeledLineSentence
import numpy as np

class UnigramClusterer:
    def __init__(self, k, top=None, show=False):
        self.k = k
        self.top = top
        self.show = show
    def cluster(self, sentences):
        cv = CountVectorizer(max_features = self.top)
        counts = cv.fit_transform(sentences).todense()
        clusterer = AgglomerativeClustering(n_clusters = self.k, affinity='cosine',
                                            linkage = 'complete')
        clusters = clusterer.fit_predict(counts)
        if self.show:
            clustSent = defaultdict(list)
            for i in range(len(sentences)): clustSent[clusters[i]].append(sentences[i])
            for c, sents in clustSent.iteritems():
                print c, len(sents)
        return clusters

class ParagraphVectorClusterer:
    def __init__(self, k, dims=100, top=None, show=False):
        self.k = k
        self.top = top
        self.show = show
        self.dims = dims
    def cluster(self, sentences):
        vectorizer = Doc2Vec(size=self.dims, min_count = 5, window=8, workers=4)
        newS = []
        for i in range(len(sentences)):
            newS.append(LabeledSentence(sentences[i].decode("UTF-8").split(), 
                                        ["SENT" + str(i).decode("UTF-8")]))
        vectorizer.build_vocab(newS)
        vectorizer.train(newS)
        data = np.empty([len(sentences), self.dims])
        for i in range(len(sentences)):
            data[i,:] = vectorizer["SENT" + str(i).decode("UTF-8")]
        clusterer = AgglomerativeClustering(n_clusters = self.k, affinity='cosine',
                                            linkage = 'complete')
        clusters = clusterer.fit_predict(data)
        if self.show:
            clustSent = defaultdict(list)
            for i in range(len(sentences)): clustSent[clusters[i]].append(sentences[i])
            for c, sents in clustSent.iteritems():
                print c, len(sents)
                for s in sents[:5]:
                    print s
        return clusters

class BigramClusterer:
    def __init__(self, k, top=None, show=False):
        self.k = k
        self.top = top
        self.show = show
    
    def cluster(self, sentences):
        cv = CountVectorizer(max_features = self.top, ngram_range = (2,2))
        counts = cv.fit_transform(sentences).todense()
        clusterer = AgglomerativeClustering(n_clusters = self.k, affinity='cosine',
                                            linkage = 'complete')
        clusters = clusterer.fit_predict(counts)
        if self.show:
            clustSent = defaultdict(list)
            for i in range(len(sentences)): clustSent[clusters[i]].append(sentences[i])
            for c, sents in clustSent.iteritems():
                print c, len(sents)
        return clusters
