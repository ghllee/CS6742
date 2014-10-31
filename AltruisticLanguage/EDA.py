import cPickle as pickle
from KickstarterParser import *
import random
import numpy as np
import matplotlib.pyplot as plt
import string
from collections import defaultdict, Counter
from scipy.stats import chi2_contingency
from nltk.corpus import stopwords
import string
from sklearn.linear_model import LogisticRegression

class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
getch = _GetchUnix()

def loadProjects(folderName, numFiles = None):
    '''Given the name of the folder where the pickled project files are, return a list of the projects contained in those pickled files. Furthermore, if numFiles is not None, return the list containing data from only that number of files.'''
    validFiles = [x for x in os.listdir(folderName) if re.search("^\d+\.pickle$", x) is not None]
    if numFiles is not None: validFiles = validFiles[:numFiles]
    projects = []
    for v in validFiles:
        fileName = folderName + "/" + v
        myFile = open(fileName)
        curP = pickle.load(myFile)
        projects.extend(curP)
    
    return projects

def getProjectsOfCategory(category, allProjects):
    returnList = []
    for p in allProjects:
        if p.category == category:
            returnList.append(p)

    return returnList

def getCategories(projects):
    return set([x.category for x in projects])


def printGroupStatistics(projects):
    cats = getCategories(projects)
    
    print '{:>18}  {:>18}  {:>18}  {:>18}'.format("Category",
                                                  "Num Projects",
                                                  "Succ Ratio",
                                                  "Ave Raised")
    for c in cats:
        if c is '': continue
        catProjects = getProjectsOfCategory(c, projects)
        succRatio = sum([1 for p in catProjects if p.result == 1])*1./len(catProjects)
        aveRaised = sum([p.raised for p in catProjects])*1./len(catProjects)
        print '{:>18}  {:>18}  {:>18}  {:>18}'.format(c,
                                                      len(catProjects),
                                                      succRatio,
                                                      aveRaised)

def getSeedPhrases():
    return ['gratitude', 'your name', 'counts', 'access', 'personal', 'mention', 'thank you']

def basicClean(myString):
    '''Given a string, returns a cleaned version of that string'''
    exclude = set(string.punctuation)
    myString = ''.join(ch for ch in myString if ch not in exclude).lower()
    return re.sub(' +', ' ', myString)


def rewardLabel(inputRewards, posFile, negFile, tokenFile = None):
    '''Given a list of rewards, a positive file to output altruistic projects,
    and a negative file to output not altruistic projects, save pickled version of the
    positive and negative examples'''
    pos = []
    neg = []
    token = []
    print chr(27) + "[2J"
    count = 1
    for p in inputRewards:
        print str(count) + "/" + str(len(inputRewards)) 
        print p.project.name
        print p.text
        print p.cost
        val = getch()
        if val.lower() == 'y':
            pos.append(p)
        elif val.lower() == 'q':
            break
        elif tokenFile is not None and val.lower() == 'h':
            token.append(p)
        else:
            neg.append(p)
            
        print chr(27) + "[2J"
        count += 1

    posOut = open(posFile + ".pickle", 'w')
    negOut = open(negFile + ".pickle", 'w')
    if tokenFile is not None: tokenOut = open(tokenFile + ".pickle", 'w')

    pickle.dump(pos, posOut, -1)
    pickle.dump(neg, negOut, -1)
    if tokenFile is not None: pickle.dump(token, tokenOut, -1)

    posOut.close()
    negOut.close()
    

def basicPlots(projects):
    '''Given some projects make some basic plots.'''
    dist = []
    prices = []
    out = open("kickstarter.txt",'w')
    for p in projects:
        out.write(basicClean(p.text) + '\n')
        if len(p.rewards) == 0: continue
        if p.backers == 0: continue
        lowCost = sorted(p.rewards, key = lambda x: x.cost)[0]
        dist.append(lowCost.numBackers*1./p.backers)
        prices.append(lowCost.cost)
        if lowCost.cost > 1000: print p.name
    out.close()
    plt.hist(dist, bins=20)
    plt.savefig("dist.png")
    plt.figure()
    print max(prices)
    print min(prices)
    plt.hist(sorted(prices)[10:-50], bins = 20)
    plt.savefig("prices.png")

