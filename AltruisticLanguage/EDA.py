import cPickle as pickle
from KickstarterParser import *
import random

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

def main():
    projects = loadProjects('output', numFiles = 1)
    random.shuffle(projects)
    for p in projects:
        sortedRewards = sorted(p.rewards, key = lambda x: x.cost)
        print p.url
        print sortedRewards[0]
        quit()

if __name__ == '__main__':
    main()
