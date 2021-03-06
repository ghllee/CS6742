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
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn import preprocessing
from scipy.sparse import csr_matrix
from scipy.io import mmwrite
import matplotlib.pyplot as plt
import operator

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

def getCategories(projects):
    return set([x.category for x in projects])

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

def buildSubCategoryDictionary(projects):
    '''Given a list of projects, builds a dictionary that maps from {sub -> [p1, p2, p3]} for all projects in the input with subcategories.'''
    x = defaultdict(list)
    for p in projects:
        if p.subCategory is not None:
            x[p.subCategory].append(p)
    return x

def categoryAltruisticPropTest(projects):
    '''Given a list of projects, split on category. Then, conduct a proportion test for for each category for proportion of altruistic donations vs not altruistic donations split on success/failure.'''

    catDict = buildCategoryDictionary(projects)
    subcatDict = buildSubCategoryDictionary(projects)

    catDict = dict(catDict.items() + subcatDict.items())

    print '{:>18}  {:>18}  {:>18}  {:>18}'.format("Category",
                                                  "Alt Ratio Succ",
                                                  "Alt Ratio Fail",
                                                  "p-val")

    barVals = []
    barColors = []
    barLabels = []
    curIndex = 0
    barLefts = []
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
        
        barVals.append(propFail-propSuc)
        barColors.append('b' if p < .01 else 'r')
        barLabels.append(cat)
        barLefts.append(curIndex)
        curIndex += 1

        print '{:>18}  {:>18.4f}  {:>18.4f}  {:>18.4f}'.format(cat, propSuc, propFail, p)

        #if propSuc > propFail: print "Greater proportion with successful projects"
        #else: print "Greater proportion with failed projects"

    plt.bar(barLefts, barVals, align='center', color = barColors)
    plt.xticks([b+.5 for b in barLefts], barLabels, rotation=45, ha='right')
    figure = plt.gcf() # get current figure
    figure.set_size_inches(14, 4)
    plt.xlim([-1.1, len(barLefts)+.1])
    plt.ylim([min(barVals) - .002, max(barVals) + .002])
    plt.savefig("failSuccess.png", dpi = 100, bbox_inches='tight')

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
    regressor = LogisticRegression(penalty='l1', C=.01)
    #regressor = DummyClassifier()
    regressor.fit(featureMatrix, target)
    return regressor
    
def getCategoryControlFeatures(projects):
    '''Given a list of projects, return a |projects| x |category| sized binary matrix, representing the encoding of the input project's categories, and list of categories in the order represented.'''
    catDict = buildCategoryDictionary(projects)
    subcatDict = buildSubCategoryDictionary(projects)
    returnMatrix = np.zeros([len(projects), len(catDict) + len(subcatDict)], dtype = np.float32)
    cats = catDict.keys()
    subcats = subcatDict.keys()

    for i in range(len(projects)):
        curProject = projects[i]
        if curProject.subCategory is None:
            returnMatrix[i, cats.index(projects[i].category)] = 1
        else:
            returnMatrix[i, len(cats) + subcats.index(projects[i].subCategory)] = 1
    return returnMatrix, cats + subcats


def getExtraControlFeatures(projects):
    '''Given a list of projecst, return a |projects| x |features| sized matrix, representing the project control features of interest, and a list of features in the order represented.'''

    #features = ['goal','durationDays','numLevels','minPledge','midPledge','maxPledge',
    #            'featured', 'video', 'numUpdates','numComments','fbConnect',
    #            'numFAQ', 'faqAveLen','creatorNumBacked', 'latitude', 'longitude', 
    #            'daysSinceEpochStart', 'aveRewardLen', 'summaryLen']


    #features = ['goal','durationDays','numLevels','minPledge','midPledge','maxPledge',
    #            'featured', 'video', 'numUpdates','numComments','fbConnect',
    #            'numFAQ', 'faqAveLen','creatorNumBacked', 'latitude', 'longitude', 
    #            'daysSinceEpochStart', 'aveRewardLen', 'summaryLen']

    features = ['goal', 'durationDays', 'numLevels', 'minPledge', 'featured', 'video',
                'numUpdates', 'numComments', 'fbConnect', 'success']
           
    returnMatrix = np.zeros([len(projects),len(features)], dtype = np.float32)

    for i in range(len(features)):
        curFeature = features[i]
        for j in range(len(projects)):
            curProject = projects[j]
            if curFeature == 'goal':
                returnMatrix[j,i] = curProject.goal
            elif curFeature == 'success':
                returnMatrix[j,i] = curProject.result
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
      

