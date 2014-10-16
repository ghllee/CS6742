# File contains the kickstarter project class and related methods/classes
from datetime import datetime
from dateutil.parser import parse
from bs4 import BeautifulSoup
import bs4
import cPickle as pickle
import time
import os
import re

class Project:
    def __init__(self):
        self.projectId = -1
        self.name = ""
        self.url = ""
        self.backers = -1
        self.parentCategory = ""
        self.category = ""
        self.duration = -1.
        self.startDate = datetime(1900, 1, 1, 1, 1, 1, 1)
        self.endDate = datetime(1900, 1, 1, 1, 1, 1, 1)
        self.goal = -1.
        self.raised = -1.
        self.lat = -1.
        self.lon = -1.
        self.shortText = ""
        self.text = ""
        self.comments = -1
        #0 is not funded, 1 is funded
        self.result = -1
        self.rewards = []
        self.faqs = []

    def __str__(self):
        retStr = ""
        retStr += self.name + "\n"
        retStr += "Id = " + str(self.projectId) + "\n"
        retStr += "url = " + self.url + "\n"
        retStr += str(self.backers) + " backers" + "\n"
        retStr += "cat = " + self.category + "\n"
        retStr += "parentCat = " + self.parentCategory + "\n"
        retStr += "duration = " + str(self.duration) + "\n"
        retStr += "end date = " + str(self.endDate) + "\n"
        retStr += "start date = " + str(self.startDate) + "\n"
        retStr += "goal = " + str(self.goal) + "\n"
        retStr += "raised = " + str(self.raised) + "\n"
        retStr += "lat = " + str(self.lat) + "\n"
        retStr += "lon = " + str(self.lon) + "\n"
        retStr += "comments = " + str(self.comments) + "\n"
        retStr += "finished = " + str(self.result) + "\n"
        for r in self.rewards:
            retStr += str(r) + "\n"
        for f in self.faqs:
            retStr += str(f) + "\n"
        retStr += self.shortText + "\n"
        retStr += self.text
        return retStr

class FAQ:
    def __init__(self):
        self.project = None
        self.question = ""
        self.answer = ""
        self.editDate = datetime(1900, 1, 1, 1, 1, 1, 1)

    def __str__(self):
        retStr = self.question + '\n'
        retStr += self.answer + '\n'
        retStr += str(self.editDate)
        return retStr

class Reward:
    def __init__(self):
        self.project = None
        self.cost = -1.
        self.currency = ""
        self.numBackers = -1
        self.text = ""
        #goes from 0 = pure pre-order to 10 = pure altruism
        self.altruismRating = -1.
        #goes from 0 = cheap altruism, 1 = mostly pre-order, 2 = expensive altruism
        self.altruismClassification = -1
        #if the reward is "limited" then this will be a tuple of (claimed, total)
        self.limited = None

    def __str__(self):
        returnString = self.text + "\n" 
        returnString += str(self.cost) + " " + str(self.currency) + "\n"
        returnString += "Backers: " + str(self.numBackers)
        return returnString


def getRewardList(soup, project):
    '''Given an input soup object and a parent object, return the reward list associated
    with that project/soup'''
    rewards = []

    for li in soup.find_all('li'):
        for div in li.find_all('div'):
            if div.get('class') is not None and 'NS-projects-reward' in div.get('class'):
                curReward = Reward()
                curReward.project = project
                for h3 in li.find_all('h3'):
                    match = re.match("Pledge (.)(\d+)", h3.text)
                    if match is None: continue
                    curReward.currency = match.groups()[0].encode('ascii', 'ignore')
                    curReward.cost = int(match.groups()[1])
                for span in div.find_all('span'):
                    if span.get('class') is not None:
                        if 'num-backers' in span.get('class'):
                            match = re.match("(\d+) Backer(|s)", span.text.strip())
                            curReward.numBackers = int(match.groups()[0])
                        if 'limited-number' in span.get('class'):
                            match = re.search("(\d+) of (\d+)", span.text.strip())
                            curReward.limited = (int(match.groups()[0]), int(match.groups()[1]))
                        else:
                            pass
                for div2 in div.find_all('div'):
                    if div2.get('class') is not None:
                        if 'desc' in div2.get('class'):
                            curReward.text = basicSanitize(div2.text.strip())
                rewards.append(curReward)
    return rewards

def basicSanitize(inString):
    '''Returns a very roughly sanitized version of the input string.'''
    return ' '.join(inString.encode('ascii', 'ignore').strip().split())

