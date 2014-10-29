import cPickle as pickle
from KickstarterParser import *
import random
import numpy as np
import matplotlib.pyplot as plt
import string

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

def main():
    projects = loadProjects('output', fileRange = (4,14))
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

if __name__ == '__main__':
    main()
