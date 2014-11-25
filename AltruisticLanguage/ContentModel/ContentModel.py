from LanguageModel import BigramModel, ETCBigramModel
import string
from nltk import tokenize
import nltk
import sys
import cPickle as pickle
from nltk import tokenize, ne_chunk
from nltk.tokenize import WhitespaceTokenizer
from sklearn.cluster import AgglomerativeClustering
import warnings
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import TruncatedSVD
from loadbar import LoadBar
import numpy as np
import random
from collections import Counter, defaultdict

class ContentModel:
    def __init__(self, langModel = 'bigram',
                 numClusters = 10,
                 minProportion = .01,
                 projectionDim = 100,
                 clusterTrainProp = .004, 
                 d1 = .00001,
                 d2 = .001,
                 cleanSents = None,
                 saveFile = None):
        '''Params= numClusters, minimum cluster proportional size to not be absorbed
        into etc cluster, and (optionally) somewhere to load/save cleaned sentences from/to.'''
        self.langModel = langModel
        self.numClusters = numClusters
        self.minProportion = minProportion
        self.projectionDim = projectionDim
        self.clusterTrainProp = clusterTrainProp
        self.d1 = d1
        self.d2 = d2
        self.cleanSents = cleanSents
        self.saveFile = saveFile
        self.wsTokenizer = WhitespaceTokenizer()

    def train(self, documentsIn):
        if self.langModel is not 'bigram': warnings.warn("Language model unsupported, using bigram")
        bar = LoadBar(30)
        random.shuffle(documentsIn)
        if self.cleanSents is None:
            print "Parsing/cleaning sentences"
            self.cleanSents = []
            bar.setup()
            for i in range(len(documentsIn)):
                if bar.test(i, len(documentsIn)): bar += 1
                d = documentsIn[i]
                sents = [( self.cleanSentence(x, properNames = "name"*4, numbers = "num"*4) , i)
                         for x in self.stringToSentences(d)]
                self.cleanSents.extend(sents)
            bar.clear()
            if self.saveFile is not None:
                print "Saving cleaned sentences to " + self.saveFile
                with open(self.saveFile, 'w') as f:
                    pickle.dump(self.cleanSents, f, -1)
        print "There were " + str(len(self.cleanSents)) + " sentences."
        self.cleanSents = self.cleanSents[:int(np.floor(len(self.cleanSents)*self.clusterTrainProp))]
        print "Finding bigram features"
        myVectorizer = CountVectorizer(decode_error='ignore',ngram_range=(2,2))
        bigramFeatures = myVectorizer.fit_transform([x[0] for x in self.cleanSents])
        print "Executing LSA with " + str(self.projectionDim) + " dimensions"
        myLSA = TruncatedSVD(n_components = self.projectionDim)
        trainer = myLSA.fit_transform(bigramFeatures)
        print "Clustering " + str(trainer.shape[0]) + " sentences for LM examples"
        clusterer = AgglomerativeClustering(n_clusters = self.numClusters, affinity='cosine',
                                            linkage = 'complete')
        clusters = clusterer.fit_predict(trainer)
        print "Counting vocab..."
        vocab = set.union(*[set(x[0].split()) for x in self.cleanSents])
        print "The trained vocab size is " + str(len(vocab))
        #VITERBI OPTIMIZATION
        for i in range(10):
            print "CLUSTERS"
            print clusters[:25]
            clusterCounts = Counter(clusters)
            etcClusters = []
            for cluster, count in clusterCounts.iteritems():
                if count < self.minProportion * len(self.cleanSents):
                    etcClusters.append(cluster)

            print "Merged " + str(len(etcClusters)) + " into etc clusters"

            print "Training language models"
            self.lms = {}
            for i in range(self.numClusters):
                if i in etcClusters: continue
                validSents = [self.cleanSents[x] for x in np.where(clusters==i)[0]] 
                curLm = BigramModel([v[0] for v in validSents], parameters = (self.d1, len(vocab)))
                self.lms[i] = curLm

            print "Training ETC model"
            self.lms['E'] = ETCBigramModel([x[0] for x in self.cleanSents],
                                           parameters = (self.lms.values(),))
            
            curNumClusters = len(self.lms)
            
            #dictionary from docIndex -> [(sent, clusternum)]
            docDict = defaultdict(list)
            for i in range(len(self.cleanSents)):
                docDict[self.cleanSents[i][1]].append((self.cleanSents[i][0], clusters[i]))

            transProbs = self.getTransitionProbs(clusters, etcClusters, docDict)
            clusters = list(set(clusters)) + ['E']
            newPaths = {}
            for d, sents in docDict.iteritems():
                observedSents = [x[0] for x in sents]
                observedSeq = [x[1] for x in sents]
                (score, path) = self.mostLikelyPath(observedSents,
                                                    self.lms.keys(), self.lms,
                                                    {k:np.log(1./curNumClusters) for k in clusters},
                                                    transProbs)
                newPaths[d] = path
            
            newClusters = []
            for d, newPath in newPaths.iteritems():
                print newPath
                newClusters.extend(newPath)
            clusters = [x if x is not 'E' else 99999 for x in newClusters]
            

    def mostLikelyPath(self, observedSentences, states, stateToLm, startProbs, transProbs):
        '''Viterbi based on code from wikipedia.'''
        V = [{}]
        path = {}
        #base cases
        for lm in states:
            V[0][lm] = startProbs[lm] + stateToLm[lm].logProb(observedSentences[0])
            path[lm] = [lm]
        #fill in rest of table
        for t in range(1, len(observedSentences)):
            V.append({})
            newpath = {}
            for lm in states:
                (prob, state) = max((V[t-1][y] + transProbs[(y,lm)] +
                                     stateToLm[lm].logProb(observedSentences[t]), y) 
                                    for y in states)
                V[t][lm] = prob
                newpath[lm] = path[state] + [lm]
            path = newpath
        n=0
        if len(observedSentences) != 1:
            n=t
        (prob, state) = max((V[n][y], y) for y in states)
        return (prob, path[state])

    def getTransitionProbs(self, clusters, etcClusters, docDict):
        '''Compute the transition probabilities in accordance with the smoothed estimate eqtn (logged)'''
        clusters = list(set(clusters)) + ['E']
        numClusters = len(clusters)
        #{(s1, s2) -> prob of going from s1 to s2
        transProbs = {}
        #{(c1, c2) -> count}
        Dpair = Counter()
        #{c -> count}
        D = Counter()
        for doc, sents in docDict.iteritems():
            classifications = [x[1] for x in sents]
            classifications = ['E' if x in etcClusters else x for x in classifications]
            D.update(list(set(classifications)))
            trans = []
            for i in range(len(classifications)-1):
                trans.append((classifications[i], classifications[i+1]))
            Dpair.update(list(set(trans)))
        for c1 in clusters:
            for c2 in clusters:
                transProbs[(c1,c2)] = np.log(1.*(Dpair[(c1,c2)] + self.d2)/
                                             (D[c1] + self.d2*numClusters))
        return transProbs

    def cleanSentence(self, stringIn, properNames = None, numbers = None, dates = None):
        '''Given a string and the tokens to replace different elements of the text with,
        returns strings with those aspects replaced with the given tokens. Also removes
        punctuation, and puts things in lower case.'''
        exclude = set(string.punctuation)
        newString = "".join([ch for ch in stringIn if ch not in exclude])
        if properNames is not None:
            names = set()
            taggedTokens = nltk.ne_chunk(nltk.pos_tag(self.wsTokenizer.tokenize(newString)))
            for t in taggedTokens:
                if type(t) != tuple:
                    names.add(t[0][0])
            tokens = newString.split()
            for i in range(len(tokens)):
                for n in names:
                    tokens[i] = re.sub("(^" + n + "|" + n + "$)", properNames, tokens[i])
            newString = " ".join(tokens)
        if numbers is not None:
            numReg = "(\d+,)*(\d+|\d+\.\d+|\.\d+)"
            newString = re.sub(numReg, numbers, newString)
        if dates is not None:
            warnings.warn("Warning, date replacement not yet implemented")
        return newString.lower()

    def toCleanSentences(self, stringList):
        '''Given a list of strings, processes them into a list of sentences
        removing punctuation and making everything lowercase.'''
        stringList = [" ".join(x.split()) for x in stringList]
        sentences = []
        for curS in stringList: sentences.extend(stringToSentences(curS))
        sentences = [s for s in sentences if len(s) >= 2]
        return sentences

    def stringToSentences(self, string):
        '''Given a string returns the list of sentences in that string.'''
        x = [" ".join(self.wsTokenizer.tokenize(s)).lower()
             for s in tokenize.sent_tokenize(string)]
        return [y for y in x if len(y.split()) >= 1] 

def main():
    if len(sys.argv) == 1:
        print "must have argument"
        quit()
    elif len(sys.argv) == 2:
        loadFile = sys.argv[1]
        loadFileClean = None
    elif len(sys.argv) == 3:
        loadFile = sys.argv[1]
        loadFileClean = sys.argv[2]


    with open(loadFile) as f:
        data = pickle.load(f)
    dataClean = None
    if loadFileClean is not None:
        with open(loadFileClean) as f:
            dataClean = pickle.load(f)
    

    x = ContentModel(saveFile = "GFM.clean", cleanSents = dataClean)
    x.train(data)
    
if __name__ == "__main__":
    main()
