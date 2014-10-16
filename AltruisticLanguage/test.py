import random

myFile = open("kickscrape.sql")

for line in myFile:
    if random.random() < .00079:
        print line
