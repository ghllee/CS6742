import re
from collections import defaultdict, Counter
import operator
import matplotlib.pyplot as plt


def interpretClusters(clusterFileName):
    #dict from {clusterNum -> [sentence1, sentence2]}
    clusterMap = defaultdict(list)
    with open(clusterFileName) as f:
        curCluster = None
        for line in f:
            if line.strip() == "***":
                continue
            elif re.search("\d", line) is not None:
                curCluster = int(line.split()[0])
            else:
                clusterMap[curCluster].append(line.strip())

    #for cluster, sents in clusterMap.iteritems():
    #    print cluster, len(sents)
    
    for cluster, sents in clusterMap.iteritems():
        if cluster == -1: continue
        counts = Counter()
        for s in sents:
            counts.update(set(getNGrams(s,n=4)))
        topTen = sorted(counts.iteritems(), key=operator.itemgetter(1))[::-1][:20]
        #print cluster
        string = str(len(sents)) + ' & \specialcell{'
        for i in range(5):
            string += '`' + topTen[i][0].replace('numnumnumnum', '\#') + '\'\\\\'
        string = string[:-2]
        string += '}\\\\\\hline'
        print string

def interpretPaths(pathsFile):
    docSents = defaultdict(list)
    with open(pathsFile) as f:
        curDoc = 0
        for line in f:
            tokens = line.strip().split(")(")
            tokens[0] = tokens[0][1:]
            tokens[-1] = tokens[-1][:-1]
            for t in tokens:
                tokens2 = t.split(',')
                docSents[curDoc].append((tokens2[0][1:-1], int(tokens2[1])))
            curDoc += 1
    lengths = Counter()
    for doc, sents in docSents.iteritems():
        lengths[len(sents)] += 1
    popLen, num = max(lengths.iteritems(), key=operator.itemgetter(1))
    print "The most popular length was " + str(popLen) + " with " + str(num) + " sentences"

    clusterCounts = Counter()
    seqDict = defaultdict(list)
    clusterPosDict = defaultdict(list)
    for doc, sents in docSents.iteritems():
        seqDict[len(sents)].append([s[1] for s in sents])
        for i in range(len(sents)):
            clusterPosDict[s[1]].append(1.*i/len(sents))
            clusterCounts[s[1]] += 1
    stateSet = set()
    for length, sequences in seqDict.iteritems():
        for s in sequences: stateSet.update(set(s))
    
    clusterAveragePosDict = {}
    for cluster, posList in clusterPosDict.iteritems():
        clusterAveragePosDict[cluster] = sum(posList)/len(posList)

    ordering = [x[0] for x in
                sorted(clusterAveragePosDict.iteritems(), key = operator.itemgetter(1))]

    ordering.remove(-1)
    #heightMap = {ordering[i]:i for i in range(len(ordering))}
    #heightMap[-1] = -1

    #assign a height for each state
    #heightMap = defaultdict(int)
    #curHeight = 0
    #for s in stateSet:
    #    print s
    #    if s == -1:
    #        heightMap[s] = -1
    #    else:
    #        heightMap[s] = curHeight
    #        curHeight += 1

    namesAndOrder = getClusterNamesOrdering()
    heightMap = {cluster:val[1] for cluster,val in namesAndOrder.iteritems()}
    
    def maxPropDiffFromBackground(lst, clusterCounts): 
        sampleCounts = Counter(lst)
        
        totalSents = sum(clusterCounts.values())
        totalSample = len(lst)
        
        maxDiff = -10
        maxCluster = -10
        for cluster, clusterCount in clusterCounts.iteritems():
            sampleProp = sampleCounts[cluster]*1.0/totalSample
            allProp = clusterCount*1.0/totalSents

            if sampleProp - allProp > maxDiff:
                maxDiff = sampleProp - allProp
                maxCluster = cluster
        return maxCluster

    for length, seqs in seqDict.iteritems():
        if length == 1: continue
        if len(seqs) < 10: continue
        statesAtStep = defaultdict(list)
        for i in range(length):
            for s in seqs:
                statesAtStep[i].append(s[i])
        
        print [namesAndOrder[maxPropDiffFromBackground(statesAtStep[i], clusterCounts)][0]
               for i in range(length)]

        #for seq in seqs:
        #    plt.plot([heightMap[s] for s in seq])
        #plt.savefig(str(length) + ".png")
        #plt.figure()
    
def getNGrams(stringIn, n=2):
    tokens = stringIn.split()
    returnList = []
    for i in range(len(tokens)-n+1): returnList.append(' '.join(tokens[i:i+n]))
    return returnList

def main():
#    interpretClusters("clustersOut.txt")
    interpretPaths("docPathsOut.txt")

if __name__ == "__main__":
    main()