def labelThings(projects):
    '''Given a list of projects, have the user label items.'''
    vgs = [x for x in projects if x.category.lower()
           in ["technology","open hardware","board & card games","product design"]]
    toLabel = []
    for p in vgs:
        sortedRewards = sorted(p.rewards, key = lambda x: x.cost)
        if len(sortedRewards) == 0: continue
        toLabel.append(sortedRewards[0])
        if len(sortedRewards) != 1:
            toLabel.append(sortedRewards[1])
    
    rewardLabel(toLabel, "posTechOHBoardProd","negTechOHBoardProd", tokenFile = "tokTechOHBoardProd")

def buildCategoryDictionary(projects):
    '''Given a list of projects, builds a dictionary that maps from {category -> [p1, p2, p3]} for all projects in the input.'''
    x = defaultdict(list)
    for p in projects: x[p.category].append(p)
    return x

def categoryAltruisticPropTest(projects):
    '''Given a list of projects, split on category. Then, conduct a proportion test for for each category for proportion of altruistic donations vs not altruistic donations split on success/failure.'''
    catDict = buildCategoryDictionary(projects)
    
    print '{:>18}  {:>18}  {:>18}  {:>18}'.format("Category",
                                                  "Alt Ratio Succ",
                                                  "Alt Ratio Fail",
                                                  "p-val")
    for cat, projectList in catDict.iteritems():
        if len(cat) == 0: continue
        success = [x for x in projectList if x.result and x.backers != 0]
        fail = [x for x in projectList if not x.result and x.backers != 0]
        sucAlt = sum([x.backers - sum([y.numBackers for y in x.rewards]) for x in success])
        failAlt = sum([x.backers - sum([y.numBackers for y in x.rewards]) for x in fail])
        sucTotal = sum([x.backers for x in success])
        failTotal = sum([x.backers for x in fail])

        chi2, p, dof, ex = chi2_contingency([[sucAlt, failAlt],[sucTotal-sucAlt, failTotal-failAlt]])

        propSuc, propFail = float(sucAlt*1./sucTotal), float(failAlt*1./failTotal)
        
        print '{:>18}  {:>18.4f}  {:>18.4f}  {:>18.4f}'.format(cat, propSuc, propFail, p)

        #if propSuc > propFail: print "Greater proportion with successful projects"
        #else: print "Greater proportion with failed projects"

def categoryAltruisticMeanValueTest(projects):
    '''Given a list of projects, split on category. Then, conduct a basic t-test for mean altruistic donation value over each of the categories split on succss/failure.'''
    catDict = buildCategoryDictionary(projects)
    for cat, projectList in catDict.iteritems():
        if len(cat) == 0: continue
        success = [x for x in projectList if x.result and x.backers != 0]
        fail = [x for x in projectList if not x.result and x.backers != 0]
        #the altruistic values per backer
        #perBackerSucc = [(x.raised - sum([y.numBackers*y.cost for y in x.rewards]))*1./x.backers
        #                 for x in success if x.backers != 0]
        #perBackerFail = [(x.raised - sum([y.numBackers*y.cost for y in x.rewards]))*1./x.backers
        #                 for x in fail if x.backers != 0]

        totalAltSucc = sum([(x.raised - sum([y.numBackers*y.cost for y in x.rewards]))
                            for x in success])
        totalBackersSucc = sum([x.backers for x in success])

        totalAltFail = sum([(x.raised - sum([y.numBackers*y.cost for y in x.rewards]))
                            for x in fail])
        totalBackersFail = sum([x.backers for x in fail])


        print cat, totalAltSucc/totalBackersSucc, totalAltFail/totalBackersFail

