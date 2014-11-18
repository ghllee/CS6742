import numpy as np
import sys
import cPickle as pickle
from collections import Counter
import sys
import string
exclude = set(string.punctuation)
loadWidth = 30

def setupLoadBar():
    sys.stdout.write("[%s]" % (" " * loadWidth))
    sys.stdout.flush()
    sys.stdout.write("\b" * (loadWidth+1))

def loadNGrams(ngramfile):
    '''Given the name of an ngram:prior file, return the list of ngrams and the list of priors associated with those ngrams'''
    ngrams = []
    priors = []
    with open(ngramfile) as f:
        for line in f:
            if len(line) != 0:
                tokens = line.split(":")
                ngram, prior = (tokens[0], float(tokens[1]))
                ngrams.append(ngram)
                priors.append(prior)

    return ngrams, np.array(priors, dtype = np.float32)

def getNGrams(stringIn, n):
    '''Given an input string, an "n" in n-gram, return a list of strings representing those n-grams. Might contain repeats.'''
    tokens = stringIn.split()
    returnList = []
    for i in range(len(tokens)-n+1): returnList.append(' '.join(tokens[i:i+n]))
    return returnList


def extractCounts(textList, ngrams, maxN):
    '''Given a list of strings, a list of ngrams we care about, and the maximum number of n that we are interested in, return an array of length ngrams containing the counts of each ngram in textList where n <= maxN.'''
    #dictionary mapping from ngram -> index
    nGramMap = {}
    for i in range(len(ngrams)): nGramMap[ngrams[i]] = i

    returnMatrix = np.empty(len(ngrams), dtype = np.float32)
    #map from {ngram -> count}
    counter = Counter()

    for n in range(1,maxN+1):
        print "Extracting " + str(n) + "-grams"
        setupLoadBar()
        for i in range(len(textList)):
            if i != 0 and i%(len(textList)/loadWidth) == 0:
                sys.stdout.write("-")
                sys.stdout.flush()
            nGrams = getNGrams(textList[i], n)
            counter.update(Counter(nGrams))
        sys.stdout.write("\n")
    for curNGram in ngrams:
        returnMatrix[nGramMap[curNGram]] = counter[curNGram]
    return returnMatrix

def countNGramsInLanguages(lang1, lang2, ngrams, maxN):
    '''Given a list of strings from lang1, a list of strings from lang2, and a list of ngrams to be aware of, returns C = 2 x |ngrams| matrix where C_{ij} is the count of ngram j in group (i+1)'''
    indexToNGram = dict(enumerate(ngrams))
    nGramToIndex = {v: k for k, v in indexToNGram.items()}

    returnArray = np.empty([2, len(ngrams)], dtype = np.float32)
    
    print "Counting " + str(len(lang1)) + " for language one."
    returnArray[0,:] = extractCounts(lang1, ngrams, maxN)

    print "Counting " + str(len(lang2)) + " for language two."
    returnArray[1,:] = extractCounts(lang2, ngrams, maxN)

    return returnArray

def basicSanitize(inString):
    '''Returns a very roughly sanitized version of the input string.'''
    returnString = ' '.join(inString.encode('ascii', 'ignore').strip().split())
    returnString = ''.join(ch for ch in returnString if ch not in exclude)
    returnString = returnString.lower()
    returnString = ' '.join(returnString.split())
    return returnString

def main():
    langF1, langF2, ngrams, maxN, sanitize, output = sys.argv[1:]
    maxN = int(maxN)
    with open(langF1) as f:
        lang1 = pickle.load(f)
    with open(langF2) as f:
        lang2 = pickle.load(f)
    n1 = 1.*sum([len(x) for x in lang1])
    n2 = 1.*sum([len(x) for x in lang2])
    ngrams, priors = loadNGrams(ngrams)
    if sanitize:
        print "Sanitizing input..."
        ngrams = [basicSanitize(x) for x in ngrams]
        lang1 = [basicSanitize(x) for x in lang1]
        lang2 = [basicSanitize(x) for x in lang2]

    countMatrix = countNGramsInLanguages(lang1, lang2, ngrams, maxN)
    zScores = np.empty(priors.shape[0])

    a0 = np.sum(priors)
    print "Computing z scores for " + str(len(ngrams)) + " n grams..."
    setupLoadBar()
    for i in range(len(ngrams)):
        if i != 0 and i%(len(ngrams)/loadWidth) == 0:
                sys.stdout.write("-")
                sys.stdout.flush()
        curNGram = ngrams[i]
        #compute delta
        term1 = np.log((countMatrix[0,i] + priors[i])/(n1 + a0 - countMatrix[0,i] - priors[i]))
        term2 = np.log((countMatrix[1,i] + priors[i])/(n2 + a0 - countMatrix[1,i] - priors[i]))
        
        delta = term1 - term2
        #compute variance on delta
        var = 1./(countMatrix[0,i] + priors[i]) + 1./(countMatrix[1,i] + priors[i])
        #store final score
        zScores[i] = delta/np.sqrt(var)

    sys.stdout.write("\n")
    sortedIndices = np.argsort(zScores)
    with open(output,'w') as f:
        writeStr = ""
        for i in sortedIndices: writeStr += ngrams[i] + " " + str(zScores[i]) + "\n"
        f.write(writeStr[:-1])

if __name__ == "__main__":
    main()
