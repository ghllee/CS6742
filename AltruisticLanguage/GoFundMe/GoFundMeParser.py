# File contains the kickstarter project class and related methods/classes
from datetime import datetime
from dateutil.parser import parse
from bs4 import BeautifulSoup
import bs4
import cPickle as pickle
import time
import os
import re
import string
from collections import Counter, defaultdict
from nltk.corpus import stopwords
import numpy as np
import operator

class GFMProject:
    def __init__(self):
        self.name = ""
        self.category = ""
        self.updates = []
        self.text = ""
    def __str__(self):
        retStr = ""
        retStr += self.name + "\n"
        retStr += self.category + "\n"
        retStr += self.text + "\n"
        retStr += "Num Updates: " + str(len(self.updates)) + "\n"
        retStr += "\n\n".join([x.text for x in self.updates])
        return retStr
    def __ne__(self, other):
        if self.name != other.name and self.category != other.category and self.text != other.text:
            return True
        return False
    def __eq__(self, other):
        if self.name == other.name and self.category == other.category and self.text == other.text:
            return True
        return False
    def __hash__(self):
        return hash((self.name, self.category, self.text))

class GFMUpdate:
    def __init__(self):
        self.project = None
        self.text = ""

exclude = set(string.punctuation)
def basicSanitize(inString, removePunct = False, lower = False):
    '''Returns a very roughly sanitized version of the input string.'''
    returnString = ' '.join(inString.encode('ascii', 'ignore').strip().split())
    if removePunct:
        returnString = ''.join(ch for ch in returnString if ch not in exclude)
    if lower: returnString = returnString.lower()

    returnString = ' '.join(returnString.split())
    return returnString

def fillProjectInfo(soup, project):
    '''Given a input soup object and the current project, fills in the non reward/faq info of that project.''' 

    for div in soup.find_all('div'):
        if div.get('class') is not None and 'pagetitle' in div.get('class'):
            project.name = div.getText(separator=' ')
        if div.get('class') is not None and 'pg_msg' in div.get('class'):
            project.text = basicSanitize(div.getText(separator=' '))
        if div.get('class') is not None and 'update_content' in div.get('class'):
            curUpdate = GFMUpdate()
            curUpdate.project = project
            curUpdate.text = basicSanitize(div.getText(separator=' '))
            curUpdate.text = curUpdate.text.replace("Subscribe to Updates","")
            curUpdate.text = curUpdate.text.replace("Show All","")
            curUpdate.text = " ".join(curUpdate.text.split())
            project.updates.append(curUpdate)

def makeDatabase(folderName, outputPickleFolder):
    '''Given a database file input, returns a list of project objects and pickles the output'''
    projects = []
    validDirs = os.walk(folderName).next()[1]
    if not os.path.exists(outputPickleFolder):
        os.makedirs(outputPickleFolder)
    for d in validDirs:
        print d
        validFiles = [x for x in os.listdir(folderName + "/" + d)
                      if re.search("^\d+\.html$", x) is not None]
        print "Parsing " + str(len(validFiles)) + " files"
        fileCount = 0
        for myFile in sorted(validFiles, key = lambda x: int(x.split('.')[0])):
            if fileCount != 0 and fileCount % 100 == 0: print fileCount
            newProject = GFMProject()
            curFile = open(folderName + "/" + d + "/" + myFile)
            curText = curFile.read()
            curSoup = BeautifulSoup(curText)
            curFile.close()
            fillProjectInfo(curSoup, newProject)
            newProject.category = d
            projects.append(newProject)
            fileCount += 1

        myOut = open(outputPickleFolder + '/' + d + '.pickle', 'w')
        pickle.dump(projects, myOut, -1)
        myOut.close()
        projects = []

def loadProjects(pickleDir):
    files = [x for x in os.listdir(pickleDir) if x[-6:] == 'pickle']
    projList = []
    for f in files:
        with open(pickleDir + "/" + f) as myF: projList.extend(pickle.load(myF))
    return projList

