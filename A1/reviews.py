import re
from collections import defaultdict
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

import matplotlib.pyplot as plt
import matplotlib.cm as cm

import string
import re
import numpy as np

class Review:
    '''Review class, which contains all information about a single review'''
    def __init__(self):
        '''Constructor method that fills in default values'''
        self.productId = ""
        self.userId = ""
        self.profileName = ""
        self.helpfulness = (-1, -1)
        self.score = -1
        self.time = -1
        self.summary = ""
        self.text = ""

    def __str__(self):
        return self.profileName + " gave " + str(self.score) + ": " + self.summary 

    def __eq__(self, other):
        if not isinstance(other, Review): return False
        return self.asList() == other.asList()
    
    def __hash__(self):
        return hash((self.productId, self.userId, self.profileName, self.helpfulness,
               self.score, self.time, self.summary, self.text))

    def asFileString(self):
        '''Returns a review file string formatted version of the review.'''
        returnString = "product/productId: " + self.productId + "\n"
        returnString += "review/userId: " + self.userId + "\n"
        returnString += "review/profileName: " + self.profileName + "\n"
        returnString += "review/helpfulness: " + str(self.helpfulness[0]) + "/" + str(self.helpfulness[1]) + "\n"
        returnString += "review/score: " + str(self.score) + "\n"
        returnString += "review/time: " + str(self.time) + "\n"
        returnString += "review/summary: " + self.summary + "\n"
        returnString += "review/text: " + self.text + "\n"
        return returnString

    def asList(self):
        return [self.productId, self.userId, self.profileName, self.helpfulness,
               self.score, self.time, self.summary, self.text]

    def printReview(self):
        print (self.productId, self.userId, self.profileName, self.helpfulness,
               self.score, self.time, self.summary, self.text)

    def setInfoFromList(self, infoList):
        '''Given a list of information, sets this reviews information to that contained in the input list. Input list must be in order specified in constructor.'''
        (self.productId, self.userId, self.profileName, self.helpfulness,
         self.score, self.time, self.summary, self.text) = tuple(infoList)

def getReviewDictionary(filename):
    '''Given a filename corresponding to a file of the same format as the data provided at http://snap.stanford.edu/data/web-FineFoods.html, returns a dictionary mapping {productId -> [Reviews of that product]}'''
    returnDict = defaultdict(list)
    for r in getReviewListFromFile(filename):
        returnDict[r.productId].append(r)
    return returnDict

def getUserDictionary(filename):
    '''Given a filename corresponding to a file of the same format as the data provided at http://snap.stanford.edu/data/web-FineFoods.html, returns a dictionary mapping {userId -> [Reviews by that user]}'''
    returnDict = defaultdict(list)
    for r in getReviewListFromFile(filename):
        returnDict[r.userId].append(r)
    return returnDict

def getReviewListFromFile(filename):
    '''Given a filename corresponding to a file of the same format as the data provided at http://snap.stanford.edu/data/web-FineFoods.html, returns the list of reviews contained in that file.'''
    returnList = []
    contentRe = r'.*/.*:(.*)\n'
    myFile = open(filename)
    text = myFile.read()
    info = [x.strip() for x in re.findall(contentRe, text)]
    if len(info) % 8 != 0: print "Invalid review file, be wary."
    for i in range(len(info)/8):
        newReview = Review()
        curInfo = info[i*8:(i+1)*8]
        helpfulYes, helpfulNo = [int(x) for x in curInfo[3].split('/')]
        curInfo[3] = (helpfulYes, helpfulNo)
        curInfo[4] = float(curInfo[4])
        curInfo[5] = int(curInfo[5])
        newReview.setInfoFromList(curInfo)
        returnList.append(newReview)
    myFile.close()
    return returnList

def removeDuplicates(dataDict):
    '''Given a dictionary of the form {any key -> [reviews]} removes duplicate reviews from the review lists. If your dictionary is keyed on users, this method will remove all duplicate reviews in the dataset by the same user.'''
    for k, reviews in dataDict.iteritems():
        dataDict[k] = list(set(reviews))

