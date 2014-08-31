import re
from collections import defaultdict

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

def writeToFile(dataDict, outfilename):
    '''Given a dictionary of the form {any key -> [reviews]} writes all the reviews in the dictionary to the specified output file.'''
    outFile = open(outfilename, 'w')
    for k, reviews in dataDict.iteritems():
        for r in reviews:
            outFile.write(r.asFileString() + "\n")
    outFile.close()


def main():
    reviews = getUserDictionary("foods.txt")
    removeDuplicates(reviews)
    outfile = "noduplicates.txt"
    writeToFile(reviews, outfile)


if __name__ == "__main__":
    main()
