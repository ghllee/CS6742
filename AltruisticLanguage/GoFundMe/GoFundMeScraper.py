import urllib2
from bs4 import BeautifulSoup
import os
catToURL = {"Medical":"/Medical-Illness-Healing/",
            "Volunteer":"/Volunteer-Service/",
            "Emergencies":"/Accidents-Personal-Crisis/",
            "Education":"/Education-Schools-Learning/",
            "Memorials":"/Funerals-Memorials-Tributes/",
            "Sports":"/Sports-Teams-Clubs/",
            "Animals":"/Animals-Pets/",
            "Business":"/Business-Entrepreneurs/",
            "Charity":"/Non-Profits-Charities/",
            "Community":"/Community-Neighbors/",
            "Competitions":"/Competitions-Pageants/",
            "Creative":"/Creative-Arts-Music-Film/",
            "Events":"/Celebrations-Special-Events/",
            "Faith":"/Missions-Faith-Church/",
            "Family":"/Babies-Kids-Family/",
            "National News":"/National-News/",
            "Newlyweds":"/Weddings-Honeymoons/",
            "Other":"/Other-Miscellaneous/",
            "Travel":"/Travel-Adventure/",
            "Wishes":"/Dreams-Hopes-Wishes/"}

def getURLs(category, pageRange = range(1,51)):
    '''Given a category name for a GoFundMe project, returns the urls from PageRange'''
    baseURL = "http://www.gofundme.com" + catToURL[category] + "?page="

    urls = []
    for i in pageRange:
        url = baseURL + str(i)
        usock = urllib2.urlopen(url)
        curSoup = BeautifulSoup(usock.read())
        usock.close()
        for a in curSoup.find_all('a'):
            if a.get('class') is not None and 'pho' in a.get('class'):
                urls.append(a.get('href'))
    return urls

def main():
    baseDir = "GoFundMe"
    for catName in [x for x in catToURL.keys() if x not in ['Business','Community','Competitions',
                                                            'Creative','Faith','Family','Medical',
                                                            'Memorials','Newlyweds','Sports']]:
        print "Scraping " + catName
        catUrls = getURLs(catName)
        print str(len(catUrls)) + " projects found"
        curDir = baseDir + '/' + catName + '/'
        if not os.path.exists(curDir):
            os.makedirs(curDir)
        for i in range(len(catUrls)):
            if i != 0 and i % (len(catUrls)/10) == 0: print i
            curUrl = catUrls[i]
            usock = urllib2.urlopen(curUrl)
            htmlText = usock.read()
            with open(curDir + str(i) + '.html', 'w') as f:
                f.write(htmlText)
            
            

if __name__ == "__main__":
    main()
