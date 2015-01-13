import sys

myFile = open(sys.argv[1])
outFile = open(sys.argv[2], 'w')
prior = .01

for line in myFile:
    outFile.write(line.strip() + ":" + str(prior) + "\n")

myFile.close()
outFile.close()
