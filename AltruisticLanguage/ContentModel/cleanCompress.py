import sys
import cPickle as pickle

def main():
    toCombine = sys.argv[1:-1]
    out = sys.argv[-1]
    sents = []
    for c in toCombine:
        with open(c) as f:
            sents.append(pickle.load(f))
    curId = sents[0][1]
    writeId = 0
    finalSents = []
    for s in sents:
        for i in s:
            newId = i[1]
            if newId != curId:
                writeId += 1
                curId = newId
            finalSents.append((i[0], writeId))
    with open(out, 'w') as f:
        pickle.dump(finalSents, f, -1)
        
if __name__ == "__main__":
    main()
