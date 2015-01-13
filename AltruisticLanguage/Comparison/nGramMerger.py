import sys

def unionNGrams(files):
    '''Given a list of files, takes the union of the n grams contained in them'''
    returnSet = set()
    for fileName in files:
        curNGrams = []
        with open(fileName) as f:
            for line in f:
                if len(line) != 0:
                    curNGrams.append(line.strip())
        returnSet.update(set(curNGrams))
    return returnSet

def intersectNGrams(files):
    '''Given a list of files, takes the intersection of the n grams contained in them'''
    setList = []
    for fileName in files:
        curNGrams = []
        with open(fileName) as f:
            for line in f:
                if len(line) != 0:
                    curNGrams.append(line.strip())
        setList.append(set(curNGrams))
    return set.intersection(*setList)

def main():
    files = sys.argv[1:-1]
    nGrams = intersectNGrams(files)
    print "Writing " + str(len(nGrams)) + " to " + sys.argv[-1]
    with open(sys.argv[-1], 'w') as f:
        writeStr = ""
        for n in nGrams:
            writeStr += n + "\n"
        f.write(writeStr[:-1])

if __name__ == "__main__":
    main()