def getFaqList(soup, project):
    '''Given an input soup object and a parent object, return the faq list associated
    with that project/soup'''
    
    questions = []
    answers = []
    dates = []

    for div in soup.find_all('div'):
        if div.get('class') is not None and 'faq-question' in div.get('class'):
            questions.append(basicSanitize(div.text))

    for div in soup.find_all('div'):
        if div.get('class') is not None and 'faq-answer' in div.get('class'):
            matchObj = re.match('^(.*)Last updated: (.*)$', basicSanitize(div.text))
            if matchObj is None: #weird kickstarter html errors, may lose a few faqs
                continue
            if len(matchObj.groups()) == 1:
                answers.append("")
                dates.append(parse(matchObj.groups()[1]))
                continue
            
            answers.append(basicSanitize(matchObj.groups()[0]))
            
            for validYear in range(2008, 2015):
                try:
                    dateStr = str(validYear) + " " + matchObj.groups()[1]
                    tryDate = parse(dateStr).replace(tzinfo=None)
                    if tryDate < project.startDate:
                        continue
                    else:
                        date = tryDate
                        break
                except ValueError:#for leap year issues...
                    continue

            dates.append(date)

    if not len(questions) == len(answers) == len(dates):
        print "FAQ parsing problem"
        return []

    returnFaqs = []
    for i in range(len(questions)):
        newFaq = FAQ()
        newFaq.project = project
        newFaq.question = questions[i]
        newFaq.answer = answers[i]
        newFaq.editDate = dates[i]
        returnFaqs.append(newFaq)
    
    return returnFaqs

def fillProjectInfo(soup, project):
    '''Given a input soup object and the current project, fills in the non reward/faq info of that project.''' 
    
    for meta in soup.find_all('meta'):
        if meta.get('property') is not None:
            if 'url' in meta.get('property'):
                project.url = meta.get('content')
            if 'latitude' in meta.get('property'):
                project.lat = float(meta.get('content'))
            if 'longitude' in meta.get('property'):
                project.lon = float(meta.get('content'))
            if 'title' in meta.get('property'):
                project.name = basicSanitize(meta.get('content'))
            if 'og:description' in meta.get('property'):
                project.shortText = basicSanitize(meta.get('content'))
            else:
                pass

    for div in soup.find_all('div'):
        if div.get('data-backers-count') is not None:
            project.backers = int(div.get('data-backers-count'))
        if div.get('data-goal') is not None:
            project.goal = float(div.get('data-goal'))
        if div.get('data-pledged') is not None:
            project.raised = float(div.get('data-pledged'))
        if div.get('class') is not None and 'full-description' in div.get('class'):
            myText = ' '.join(div.findAll(text=True))
            project.text = basicSanitize(myText)

    for span in soup.find_all('span'):
        if span.get('data-duration') is not None:
            project.duration = float(span.get('data-duration'))
        if span.get('data-comments-count') is not None:
            project.comments = int(span.get('data-comments-count'))
        if span.get('data-end_time') is not None:
            project.endDate = parse(span.get('data-end_time')).replace(tzinfo=None)

    for li in soup.find_all('li'):
        if li.get('data-project-parent-category') is not None:
            project.parentCategory = basicSanitize(li.get('data-project-parent-category'))
            for a in li.find_all('a'):
                project.category = basicSanitize(a.text)
        if li.get('class') is not None and 'posted' in li.get('class'):
            searchObj = re.search('([A-Za-z]{3}. \d+, \d+)', basicSanitize(li.text))
            project.startDate = parse(searchObj.groups()[0]).replace(tzinfo=None)

    project.result = 0 if project.goal > project.raised else 1
    project.faqs = getFaqList(soup, project)
    project.rewards = getRewardList(soup, project)


def makeDatabase(htmlFolderName, outputPickleFolder, perFile = 1000):
    '''Given a database file input, returns a list of project objects and pickles the output'''
    projects = []
        
    fileCounter = 1
    
    validFiles = [x for x in os.listdir(htmlFolderName) if re.search("^\d+\.html$", x) is not None]
    print "Parsing " + str(len(validFiles)) + " files"
    for myFile in sorted(validFiles, key = lambda x: int(x.split('.')[0])):
        newProject = Project()
        newProject.projectId = int(myFile.split(".")[0])
        curFile = open(htmlFolderName + "/" + myFile)
        curText = curFile.read()
        curSoup = BeautifulSoup(curText)
        curFile.close()
        fillProjectInfo(curSoup, newProject)
        projects.append(newProject)
        curId = newProject.projectId
        if len(projects) == perFile:
            outputPickleFile = outputPickleFolder + '/' + str(fileCounter) + '.pickle'
            myOut = open(outputPickleFile, 'w')
            pickle.dump(projects, myOut, -1)
            myOut.close()
            projects = []
            fileCounter += 1

        fileNum = newProject.projectId
        if fileNum != 0 and fileNum % 100 == 0: print fileNum

        

    myOut = open(outputPickleFolder + '/' + str(fileCounter) + '.pickle', 'w')
    pickle.dump(projects, myOut, -1)
    myOut.close()
    
def main():
    makeDatabase("kickstarter", "output")

if __name__ == "__main__":
    main()
