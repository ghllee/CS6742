import sys

def main():
    '''Command line argument should be [input file] [prior] [output file]'''
    with open(sys.argv[-1], 'w') as out:
        with open(sys.argv[1]) as fileIn:
            writeStr = ""
            for line in fileIn:
                writeStr += line.strip() + ":" + sys.argv[2] + "\n"
            out.write(writeStr[:-1])

if __name__ == "__main__":
    main()