def basicStats(projectsIn):
    '''Given some projects, print out some basic altruistic stats.'''
    projects = [p for p in projectsIn]

    succ = len([p for p in projects if p.result])
    fail = len(projects) - succ
    print "There are {} successful and {} unsuccessful projects".format(succ, fail)
    
    numDonations = sum([p.backers for p in projects])
    numAltruisticDonations = sum([p.backers - sum([y.numBackers for y in p.rewards]) for p in projects])
    print "The dataset consists of {} dontation events, of which {} are altruistic".format(numDonations, numAltruisticDonations)
    print "That constitutes {0:.4f} percent of all donations".format(numAltruisticDonations*1./numDonations)

    totalRaised = sum([p.raised for p in projects])
    totalAltRaised = sum([p.raised - sum([y.numBackers*y.cost for y in p.rewards])
                         for p in projects])
    print "The total amount raised is {}. The total altruistic giving is {}".format(totalRaised,
                                                                                    totalAltRaised)
    print "That constitutes {0:.4f} percent of all donations".format(totalAltRaised*1./totalRaised)

def penLogisticRegression(featureMatrix, target):
    '''Given a feature matrix of size |items| x |features| and a binary target vector of length |items|, perform penalized logistic regression of the feature matrix on the target.'''
    regressor = LogisticRegression(penalty = 'l2', dual=False)
    regressor.fit(featureMatrix, target)
    return regressor
    
def getCategoryControlFeatures(projects):
    '''Given a list of projects, return a |projects| x |category| sized binary matrix, representing the encoding of the input project's categories, and list of categories in the order represented.'''
    catDict = buildCategoryDictionary(projects)
    returnMatrix = np.zeros([len(projects), len(catDict)], dtype = np.float32)
    cats = catDict.keys()

    for i in range(len(projects)):
        returnMatrix[i, cats.index(projects[i].category)] = 1
    return returnMatrix, cats


def getExtraControlFeatures(projects):
    '''Given a list of projecst, return a |projects| x |features| sized matrix, representing the project control features of interest, and a list of features in the order represented.'''

    features = ['goal','durationDays','numLevels','minPledge','midPledge','maxPledge',
                'featured', 'video', 'numUpdates','numComments','fbConnect', 'featured',
                'numFAQ', 'faqAveLen','creatorNumBacked', 'latitude', 'longitude', 
                'daysSinceEpochStart', 'aveRewardLen', 'summaryLen']
                
    returnMatrix = np.zeros([len(projects),len(features)], dtype = np.float32)

    for i in range(len(features)):
        curFeature = features[i]
        for j in range(len(projects)):
            curProject = projects[j]
            if curFeature == 'goal':
                returnMatrix[j,i] = curProject.goal
            elif curFeature == 'durationDays': 
                returnMatrix[j,i] = curProject.duration
            elif curFeature == 'numLevels':
                returnMatrix[j,i] = len(curProject.rewards)
            elif curFeature == 'minPledge':
                if len(curProject.rewards) == 0:
                    returnMatrix[j,i] = 0
                    continue
                returnMatrix[j,i] = np.min([x.cost for x in curProject.rewards])
            elif curFeature == 'midPledge':
                if len(curProject.rewards) == 0:
                    returnMatrix[j,i] = 0
                    continue
                returnMatrix[j,i] = np.median([x.cost for x in curProject.rewards])
            elif curFeature == 'maxPledge':
                if len(curProject.rewards) == 0:
                    returnMatrix[j,i] = 0
                    continue
                returnMatrix[j,i] = np.max([x.cost for x in curProject.rewards])
            elif curFeature == 'featured':
                returnMatrix[j,i] = curProject.featured
            elif curFeature == 'video':
                returnMatrix[j,i] = curProject.hasVideo
            elif curFeature == 'numUpdates':
                returnMatrix[j,i] = curProject.updates
            elif curFeature == 'numComments':
                returnMatrix[j,i] = curProject.comments
            elif curFeature == 'fbConnect':
                returnMatrix[j,i] = curProject.creatorFacebookConnect
            elif curFeature == 'featured':
                returnMatrix[j,i] = curProject.featured
            elif curFeature == 'numFAQ': 
                returnMatrix[j,i] = len(curProject.faqs)
            elif curFeature == 'faqAveLen':
                if len(curProject.faqs) == 0:
                    returnMatrix[j,i] = 0
                    continue
                returnMatrix[j,i] = sum([len(x.answer)
                                         for x in curProject.faqs])*1./len(curProject.faqs)
            elif curFeature == 'creatorNumBacked':
                returnMatrix[j,i] = curProject.creatorNumBacked
            elif curFeature == 'latitude':
                returnMatrix[j,i] = curProject.lat
            elif curFeature == 'longitude':
                returnMatrix[j,i] = curProject.lon
            elif curFeature == 'daysSinceEpochStart':
                epoch = datetime.utcfromtimestamp(0)
                numDays = int((curProject.startDate - epoch).days)
                returnMatrix[j,i] = numDays 
            elif curFeature == 'aveRewardLen':
                if len(curProject.rewards) == 0:
                    returnMatrix[j,i] = 0
                    continue
                returnMatrix[j,i] = sum([len(x.text)
                                         for x in curProject.rewards])*1./len(curProject.rewards)
            elif curFeature == 'summaryLen':
                returnMatrix[j,i] = len(curProject.shortText)
            else:
                print curFeature + " not a valid feature."
    
    return returnMatrix, features
        