def extractTextFeatures(projects, minOccur = 10, nGram = 3):
    '''Given a list of projects, a minimum number of occurances, and maximum sized n-gram of interest, return a |projects| x |features| n-gram count matrix and list of n-grams in the order represented, given that the selected features appear in a least minOccur projects and at least once in every category.'''

    gramCatCounter = defaultdict(lambda: Counter())
    nGramCounter = Counter()
    catCounter = Counter()
    catGramDict = defaultdict(set)

    myGramFun = lambda x,y: getNGrams(x, y, toLower = True, removePunct = True)

    for n in range(1,nGram+1):
        print "Extracting " + str(n) + "-grams"
        for p in projects:
            nGrams = myGramFun(p.text, n)
            for g in nGrams:
                nGramCounter[g] += 1
                gramCatCounter[p.category][g] += 1
            catGramDict[p.category].update(set(nGrams))
            catCounter[p.category] += 1

    validGrams = [x for x in proportionalIntersection(catGramDict.values(), proportion=1)
                  if nGramCounter[x] > minOccur]
    print len(validGrams)
    print catCounter

    gramToVar = {}
    i = 1
    print "Filtering..."
    for v in validGrams:
        if i % 1000 == 0: print i
        perDocList = []
        for cat, catCount in catCounter.iteritems():
            perDocList.append((gramCatCounter[cat][v]*.1)/catCount)
        gramToVar[v] = 1.0*(np.max(perDocList)-np.min(perDocList))/np.max(perDocList)

    validGrams = [x[0] for x in
                  sorted(gramToVar.items(), key = operator.itemgetter(1))[:int(.9*len(gramToVar))]]
    
    with open('gfm90SW.ngrams','w') as f:
        words = ""
        for v in validGrams:
            words += v + "\n"
        f.write(words[:-1])

    validGrams = [v for v in validGrams if not
                  set.issubset(set(v.split()), set(stopwords.words('english')))]

    with open('gfm90.ngrams','w') as f:
        words = ""
        for v in validGrams:
            words += v + "\n"
        f.write(words[:-1])

def proportionalIntersection(setList, proportion = .5):
    '''Given a list of sets, return the set of items that exist in a least floor(proportion*numSets)'''
    candidates = set()
    for l in setList:
        candidates.update(l)

    minNumSets = np.floor(proportion*len(setList))
    #maps from item -> numSets
    c = Counter()
    for s in setList:
        for item in s: c[item] += 1
    
    returnList = []
    for k,v in c.iteritems():
        if v >= minNumSets: returnList.append(k)

    return returnList

def getNGrams(stringIn, n, toLower = True, removePunct = False):
    '''Given an input string, an "n" in n-gram, whether or not we should lowercase, whether or not we should remove punct, and a list of stopwords (None of remove none), return a list of strings representing those n-grams. Might contain repeats.'''
    if toLower: stringIn = stringIn.lower()
    exclude = set(string.punctuation)
    if removePunct: stringIn = ''.join(ch for ch in stringIn if ch not in exclude)
    tokens = stringIn.split()

    returnList = []
    for i in range(len(tokens)-n+1): returnList.append(' '.join(tokens[i:i+n]))
    return returnList


def main():
    projects = set(loadProjects("output"))
    projects = [x for x in projects if "News" not in x.category and "Other" not in x.category]
    print projects[0].category
    #catDict = defaultdict(list)
    #for p in projects: catDict[p.category].append(p)
    
    #for k,v in catDict.iteritems():
    #    with open("projectTexts/" + k + ".pickle", 'w+') as f:
    #        pickle.dump([x.text for x in v], f, -1)

    myTexts = [p.text for p in projects]
    with open('GFMText.pickle','w') as f:
        pickle.dump(myTexts, f, -1)
    quit()
    
    #extractTextFeatures(projects)

    #with open('gofundme50.ngrams','w') as f:
    #    for n in nGrams: f.write(n + "\n")
    #for p in projects: counter[p.name] += 1
    #for k,v in counter.iteritems():
    #    if v >= 2: print k
    #makeDatabase("GoFundMe", "output")

if __name__ == "__main__":
    main()
