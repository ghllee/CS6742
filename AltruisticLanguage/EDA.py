import cPickle as pickle
from KickstarterParser import *
import random
import numpy as np
import matplotlib.pyplot as plt
import string
from collections import defaultdict
from scipy.stats import chi2_contingency

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

def loadProjects(folderName, fileRange = None):
    '''Given the name of the folder where the pickled project files are, return a list of the projects contained in those pickled files. Furthermore, if numFiles is not None, return the list containing data from only that number of files.'''
    validFiles = [x for x in os.listdir(folderName) if re.search("^\d+\.pickle$", x) is not None]
    if fileRange is not None: validFiles = validFiles[fileRange[0]:fileRange[1]]
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
        print cat, propSuc, propFail, p

        if propSuc > propFail: print "Greater proportion with successful projects"
        else: print "Greater proportion with failed projects"

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


def main():
    projects = loadProjects('output')
    categoryAltruisticMeanValueTest(projects)

if __name__ == '__main__':
    main()