def getValidGrams(projects, minOccur = 50, nGram = 3):
    '''Given a list of projects, return the valid set of n-grams associated with that set.'''
    myGramFun = lambda x,y: getNGrams(x, y, toLower = True, removePunct = True)
    nGramCounter = Counter()
    catGramDict = defaultdict(set)

    for n in range(1,nGram+1):
        print "Extracting " + str(n) + "-grams"
        for p in projects:
            nGrams = myGramFun(p.text, n)
            for r in p.rewards:
                nGrams.extend(myGramFun(r.text,n))
            for g in nGrams:
                nGramCounter[g] += 1
            catGramDict[p.category].update(set(nGrams))

    for g in gramsInQuestion:
        print g, nGramCounter[g]
        catsNotIn = []
        for k,v in catGramDict.iteritems():
            if g not in v: catsNotIn.append(k)
        print catsNotIn
        print "~"*5

    validGrams = set([v for v in set.intersection(*catGramDict.values())
                      if nGramCounter[v] >= minOccur])

    validGrams = set([v for v in validGrams if not
                  set.issubset(set(v.split()), set(stopwords.words('english')))])


    return validGrams

def extractTextFeatures(projects, minOccur = 10, nGram = 3, counts=False):
    '''Given a list of projects, a minimum number of occurances, and maximum sized n-gram of interest, return a |projects| x |features| n-gram count matrix and list of n-grams in the order represented, given that the selected features appear in a least minOccur projects and at least once in every category. If counts = True, then the return matrix has counts features, if counts=False, then the return matrix has binary indicators'''
    #dict mapping from category -> set of n grams in that category
    catGramDict = defaultdict(set)
    #gram -> category -> count of that gram in that category
    gramCatCounter = defaultdict(lambda: Counter())
    #counter mapping from n-gram -> count
    nGramCounter = Counter()

    #maps from category -> numProjects in that category
    catCounter = Counter()

    myGramFun = lambda x,y: getNGrams(x, y, toLower = True, removePunct = True)

    #map from {project -> {gram -> count}}
    docCounter = defaultdict(Counter)

    for n in range(1,nGram+1):
        print "Extracting " + str(n) + "-grams"
        for p in projects:
            nGrams = myGramFun(p.text, n)
            for r in p.rewards:
                nGrams.extend(myGramFun(r.text,n))
            for f in p.faqs:
                nGrams.extend(myGramFun(f.question,n))
                nGrams.extend(myGramFun(f.answer,n))
            for g in nGrams:
                nGramCounter[g] += 1
                gramCatCounter[p.category][g] += 1
                docCounter[p][g] += 1
            catGramDict[p.category].update(set(nGrams))
            catCounter[p.category] += 1
    
    validGrams = [x for x in set.intersection(*catGramDict.values()) if nGramCounter[x] >= minOccur]

    print "Found {} n-grams".format(len(validGrams))

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

    
    print "Using {} n-grams".format(len(validGrams))

    returnMatrix = np.zeros([len(projects),len(validGrams)], dtype = np.float32)
    for i in range(len(projects)):
        if i is not 0 and i % 100 == 0: print i
        curProject = projects[i]
        for j in range(len(validGrams)):
            if counts:
                returnMatrix[i,j] += docCounter[curProject][validGrams[j]]
            else:
                returnMatrix[i,j] = 1 if docCounter[curProject][validGrams[j]] != 0 else 0
    return returnMatrix, validGrams


