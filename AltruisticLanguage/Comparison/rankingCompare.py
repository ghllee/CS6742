import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as sp
from collections import Counter, defaultdict

file1 = "newNGrams/GFMvsKSSW.result"
file2 = "newNGrams/AMAvsKSSW.result"

rank1 = []
rank2 = []

ngrams = []

skip = 4

nGramCounter = Counter()
ngramToVal = {}
ngrams = []
orderedNGram = defaultdict(list)
with open(file1) as f:
    for line in f:
        if len(line) == 0: continue
        tokens = line.split()
        nGram = ' '.join(tokens[:-1])
        if skip is not None:
            if len(tokens) == skip: continue
        orderedNGram[len(tokens)].append((nGram, float(tokens[-1])))
        ngramToVal[nGram] = float(tokens[-1])
        ngrams.append(nGram)

orderedNGram = defaultdict(list)
ngramToVal2 = {}
with open(file2) as f:
    for line in f:
        if len(line) == 0: continue
        tokens = line.split()
        nGram = ' '.join(tokens[:-1])
        if skip is not None:
            if len(tokens) == skip: continue
        orderedNGram[len(tokens)].append((nGram, float(tokens[-1])))
        ngramToVal2[nGram] = float(tokens[-1])

print len(ngrams)

#for i in [2,3,4]:
#    print i
#    for x in orderedNGram[i][:5]:
#        print x
#    print
#    for x in orderedNGram[i][-5:]:
#        print x



rank1 = [ngramToVal[n] for n in ngrams]
rank2 = [ngramToVal2[n] for n in ngrams]

tau, p_value = sp.stats.kendalltau(rank1, rank2)
print tau, p_value
