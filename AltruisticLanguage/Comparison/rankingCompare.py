from scipy.stats import spearmanr as spr
import matplotlib.pyplot as plt

file1 = "GFMvKSSW.result"
file2 = "KSvAMASW.result"

ngramToID = {}

rank1 = []
rank2 = []

with open(file1) as f:
    curId = 0
    for line in f:
        if len(line) == 0: continue
        tokens = line.split()
        nGram = ' '.join(tokens[:-1])
        if len(tokens) != 2: continue
        ngramToID[nGram] = curId
        rank1.append(curId)
        curId += 1

idToNgram = {i:n for n,i in ngramToID.iteritems()}

with open(file2) as f:
    for line in f:
        if len(line) == 0: continue
        tokens = line.split()
        if len(tokens) != 2: continue
        nGram = ' '.join(tokens[:-1])
        rank2.append(ngramToID[nGram])



for nGram, ID in ngramToID.iteritems():
    pass


print len(rank1)
print len(rank2)
print spr(rank1, rank2)
