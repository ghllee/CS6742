import re
import cPickle as pickle
import string
from collections import defaultdict, Counter
import numpy as np
from nltk.corpus import stopwords

exclude = set(string.punctuation)

class Product:
    def __init__(self):
        self.ID = ""
        self.description = ""
        self.mainCats = []

def basicSanitize(inString, removePunct = False, lower = False):
    '''Returns a very roughly sanitized version of the input string.'''
    returnString = ' '.join(inString.encode('ascii', 'ignore').strip().split())
    if removePunct:
        returnString = ''.join(ch for ch in returnString if ch not in exclude)
    if lower: returnString = returnString.lower()
    returnString = ' '.join(returnString.split())
    return returnString

def getNGrams(stringIn, n, toLower = True, removePunct = False):
    '''Given an input string, an "n" in n-gram, whether or not we should lowercase, whether or not we should remove punct, and a list of stopwords (None of remove none), return a list of strings representing those n-grams. Might contain repeats.'''
    if toLower: stringIn = stringIn.lower()
    exclude = set(string.punctuation)
    if removePunct: stringIn = ''.join(ch for ch in stringIn if ch not in exclude)
    tokens = stringIn.split()
    returnList = []
    for i in range(len(tokens)-n+1): returnList.append(' '.join(tokens[i:i+n]))
    return returnList

def proportionalIntersection(setList, proportion = .5):
    '''Given a list of sets, return the set of items that exist in at least floor(proportion*numSets)'''
    candidates = set()
    for l in setList:
        candidates.update(l)
    minNumSets = np.floor(proportion*len(setList))

    c = Counter()
    for s in setList:
        for item in s: c[item] += 1

    returnList = []
    for k,v in c.iteritems():
        if v >= minNumSets: returnList.append(k)

    return returnList


def extractTextFeatures(products, minOccur = 50, nGram = 3):
    '''Given a list of products, a minimum number of occurances, and maximum sized n-gram of interest, return a |projects| x |features| n-gram count matrix and list of n-grams in the order represented, given that the selected features appear in a least minOccur projects and at least once in every category.'''
    myGramFun = lambda x,y: getNGrams(x, y, toLower = True, removePunct = True)
    validGrams = []

    for n in range(1,nGram+1):
        catGramDict = defaultdict(set)
        nGramCounter = Counter()
        print "Extracting " + str(n) + "-grams"
        for p in products:
            nGrams = myGramFun(p.description, n)
            for g in nGrams:
                nGramCounter[g] += 1
            for c in p.mainCats:
                catGramDict[c].update(set(nGrams))
        curValidGrams = [x for x in proportionalIntersection(catGramDict.values(), proportion=.7)
                         if nGramCounter[x] > minOccur]

        validGrams.extend(curValidGrams)

    with open('amazon50SW.ngrams','w') as f:
        words = ""
        for v in validGrams:
            words += v + "\n"
        f.write(words[:-1])

    validGrams = [v for v in validGrams if not
                  set.issubset(set(v.split()), set(stopwords.words('english')))]

    with open('amazon50.ngrams','w') as f:
        words = ""
        for v in validGrams:
            words += v + "\n"
        f.write(words[:-1])

def readProductsFromFile(descriptions, categories):
    '''Given a descriptions file and a categories file, returns a list of Products'''    
    #maps from productId to Product
    idToProduct = {}
    print "Loading descriptions"
    with open(descriptions) as f:
        curProduct = None
        for line in f:
            if len(line.split()) == 0:
                continue
            else:
                matchObj = re.match("product/(.+): (.+|)", line)
                matches = matchObj.groups()
                #a new product
                if matches[0] == 'productId':
                    if curProduct is not None:
                        idToProduct[curProduct.ID] = curProduct
                    curProduct = Product()
                    curProduct.ID = basicSanitize(matches[1])
                elif matches[0] == 'description':
                    curProduct.description = basicSanitize(matches[1])
    
    print "Loading categories"
    with open(categories) as f:
        curId = None
        for line in f:
            if len(line.strip()) == 0: continue
            if line[0] != ' ':
                curId = line.strip()
            else:
                if curId not in idToProduct: continue
                idToProduct[curId].mainCats.append(line.split(',')[0].strip())
                if idToProduct[curId].mainCats[-1] == '':
                    print line

    return [x for x in idToProduct.values() if len(x.mainCats) != 0 and
            len(x.description) > 0]

def loadFromFile(name):
    with open(name) as f:
        products = pickle.load(f)
    return products

def main():
    pass
    products = loadFromFile("products.pickle")
    #products = readProductsFromFile("descriptions.txt","categories.txt")
    extractTextFeatures(products)
    #pickle.dump(products, open("products.pickle",'w'), -1)

    
    

if __name__ == "__main__":
    main()