def removeTextTimeDuplicates(dataDict):
    '''Given a dictionary of the form {any key -> [reviews]} removes duplicate reviews from the review lists, where duplicate is defined by identical timestamp and review text. If your dictionary is keyed on users, this method will remove all duplicate reviews in the dataset by the same user.'''
    for k, reviews in dataDict.iteritems():
        remove = []
        for i in range(len(reviews)):
            for j in range(i+1, len(reviews)):
                if reviews[i].text == reviews[j].text and reviews[i].time == reviews[j].time:
                    remove.append(i)
        dataDict[k] = [dataDict[k][i] for i in range(len(dataDict[k])) if i not in remove]

def writeToFile(dataDict, outfilename):
    '''Given a dictionary of the form {any key -> [reviews]} writes all the reviews in the dictionary to the specified output file.'''
    outFile = open(outfilename, 'w')
    for k, reviews in dataDict.iteritems():
        for r in reviews:
            outFile.write(r.asFileString() + "\n")
    outFile.close()

def tokenize(myString, stemmer=None):
    '''Given a string, returns a list of tokens from that string'''
    exclude = set(string.punctuation)
    myString = ''.join(ch for ch in myString if ch not in exclude).lower()
    if stemmer != None:
        myString = ' '.join([stemmer.stem(word) for word in myString.split(" ")])
    myString = re.sub(' +', ' ', myString)
    curTokens = myString.split(' ')
    returnTokens = []
    for t in curTokens:
        try:
            float(t)
            returnTokens.append("####")
        except ValueError:
            returnTokens.append(t)

    return returnTokens


def getTfidfMatrix(reviewList,
                   tokenizeMethod = tokenize,
                   stemObject = None,
                   dimReduceObject = None):
    '''Given a list of reviews, a method of tokenizing objects (which can, optionally, take as a second argument a stem object), (optionally) an object that stemps tokens, and (optionally) an object that reduces the dimensionality of matricies, returns a tfidf matrix of dimension (numDocs x numFeatures (which is either the size of the vocabulary, or the number of dimensions the dimReduceObject used))'''

    if stemObject is not None:
        tokenizeMethod = lambda s: tokenize(s, stemObject)

    tfidfer = TfidfVectorizer(tokenizer = tokenizeMethod, max_df=.8, min_df = 3,
                                  stop_words = 'english',
                                  dtype = np.float32, decode_error = 'ignore')
    documentList = [r.text for r in reviewList]
    tfidfMatrix = tfidfer.fit_transform(documentList).toarray()
    if dimReduceObject is not None:
        tfidfMatrixCompressed = dimReduceObject.fit_transform(tfidfMatrix)
    else:
        tfidfMatrixCompressed = tfidfMatrix
    return tfidfMatrixCompressed, tfidfMatrix, tfidfer

def constrainedKMeans(numClusters, data, minPercent = .1):
    '''Given the number of clusters you want, and the minimum proportion of the data that is allowed to be in a single cluster, returns the cluster centers, assignments for each datapoint, and the distance of each point to each center.'''
    
    additionalClusters = 0
    done = False
    while not done:
        curNumClusters = numClusters + additionalClusters

        kMeansObj = KMeans(curNumClusters)
        curPredictions = kMeansObj.fit_predict(data)

        #Maps from classification number -> list of indices of points in that class
        classificationDict = {}
        for i in range(curNumClusters):
            #Don't know why np.where returns a tuple...
            classificationDict[i] = np.where(curPredictions == i)[0]

        #Reassign additionalClusters of the smallest clusters to get to numClusters
        for i in range(additionalClusters):
            minCluster = min(classificationDict.items(), key = lambda x: len(x[1]))[0]
            minDist = 999999999
            minDistCluster = -1
            for k, v in classificationDict.iteritems():
                if minCluster == k: continue
                dist = np.linalg.norm(np.mean(data[v,:], axis=0)
                                  - np.mean(data[classificationDict[minCluster],:], axis=0))
                if dist < minDist:
                    minDist = dist
                    minDistCluster = k
            #merge minDistCluster and minCluster!
            classificationDict[minDistCluster] = np.append(classificationDict[minDistCluster],
                                                           classificationDict[minCluster])
            classificationDict.pop(minCluster)

        minClusterSize = len(min(classificationDict.items(), key = lambda x: len(x[1]))[1])
        totalPoints = data.shape[0]
        if float(minClusterSize) / totalPoints > minPercent: done = True
        additionalClusters += 1

    predictions = np.array([-1 for x in range(data.shape[0])])
    clusterCenters = np.zeros([numClusters, data.shape[1]])
    distances = np.zeros([data.shape[0], numClusters])
    classesWritten = 0
    for k, v in classificationDict.iteritems():
        predictions[v] = classesWritten
        clusterCenters[classesWritten, :] = np.mean(data[v, :], axis=0)
        classesWritten += 1
    
    for i in range(len(predictions)):
        for j in range(numClusters):
            distances[i,j] = np.linalg.norm(data[i,:] - clusterCenters[j,:])

    return clusterCenters, predictions, distances




