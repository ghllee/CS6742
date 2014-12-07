import numpy as np
from collections import Counter
from scipy.sparse import lil_matrix
from loadbar import LoadBar

class LanguageModel:
    def __init__(self, sentencesIn, parameters = None):
        if parameters is not None:
            self.setParams(parameters)
        self.train(sentencesIn)

    def setParams(self, parameters):
        '''Given a tuple of parameters you expect, save them.'''
        print "OVERRIDE ME"
        pass

    def train(self, sentencesIn):
        '''Given a list of sentences, '''
        print "OVERRIDE ME"
        pass

    def logProb(self, sentence):
        '''Given a sentence, returns the log probability of that sentence under this model'''
        print "OVERRIDE ME"
        pass

class ETCBigramModel(LanguageModel):
    def setParams(self, parameters):
        '''Here, we expect parameters in the form ([otherLM1, otherLM2, ...]) where
        the other LMs are REQUIRED to have the function bigramProb(bigram)'''
        self.otherLMs = parameters[0]
        self.loader = LoadBar(30)

    def getDenom(self, baseWord):
        return np.sum(self.oneMinusMaxPsiMatrix[self.wordToIndex[baseWord], :])

    def train(self, sentencesIn):
        #Fill up the oneMinsMaxPsiMatrix in O(|V|^2) [[NOT GREAT]]
        self.loader.setup()
        self.vocab = set()
        for s in sentencesIn:
            self.vocab.update(set(s.split()))
        self.wordToIndex = {w:i for w,i in zip(self.vocab, range(len(self.vocab)))}
        self.oneMinusMaxPsiMatrix = np.zeros([len(self.vocab), len(self.vocab)])
        total = len(self.vocab)**2
        i = 0
        for w1, i1 in self.wordToIndex.iteritems():
            for w2, i2 in self.wordToIndex.iteritems():
                if self.loader.test(i, total): self.loader+=1
                maxProb = 0.
                for l in self.otherLMs:
                    curProb = l.bigramProb((w1, w2))
                    if maxProb < curProb: maxProb = curProb
                self.oneMinusMaxPsiMatrix[i1, i2] = 1.-maxProb
                i += 1
        self.loader.clear()

    def bigramProb(self, bigram):
        numer = self.oneMinusMaxPsiMatrix[self.wordToIndex[bigram[0]],
                                          self.wordToIndex[bigram[1]]]
        denom = self.getDenom(bigram[0])
        return numer/denom

    def logProb(self, sentence):
        logProb = 0
        for bi in self.getBigrams(sentence.split()): logProb += np.log(self.bigramProb(bi))
        return logProb

    def getBigrams(self, tokens):
        returnList = []
        for i in range(len(tokens) - 1): returnList.append((tokens[i], tokens[i+1]))
        return returnList

class BigramModel(LanguageModel):
    def train(self, sentencesIn):
        #determine vocab we need to store and assign index to each
        self.wordToIndex = {}
        wordCounter = Counter()
        bigramCounter = Counter()
        for s in sentencesIn:
            tokens = s.split()
            for t in set(tokens):
                wordCounter[t] += 1
            for b in set(self.getBigrams(tokens)):
                bigramCounter[b] += 1
        wordSet = set(wordCounter.keys())
        i = 0
        for w in wordSet:
            self.wordToIndex[w] = i
            i += 1
        #okay, now that we have that, we can create our main storage devices
        self.wordFreq = np.zeros(len(wordSet), dtype = np.uint32)
        self.bigramFreq = lil_matrix((len(wordSet), len(wordSet)), dtype = np.uint32)
        for word, count in wordCounter.iteritems(): self.wordFreq[self.wordToIndex[word]] = count
        for bigram, count in bigramCounter.iteritems():
            self.bigramFreq[self.wordToIndex[bigram[0]], self.wordToIndex[bigram[1]]] = count

    def logProb(self, sentence):
        logProb = 0
        for bi in self.getBigrams(sentence.split()): logProb += np.log(self.bigramProb(bi))
        return logProb
        
    def bigramProb(self, bi):
        '''Given a bigram, return the probability of that bigram.'''
        if bi[0] in self.wordToIndex:
            termFreq = self.wordFreq[self.wordToIndex[bi[0]]]
            if bi[1] in self.wordToIndex:
                biFreq = self.bigramFreq[self.wordToIndex[bi[0]], self.wordToIndex[bi[1]]]
            else:
                biFreq = 0
        else:
            termFreq = 0
            biFreq = 0
        return float(biFreq + self.d1)/(termFreq + self.d1 * self.V)

    def getBigrams(self, tokens):
        returnList = []
        for i in range(len(tokens) - 1): returnList.append((tokens[i], tokens[i+1]))
        return returnList
        
    def setParams(self, parameters):
        '''Here, we expect parameters in the form (d1, Vocab size)'''
        self.d1 = parameters[0]
        self.V = parameters[1]


class UniformModel(LanguageModel):
    def train(self, sentencesIn):
        self.vocab = set()
        for s in sentencesIn:
            self.vocab.update(set(s.split()))
        self.vocabLen = len(self.vocab)

    def logProb(self, sentence):
        return -999999
        return -np.log(self.vocabLen) - len(sentence.split()) * np.log(self.vocabLen+1)
        
    def setParams(self, parameters):
        '''This model requires no parameters'''
        pass


def main():
    y = ['is jack is jack','is jack']
    x = BigramModel(y, parameters=(.001, 100000))

if __name__ == "__main__":
    main()
