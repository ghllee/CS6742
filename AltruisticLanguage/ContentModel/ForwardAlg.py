import numpy as np
import sys
import os
from LanguageModel import *
import cPickle as pickle
from collections import defaultdict
from loadbar import LoadBar

def emissionProb(initProb, transProb, observation, lms):
    '''Log-scale forward algorithm from
    http://bozeman.genome.washington.edu/compbio/mbt599_2006/hmm_scaling_revised.pdf
    Assumption: everything already comes in logscale.
    initProb: {state -> initProb}
    transProb: {(state1, state2) -> transProb}
    observation: [sentence1, sentence2, ...]
    lms: {state -> language model (with logProb function)}'''
    def elnsum(elnx,elny):
        if elnx == "LZ" or elny == "LZ":
            if elnx == "LZ":
                return elny
            else:
                return elnx
        else:
            if elnx > elny:
                return elnx + np.log(1 + np.exp(elny-elnx))
            else:
                return elny + np.log(1 + np.exp(elnx-elny))
    def elnprod(elnx, elny):
        if elnx == "LZ" or elny == "LZ":
            return "LZ"
        else:
            return elnx + elny

    states = lms.keys()
    M = np.zeros((len(lms), len(observation)))
    for i in range(len(states)):
        curState = states[i]
        M[i,0] = elnprod(initProb[states[i]], lms[curState].logProb(observation[0]))
    for i in range(1, len(observation)):
        for j in range(len(states)):
            curObs = observation[i]
            curState = states[j]
            logalpha = "LZ"
            for k in range(len(states)):
                logalpha = elnsum(logalpha, elnprod(M[k, i-1], transProb[(states[k],curState)]))
            M[j,i] = elnprod(logalpha, lms[states[j]].logProb(curObs))

    finalAns = "LZ"
    for i in range(len(states)):
        finalAns = elnsum(finalAns, M[i, len(observation)-1])
    return finalAns

def loadContentClusters(folder):
    '''Given a folder, returns a dictionary mapping {cluster -> model} for the content
    clusters.'''
    returnDict = {}
    for i in os.listdir(folder):
        if i.endswith(".lm"):
            with open(folder + "/" + i) as f:
                returnDict[int(i.split(".")[0])] = pickle.load(f)
        else:
            continue
    return returnDict

def getEtc(inFolder):
    '''Given the in folder, returns an etc model corresponding to the etc model in that directory.'''
    etcModel = ETCBigramModel()
    with open(inFolder + "/etcMatrix.npy") as f:
        etcModel.oneMinusMaxPsiMatrix = np.load(inFolder + "/etcMatrix.npy")
    with open(inFolder + "/etcWordToIndex.pickle") as f:
        etcModel.wordToIndex = pickle.load(f)
    return etcModel

def getStartProbs(inFolder, states, smooth = 1):
    '''Given a paths file, return a dictionary {states -> logged init prob}'''
    countDict = {}
    stateStrings = [str(s) for s in states]
    with open(inFolder + "/clustersOut.txt") as f:
        for line in f:
            if line.strip().split()[0] in stateStrings and len(line.strip().split()) == 2:
                countDict[int(line.strip().split()[0])] = int(line.strip().split()[1])
    totalSent = sum(countDict.values())
    returnDict = {}
    for s in states:
        returnDict[s] = np.log(((countDict[s] + smooth)*1.0)/(totalSent + len(states) * smooth))
    return returnDict

def main():
    if len(sys.argv) != 4:
        print "Wrong number of arguments -- inFolder, cleanTest, outFile"
        quit()
    inFolder, cleanTest, outFile = sys.argv[1:4]
    lms = loadContentClusters(inFolder)
    lms[-1] = getEtc(inFolder)
    with open(inFolder + "/transProbs") as f:
        transProb = pickle.load(f)
    startProb = getStartProbs(inFolder, lms.keys())
    #{doc -> [s1, s2, s3...]}
    docSents = defaultdict(list)
    with open(cleanTest) as f:
        sents = pickle.load(f)
    for s in sents:
        docSents[int(s[1])].append(s[0])
    
    print "Finding emission probabilities..."
    bar = LoadBar(30)
    bar.setup()
    probs = []
    docCount = 0
    for doc, curSents in docSents.iteritems():
        if bar.test(docCount, len(docSents)): bar += 1
        numTokens = sum([len(s.split()) for s in curSents])
        probs.append(emissionProb(startProb, transProb, curSents, lms) / numTokens)
        docCount += 1
    bar.clear()
    with open(outFile,'w') as f:
        f.write(','.join([str(p) for p in probs]) + "\n")
if __name__ == "__main__":
    main()