def extractGivenTextFeatures(projects, inFile, counts=False):
    '''Given an input of text features in the form of the kickstarter paper, return the feature matrix and valid n-grams.'''

    ngrams = getGramsFromFile(inFile)
    myNGrams = [g[0] for g in ngrams]
    print "Using {} n-grams".format(len(myNGrams))
    #dictionary mapping from ngram -> index
    nGramMap = {}
    for i in range(len(myNGrams)): nGramMap[myNGrams[i]] = i

    returnMatrix = np.zeros([len(projects),len(myNGrams)], dtype = np.float32)

    catGramDict = defaultdict(set)

    myGramFun = lambda x,y: getNGrams(x, y, toLower = True, removePunct = True)

    #map from {project -> {gram -> count}}
    docCounter = defaultdict(Counter)

    for n in range(1,4):
        print "Extracting " + str(n) + "-grams"
        for i in range(len(projects)):
            if i != 0 and i % 1000 == 0: print i
            curProject = projects[i]
            nGrams = myGramFun(curProject.text, n)
            for r in curProject.rewards:
                nGrams.extend(myGramFun(r.text,n))
            nGramCounter = Counter(nGrams)
            for k,v in nGramCounter.iteritems():
                if k in myNGrams:
                    if counts:
                        returnMatrix[i,nGramMap[k]] = v
                    else:
                        returnMatrix[i,nGramMap[k]] = 1
    return returnMatrix, myNGrams


def getNGrams(stringIn, n, toLower = True, removePunct = False):
    '''Given an input string, an "n" in n-gram, whether or not we should lowercase, whether or not we should remove punct, and a list of stopwords (None of remove none), return a list of strings representing those n-grams. Might contain repeats.'''
    if toLower: stringIn = stringIn.lower()
    exclude = set(string.punctuation)
    if removePunct: stringIn = ''.join(ch for ch in stringIn if ch not in exclude)
    tokens = stringIn.split()
    
    returnList = []
    for i in range(len(tokens)-n+1): returnList.append(' '.join(tokens[i:i+n]))
    return returnList

def crossValidate(dataMatrix, target, k=5):
    '''Returns the average cross validation error given k groups'''
    (numEx, numFeatures) = dataMatrix.shape

    print dataMatrix.shape

    def chunks(l, n):
        if n < 1:
            n = 1
        return [l[i:i + n] for i in range(0, len(l), n)]
        
    myChunks = chunks(range(numEx), numEx/k)

    aveAcc = 0
    for i in range(k):
        testingData = dataMatrix[myChunks[i],:]
        testingTarget = target[myChunks[i]]

        trainingIndices = []
        for j in range(k):
            if j == i: continue
            trainingIndices.extend(myChunks[j])

        trainingData = dataMatrix[trainingIndices,:]
        trainingTarget = target[trainingIndices]
        print trainingData.shape
        print testingData.shape

        print "Training Regression {} of {}...".format(i+1, k)
        myModel = penLogisticRegression(trainingData, trainingTarget)
        acc = myModel.score(testingData, testingTarget)
        print "Acc = {}".format(acc)
        aveAcc += acc

    return aveAcc/k

def getEntropy(text, unigrams):
    '''Given a text document and a list of unigrams of interest, returns the entropy of the
    distribution of the unigrams.'''
    uniGrams = getNGrams(text, 1, toLower = True, removePunct = True)
    uniDist = Counter(uniGrams)
    docLen = len(uniGrams)
    entropy = 0
    for u in unigrams:
        if uniDist[u] == 0: continue
        p = (uniDist[u] * 1.)/docLen
        entropy += -p*np.log2(p)
    return entropy

