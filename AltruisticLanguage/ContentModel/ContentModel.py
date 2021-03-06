from LanguageModel import BigramModel, ETCBigramModel, UniformModel
import string
from nltk import tokenize
import nltk
import sys
import cPickle as pickle
from nltk import tokenize, ne_chunk
from nltk.tokenize import WhitespaceTokenizer
import warnings
import re
from SentenceCluster import UnigramClusterer, BigramClusterer, ParagraphVectorClusterer
from loadbar import LoadBar
import numpy as np
import random
from collections import Counter, defaultdict
import regexStore
import os

#for music data, 3000, .002
#succ 1415, .004 -> 33 clusters
#fail 1350, .004 -> 32 clusters
class ContentModel:
    def __init__(self, langModel = 'bigram',
                 numClusters = 1350,
                 minProportion = .004,
                 clusterTrainProp = 1, 
                 d1 = .00000005,
                 d2 = .001,
                 cleanSents = None,
                 saveFile = None,
                 name = "success"):
        '''Params= numClusters, minimum cluster proportional size to not be absorbed
        into etc cluster, and (optionally) somewhere to load/save cleaned sentences from/to.'''
        self.langModel = langModel
        self.numClusters = numClusters
        self.minProportion = minProportion
        self.clusterTrainProp = clusterTrainProp
        self.d1 = d1
        self.d2 = d2
        self.cleanSents = cleanSents
        self.saveFile = saveFile
        self.wsTokenizer = WhitespaceTokenizer()

        #model itself
        self.name = name
        self.lms = None
        self.transProbs = None

    def train(self):
        if not os.path.exists(self.name):
            os.makedirs(self.name)
        if self.langModel is not 'bigram': warnings.warn("Language model unsupported, using bigram")
        bar = LoadBar(30)

        print "There were " + str(len(self.cleanSents)) + " sentences."
        self.cleanSents = self.cleanSents[:int(np.floor(len(self.cleanSents)*self.clusterTrainProp))]
        print "Counting vocab..."
        vocab = set.union(*[set(x[0].split()) for x in self.cleanSents])
        print "The vocab size is " + str(len(vocab))
        print "Clustering things"
        clusterer = BigramClusterer(self.numClusters, show=True)
        clusters = clusterer.cluster([x[0] for x in self.cleanSents])
       
        clusterCounts = Counter(clusters)
        etcClusters = []
        for cluster, count in clusterCounts.iteritems():
            if count < self.minProportion * len(self.cleanSents):
                etcClusters.append(cluster)
        
        print "Merged " + str(len(etcClusters)) + " into etc clusters"
        m = self.numClusters - len(etcClusters) + 1
        print "This gives us " + str(m) + " clusters"
        clusters = [c if c not in etcClusters else -1 for c in clusters]
        allClusters = set(clusters + [-1])

        docDict = defaultdict(list)
        for i in range(len(self.cleanSents)):
            docDict[self.cleanSents[i][1]].append((self.cleanSents[i][0], clusters[i]))

        for d, sents in docDict.iteritems():
            observedSents = [x[0] for x in sents]
            observedSeq = [x[1] for x in sents]

        #VITERBI OPTIMIZATION
        for i in range(100):
            print "Iteration " + str(i)
            
            print "Training language models"
            self.lms = {}
            #maps from cluster -> [sentence]
            clustSent = defaultdict(list)
            for i in range(len(self.cleanSents)): clustSent[clusters[i]].append(self.cleanSents[i])

            #maps from cluster -> language model
            print "Training Bigram LMs"
            self.lms = {}
            for x in allClusters:
                if x == -1: continue
                sents = clustSent[x]
                self.lms[x] = BigramModel([y[0] for y in sents],
                                          (self.d1, len(vocab)))
            print "Training ETC model"
            self.lms[-1] = ETCBigramModel([x[0] for x in self.cleanSents],
                                          (self.lms.values(),))
            
            #dictionary from docIndex -> [(sent, clusternum)]
            docDict = defaultdict(list)
            for i in range(len(self.cleanSents)):
                docDict[self.cleanSents[i][1]].append((self.cleanSents[i][0], clusters[i]))

            print "Estimating transition probabilities"
            self.transProbs = self.getTransitionProbs(allClusters, docDict, m)

            newPaths = {}
            print "Estimating Viterbi paths"
            numDocs = len(docDict.keys())
            curIter = 0
            bar.setup()
            for d, sents in docDict.iteritems():
                if bar.test(curIter, numDocs): bar+=1
                observedSents = [x[0] for x in sents]
                observedSeq = [x[1] for x in sents]

                (score, path) = self.mostLikelyPath(observedSents,
                                                    self.lms.keys(), self.lms,
                                                    {k:np.log(1./m) for k in allClusters},
                                                    self.transProbs)
                newPaths[d] = path
                curIter +=1
            bar.clear()
            
            newClusters = []
            curIter = 0
            for d, newPath in newPaths.iteritems():
                if curIter < 6: print newPath
                newClusters.extend(newPath)
                curIter += 1

            print "Saving model..."
            for cluster, model in self.lms.iteritems():
                if cluster == -1:
                    with open(self.name + "/etcWordToIndex.pickle",'w') as f:
                        pickle.dump(model.wordToIndex, f, -1)
                    with open(self.name + "/etcMatrix.npy", 'w') as f:
                        np.save(f, model.oneMinusMaxPsiMatrix)
                else:
                    with open(self.name + "/" + str(cluster) + ".lm", 'w') as f:
                        pickle.dump(model, f, -1)
            with open(self.name + '/' + "transProbs", 'w') as f:
                pickle.dump(self.transProbs, f, -1)
            if newClusters == clusters:
                print "Converged"
                break
            clusters = newClusters

        docDict = defaultdict(list)
        for i in range(len(self.cleanSents)):
            docDict[self.cleanSents[i][1]].append((self.cleanSents[i][0], clusters[i]))
        with open(self.name + "/docPathsOut.txt",'w') as f:
            for doc, sentsClusters in docDict.iteritems():
                for sc in sentsClusters:
                    f.write(str(sc))
                f.write("\n")

        with open(self.name + "/clustersOut.txt",'w') as f:
            for i in range(len(self.cleanSents)):
                clustSent = defaultdict(list)
                for i in range(len(self.cleanSents)): 
                    clustSent[clusters[i]].append(self.cleanSents[i])
            for c, sents in clustSent.iteritems():
                f.write(str(c) + " " + str(len(sents)) + "\n")
                for s in sents:
                    f.write(s[0] + "\n")
                f.write("***\n")


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
            for y in states:
                (prob, state) = max((V[t-1][y0] + transProbs[(y0,y)] + 
                                     stateToLm[y].logProb(observedSentences[t]), y0)
                                    for y0 in states)
                V[t][y] = prob
                newpath[y] = path[state] + [y]
            path = newpath
        n=0
        if len(observedSentences) != 1:
            n=t
        (prob, state) = max((V[n][y], y) for y in states)
        return (prob, path[state])

    def getTransitionProbs(self, clusters, docDict, numClusters):
        '''Compute the transition probabilities in accordance with the smoothed estimate eqtn (logged)'''
        clusters = list(set(clusters))
        #{(s1, s2) -> prob of going from s1 to s2
        transProbs = {}
        #{(c1, c2) -> count}
        Dpair = Counter()
        #{c -> count}
        D = Counter()
        for doc, sents in docDict.iteritems():
            classifications = [x[1] for x in sents]
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

    def cleanSentence(self, stringIn, properNames = None, numbers = None, dates = None, urls = None):
        '''Given a string and the tokens to replace different elements of the text with,
        returns strings with those aspects replaced with the given tokens. Also removes
        punctuation, and puts things in lower case.'''
        newString = stringIn
        if urls is not None:
            replaced = re.findall(regexStore.urlReg, newString)
            newString = re.sub(regexStore.urlReg, urls, newString)
        exclude = set(string.punctuation)
        newString = "".join([ch for ch in newString if ch not in exclude])
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
    if len(sys.argv) != 3:
        print "must have arguments of form [clean load file] [model name]"
        quit()
    loadFileClean, modelName = sys.argv[1:3]
    
    
    with open(loadFileClean) as f:
        dataClean = pickle.load(f)
    dataClean = [x for x in dataClean if len(x[0].strip().split()) > 4]

    x = ContentModel(cleanSents = dataClean, name=modelName)
    x.train()

def main2():
    documentsIn = pickle.load(open(sys.argv[1]))
    bar = LoadBar(30)
    cleanSents = []
    cm = ContentModel()
    bar.setup()
    for i in range(len(documentsIn)):
        if bar.test(i, len(documentsIn)): bar += 1
        d = documentsIn[i]
        sents = [(cm.cleanSentence(x, properNames = "name"*4, numbers = "num"*4, urls = "url"*4) , i)
                 for x in cm.stringToSentences(d)]
        cleanSents.extend(sents)
    bar.clear()
    print "Saving cleaned sentences to XXX"
    with open(sys.argv[2], 'w') as f:
        pickle.dump(cleanSents, f, -1)
    
if __name__ == "__main__":
    main()