def extractTextFeatures(projects, minOccur = 30, nGram = 3):
    '''Given a list of projects, a minimum number of occurances, and maximum sized n-gram of interest, return a |projects| x |features| n-gram count matrix and list of n-grams in the order represented, given that the selected features appear in a least minOccur projects and at least once in every category.'''

    #dict mapping from category -> set of n grams in that category
    catGramDict = defaultdict(set)
    #counter mapping from n-gram -> count
    nGramCounter = Counter()

    myGramFun = lambda x,y: getNGrams(x, y, toLower = True, removePunct = True)

    for n in range(1,nGram+1):
        print "Extracting " + str(n) + "-grams"
        for p in projects:
            nGrams = myGramFun(p.text, n)
            for g in nGrams: nGramCounter[g] += 1
            catGramDict[p.category].update(set(nGrams))
    
    validGrams = [x for x in set.intersection(*catGramDict.values()) if nGramCounter[x] >= minOccur]
    validGrams = [v for v in validGrams if not
                  set.issubset(set(v.split()), set(stopwords.words('english')))] 

    print "Using {} n-grams".format(len(validGrams))
    
    returnMatrix = np.zeros([len(projects),len(validGrams)], dtype = np.float32)
    for i in range(len(projects)):
        curProject = projects[i]
        for j in range(len(validGrams)):
            curGram = validGrams[j]
            returnMatrix[i,j] += projects[i].text.count(curGram)
    
    return returnMatrix, validGrams


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
    projects = loadProjects('output')
    projects = [p for p in projects if len(p.category) != 0]
    basicStats(projects)
    
    featureMatrix1, ngrams = extractTextFeatures(projects)
    featureMatrix2, cats = getCategoryControlFeatures(projects)
    featureMatrix3, controls = getExtraControlFeatures(projects)
    featureMatrix4, success = np.array([p.result == 1 for p in projects], dtype = np.int), ['success']

    data = np.concatenate([featureMatrix1, featureMatrix2, featureMatrix3, featureMatrix4], axis = 1)
    headers = np.concatenate([ngrams, cats, controls, success])

    with open('success.csv', 'wb') as f:
        headerString = ','.join(headers)[:-1]
        f.write(headerString + "\n")
        np.savetxt(f, data, delimiter=",")


if __name__ == '__main__':
    main()