def getTextControlFeatures(projects):
    '''Given a list of projects, return a matrix of text control features.'''
    features = ['length', 'entropy100', 'entropy1000', 'tokenToType']
    returnMatrix = np.zeros([len(projects),len(features)], dtype = np.float32)

    computeEntropy = False
    for f in features:
        if 'entropy' in f:
            computeEntropy = True
    
    if computeEntropy == True:
        unigramCounter = Counter()
        for p in projects:
            unigramCounter.update(getNGrams(p.text, 1, toLower = True, removePunct = True))
        topThousand = [x[0] for x
                       in sorted(unigramCounter.items(), key=operator.itemgetter(1))[:1000:-1]]
    for i in range(len(features)):
        curFeature = features[i]
        for j in range(len(projects)):
            if curFeature == 'length':
                returnMatrix[j,i] = len(getNGrams(projects[j].text,
                                                  1, toLower = True, removePunct = True))
            elif curFeature == 'entropy100':
                returnMatrix[j,i] = getEntropy(projects[j].text, topThousand[:100])
            elif curFeature == 'entropy1000':
                returnMatrix[j,i] = getEntropy(projects[j].text, topThousand)
            elif curFeature == 'tokenToType':
                unigrams = getNGrams(projects[j].text,
                                     1, toLower = True, removePunct = True)
                if len(unigrams) == 0: returnMatrix[j,i] = 0
                else: returnMatrix[j,i] = (len(set(unigrams)) * 1.)/len(unigrams)
            else:
                print curFeature + " is not implemented"

    return returnMatrix, features

def saveFeatureMatrixAndHeaders(projects, matrixOut, headersOut,
                                control = False, given = None, counts = True):
    '''Given a list of projects, filenames for the output matrix/target/header data, and whether or not you just want the control matrix, outputs the requested data to the requested files.'''
    if not control:
        if given is None:
            featureMatrix1, ngrams = extractTextFeatures(projects, counts=counts, minOccur = 10)
        else:
            featureMatrix1, ngrams = extractGivenTextFeatures(projects, given, counts=counts)
    featureMatrix2, cats = getCategoryControlFeatures(projects)
    featureMatrix3, controls = getExtraControlFeatures(projects)
    featureMatrix4, langControls = getTextControlFeatures(projects)

    numBackers = np.zeros([len(projects), 1], dtype=np.int)
    numAltruistic = np.zeros([len(projects), 1], dtype=np.int)
    numBackers[:,0] = np.array([p.backers for p in projects])
    numAltruistic[:,0] = np.array([(p.backers - sum([y.numBackers for y in p.rewards]))
                                   for p in projects])

    if not control: ngrams = ['T' + g for g in ngrams]
    cats = ['C' + c for c in cats]
    controls = ['O' + o for o in controls]
    langControls = ['L' + l for l in langControls]
    targets = ["numBackers, numAltruistic"]

    if not control:
        data = np.concatenate([featureMatrix1,
                               featureMatrix2,
                               featureMatrix3,
                               featureMatrix4,
                               numBackers, 
                               numAltruistic],axis = 1)
    else:
        data = np.concatenate([featureMatrix2,
                               featureMatrix3,
                               featureMatrix4,
                               numBackers, numAltruistic] ,axis = 1)

    if not control:
        headers = np.concatenate([ngrams,
                                  cats,
                                  controls,
                                  langControls,
                                  targets])
    else:
        headers = np.concatenate([cats,
                                  controls, langControls, targets])

    sparseMatrix = csr_matrix(data)
    mmwrite(matrixOut, sparseMatrix)
    with open(headersOut, 'w') as f:
        f.write(",".join(headers) + "\n") 

def getGramsFromFile(filename):
    '''Given a filename of a file that stores n-gram weight information, return a list of tuples corresponding to the (gram, weight) pairs described by that file'''
    returnList = []
    myFile = open(filename)
    for line in myFile.read().split("\r"):
        myMatch = re.match("(.+)\t(.+)", line)
        returnList.append((myMatch.groups()[0], myMatch.groups()[1]))

    return returnList

