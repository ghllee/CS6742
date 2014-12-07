import cPickle as pickle
from KickstarterParser import *
from nltk.corpus import stopwords
import string
import re

def main():
    '''Pickles a list of 3000 strings, each corresponding to a kickstarter project description. Also does some pre-processing.'''
    numFiles = 46
    pickleNames = ["output/" + str(i+1) + ".pickle" for i in range(numFiles)]
    finalList = []
    for name in pickleNames:
        curProjectList = pickle.load(open(name, "rb"))
        for p in curProjectList:
            finalList.append(cleanDescription(p.text, mapNumbers = False,
                                              removeURLs = True,
                                              removeStops = True))
            

    myOut = open('KSProcessed.pickle', 'w')
    pickle.dump(finalList, myOut, -1)
    myOut.close()

def cleanDescription(descIn, mapNumbers = False,
                     removeURLs = False, removeStops = False):

    if removeURLs:
        urlRE = r"(?:\s|^)(\S*\.(?:com|org|net|be)\S*)(?:\s|$)"
        desc = ' '.join(re.sub(urlRE, ' ', descIn).split())
        #desc = ' '.join(x for x in descIn.split() if tokenTest(x))
        #def tokenTest(token):
        #    forbid = ["." + x for x in ["com", "net","be","org"]]
        #    for f in forbid:
        #        if f in token:
        #            print token
        #            return False
        #    return True
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

    if removeStops:
        stop = stopwords.words('english')
        desc = ' '.join([x for x in desc.split() if x not in stop])
    return desc

if __name__ == "__main__":
    main()