def clusterPlot(tfidfMatrix, outFile = None):
    ''' '''
    assert tfidfMatrix.shape[1] == 2, "clusters can only be visualized in two dimensions!"
    #clusterPredictions = clusterObject.fit_predict(tfidfMatrix)
    
    centroids, clusterPredictions = constrainedKMeans(2, tfidfMatrix) 
    numClusters = np.max(clusterPredictions) + 1
    colors = cm.rainbow(np.linspace(0, 1, numClusters))

    centroids = []
    for i in range(numClusters):
        clusterIndices = [t for t in range(len(clusterPredictions))
                          if clusterPredictions[t] == i]
        centroids.append(np.mean(tfidfMatrix[clusterIndices,:], axis=0))

    for i in range(len(colors)):
        plt.scatter(centroids[i][0], centroids[i][1], s = 100, marker='+', color = colors[i])
    for i in range(len(clusterPredictions)):
        plt.scatter(tfidfMatrix[i][0], tfidfMatrix[i][1], s = 1,
                    color = colors[clusterPredictions[i]])
    plt.title("2-D review clustering")
    if outFile != None:
        plt.savefig(outFile)
    else:
        plt.show()
    plt.clf()



def main():
    reviews = getReviewDictionary("foods.txt")
    removeDuplicates(reviews)
    removeTextTimeDuplicates(reviews)
    
    n = 500 #number of top reviews to consider
    helpratio = .6 #threshold required before considered "helpful"

    #Getting the top n most reviewed items...
    #get the item with the most "helpful" reviews
    mostReviewed = sorted(reviews, key=lambda k: -sum([r.helpfulness[1]!=0 for r in reviews[k]]))[:n]
    itemCounter = 0
    productIdFile = open("productIds.txt", 'w')
    for popItem in mostReviewed:
        productIdFile.write(popItem + '\n')
        outFile = open("temp/" + str(itemCounter) + '.csv' , 'w')
        outFileTypicalWords = open("temp/" + str(itemCounter) + '.txt' , 'w')

        compressed, rawtfidf, tfidfObject = getTfidfMatrix(reviews[popItem],
                                                           tokenizeMethod = tokenize,
                                                           stemObject = None,
                                                           dimReduceObject = PCA(n_components=100))


        centers, predictions, distances = constrainedKMeans(10, compressed, minPercent=.03)
        words = tfidfObject.get_feature_names()
        #print words with highest average tfidf per cluster
        for i in range(10):
            #find the mean tfidf statistics for this particular cluster
            meanTfidf = np.mean(rawtfidf[np.where(np.array(predictions) == i)[0],:], axis=0)
            numTop = 10
            top = np.sort(meanTfidf)[:-(numTop + 1):-1]
            topIndices = np.array([], dtype=np.int)
            for j in range(numTop):
                topIndices = np.append(topIndices, np.where(meanTfidf == top[j])[0])
            topIndices = np.unique(topIndices)
            outFileTypicalWords.write("Cluster " + str(i) + "\n")
            for t in topIndices:
                outFileTypicalWords.write(words[t] + "\n")


        for i in range(len(reviews[popItem])):
            curReview = reviews[popItem][i]
            minDist = np.min(distances[i,:])
            helpful = 0
            if curReview.helpfulness[1] == 0:
                pass
            else:
                helpRatio = float(curReview.helpfulness[0])/curReview.helpfulness[1]
                if helpRatio > helpratio: helpful = 1

            outFile.write(str(minDist) + "," + str(helpful) + "\n")
        
        outFile.close()
        outFileTypicalWords.close()
        itemCounter += 1
        print itemCounter

    productIdFile.close()


if __name__ == "__main__":
    main()