def compareMineToTheirs(projects):
    grams = getGramsFromFile("KS.predicts")
    #featureMatrix1, ngrams = extractTextFeatures(projects)
    
    myGrams = set(getValidGrams(projects))
    theirGrams = set([g[0] for g in grams])
    
    print "I use " + str(len(myGrams)) + " ngrams"
    print "They use " + str(len(theirGrams)) + " ngrams"


    print "They use " + str(len(theirGrams - myGrams)) + " unique n-grams when compared to me."
    print "I use " + str(len(myGrams - theirGrams)) + " unique n-grams when compared to them."
    
    print "~~~~~~ They use that I don't ~~~~~~"
    for g in list(theirGrams - myGrams)[:20]:
        print g
    
    print "~~~~~~ I use that they don't ~~~~~~"
    for g in list(myGrams - theirGrams)[:20]:
        print g

def main():
    projects = loadProjects('output')
    projects = [p for p in projects if len(p.category) != 0]
    #minDate = min([p.startDate for p in projects])
    #maxDate = max([p.endDate for p in projects])
    
    #train = 400
    #test = 600
    #catDict = buildCategoryDictionary(projects)
    #music = catDict["Photography"]
    #succ = [p for p in music if p.backers != 0
    #        and
    #        1.*(p.backers - sum([y.numBackers for y in 
    #                             p.rewards]))/(1.0*p.backers)>.1 if len(p.text) > 0]
    #fail = [p for p in music if p.backers == 0
    #        or
    #        1.*(p.backers - sum([y.numBackers for y in 
    #                             p.rewards]))/(1.0*p.backers)<=.1 if len(p.text) > 0]
    #print len(succ)
    #print len(fail)
    #pickle.dump([x.text for x in succ[:train]], open("succTrainPhoto.pickle", 'w'), -1)
    #pickle.dump([x.text for x in fail[:train]], open("failTrainPhoto.pickle", 'w'), -1)
    #pickle.dump([x.text for x in succ[train:test]], open("succTestPhoto.pickle", 'w'), -1)
    #pickle.dump([x.text for x in fail[train:test]], open("failTestPhoto.pickle", 'w'), -1)
    #projects = [p for p in succ[:train]]
    #projects.extend([p for p in fail[:train]])
    #projects.extend([p for p in succ[train:test]])
    #projects.extend([p for p in fail[train:test]])
    

    #cats = set([p.category for p in projects])
    #print cats
    #print minDate
    #print maxDate

    #categoryAltruisticPropTest(projects)
    #basicStats(projects)
    #texts = [p.text for p in projects]
    #extractTextFeatures(projects, minOccur = 50, nGram = 3)
    #with open("KSText.pickle", 'w') as f: pickle.dump(texts, f, -1)
    #basicStats(projects)
    #compareMineToTheirs(projects)
    #saveFeatureMatrixAndHeaders(projects, "dataBinaryTheirs.mtx",
    #                            "target.csv", "headersTheirs.csv", given="KS.predicts",
    #                            counts=False)
    saveFeatureMatrixAndHeaders(projects, "allControl.mtx", "allControl.csv", counts=False,
                                control = True)
    #saveFeatureMatrixAndHeaders(projects, "musicSmall.mtx", "musicSmall.csv", counts=False)
    #saveFeatureMatrixAndHeaders(projects, "photoSmall.mtx", "photoSmall.csv", counts=False)

    #target = np.zeros([len(projects), 1], dtype=np.int)
    
    #target = np.array([0 if p.backers == 0
    #                   else
    #                   1.*(p.backers - sum([y.numBackers for y in p.rewards]))/(1.0*p.backers)>.1
    #                   for p in projects])
    
    #target = np.zeros([len(projects), 1], dtype=np.int)
    #np.savetxt("altBinaryTarget.csv", target)
    
if __name__ == '__main__':
    main()
