import cPickle as pickle
from KickstarterParser import *
import string
import re

def main():
    '''Pickles a list of 3000 strings, each corresponding to a kickstarter project description. Also does some pre-processing.'''
    numFiles = 3
    pickleNames = ["output/" + str(i+1) + ".pickle" for i in range(numFiles)]
    finalList = []
    for name in pickleNames:
        curProjectList = pickle.load(open(name, "rb"))
        for p in curProjectList:
            finalList.append(cleanDescription(p.text, mapNumbers = True, removeURLs = True))

    myOut = open('3000.pickle', 'w')
    pickle.dump(finalList, myOut, -1)
    myOut.close()

def cleanDescription(descIn, mapNumbers = False, removeURLs = False):
    '''Given a description, '''

    if removeURLs:
        urlRE = ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))'
        descIn = re.sub(urlRE, '', descIn)

    exclude = set(string.punctuation)
    desc = ''.join(ch for ch in descIn if ch not in exclude).lower()
    desc = ' '.join(desc.split())

    if mapNumbers:
        inTokens = desc.split(' ')
        tokens = []
        for t in inTokens:
            try:
                float(t)
                tokens.append("####")
            except ValueError:
                tokens.append(t)
        desc = ' '.join(tokens)
    return desc

if __name__ == "__main__":
    main()
