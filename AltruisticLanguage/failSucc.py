from KickstarterParser import *
from EDA import loadProjects
from collections import defaultdict, Counter
from scipy.stats import chi2_contingency
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind as ttest
import numpy as np

def categoryValueTest(projects):
    catDict = buildCategoryDictionary(projects)
    #subcatDict = buildSubCategoryDictionary(projects)
    #catDict = dict(catDict.items()) + subcatDict.items())
    for cat, projectList in catDict.iteritems():
        if len(cat) == 0: continue
        success = [x for x in projectList if x.result and x.backers >= 10]
        fail = [x for x in projectList if not x.result and x.backers >= 10]
        sucAltRatio = [1.-(1.0*sum([y.numBackers for y in x.rewards]))/x.backers for x in success]
        failAltRatio = [1.-(1.0*sum([y.numBackers for y in x.rewards]))/x.backers for x in fail]
        sucAltRatioVals = [1.-(1.0*sum([y.numBackers*y.cost for y in x.rewards]))/x.raised
                       for x in success]
        failAltRatioVals = [1.-(1.0*sum([y.numBackers*y.cost for y in x.rewards]))/x.raised
                       for x in fail]
        bins = [(x*1.)/100 for x in range(1,100)]
        plt.hist(sucAltRatio, bins, alpha=0.5,
                 color = 'g', label='Success, N=' + str(len(sucAltRatio)),
                 normed = True)
        plt.hist(failAltRatio, bins, alpha=0.5,
                 color = 'b', label='Failure, N='+str(len(failAltRatio)),
                 normed = True)
        plt.axvline(x=np.mean(sucAltRatio),linewidth=4, color='g', ls = '--')
        plt.axvline(x=np.mean(failAltRatio),linewidth=4, color='b', ls = '--')
        plt.legend(loc='upper right', fontsize=18)
        plt.title(cat, fontsize=18)
        plt.xlabel("Proportion Altruistic", fontsize=18)
        plt.axes().get_yaxis().set_visible(False)
        plt.savefig("catGraphs/" + cat + "events.png")
        plt.close()

        plt.hist(sucAltRatioVals, bins, alpha=0.5,
                 color = 'g', label='Success, N=' + str(len(sucAltRatio)),
                 normed = True)
        plt.hist(failAltRatioVals, bins, alpha=0.5,
                 color = 'b', label='Failure, N='+str(len(failAltRatio)),
                 normed = True)
        plt.axvline(x=np.mean(sucAltRatioVals),linewidth=4, color='g', ls = '--')
        plt.axvline(x=np.mean(failAltRatioVals),linewidth=4, color='b', ls = '--')
        plt.legend(loc='upper right', fontsize=18)
        plt.title(cat, fontsize=18)
        plt.xlabel("Proportion Altruistic", fontsize=18)
        plt.axes().get_yaxis().set_visible(False)
        plt.savefig("catGraphs/" + cat + "vals.png")
        plt.close()
        plt.figure()

        print "Events", cat, ttest(sucAltRatio, failAltRatio, equal_var=False)
        print "Vals", cat, ttest(sucAltRatioVals, failAltRatioVals, equal_var=False)
        print

def categoryAltruisticPropTest(projects):
    '''Given a list of projects, split on category. Then, conduct a proportion test for for each category for proportion of altruistic donations vs not altruistic donations split on success/failure.'''

    catDict = buildCategoryDictionary(projects)
    subcatDict = buildSubCategoryDictionary(projects)

    catDict = dict(catDict.items() + subcatDict.items())

    print '{:>18}  {:>18}  {:>18}  {:>18}'.format("Category",
                                                  "Alt Ratio Succ",
                                                  "Alt Ratio Fail",
                                                  "p-val")

    barVals = []
    barColors = []
    barLabels = []
    curIndex = 0
    barLefts = []
    for cat, projectList in catDict.iteritems():
        if len(cat) == 0: continue
        success = [x for x in projectList if x.result and x.backers != 0]
        fail = [x for x in projectList if not x.result and x.backers != 0]
        sucAlt = sum([x.backers - sum([y.numBackers for y in x.rewards]) for x in success])
        failAlt = sum([x.backers - sum([y.numBackers for y in x.rewards]) for x in fail])
        sucTotal = sum([x.backers for x in success])
        failTotal = sum([x.backers for x in fail])

        chi2, p, dof, ex = chi2_contingency([[sucAlt, failAlt],[sucTotal-sucAlt, failTotal-failAlt]])

        propSuc, propFail = float(sucAlt*1./sucTotal), float(failAlt*1./failTotal)
        
        barVals.append(propFail-propSuc)
        barColors.append('b' if p < .01 else 'r')
        barLabels.append(cat)
        barLefts.append(curIndex)
        curIndex += 1

        print '{:>18}  {:>18.4f}  {:>18.4f}  {:>18.4f}'.format(cat, propSuc, propFail, p)

        #if propSuc > propFail: print "Greater proportion with successful projects"
        #else: print "Greater proportion with failed projects"

    plt.bar(barLefts, barVals, align='center', color = barColors)
    plt.xticks([b+.5 for b in barLefts], barLabels, rotation=45, ha='right')
    figure = plt.gcf() # get current figure
    figure.set_size_inches(14, 4)
    plt.xlim([-1.1, len(barLefts)+.1])
    plt.ylim([min(barVals) - .002, max(barVals) + .002])
    plt.savefig("failSuccess.png", dpi = 100, bbox_inches='tight')


def buildCategoryDictionary(projects):
    '''Given a list of projects, builds a dictionary that maps from {category -> [p1, p2, p3]} for all projects in the input.'''
    x = defaultdict(list)
    for p in projects: x[p.category].append(p)
    return x

def buildSubCategoryDictionary(projects):
    '''Given a list of projects, builds a dictionary that maps from {sub -> [p1, p2, p3]} for all projects in the input with subcategories.'''
    x = defaultdict(list)
    for p in projects:
        if p.subCategory is not None:
            x[p.subCategory].append(p)
    return x

def printGroupStatistics(projects):
    cats = getCategories(projects)

    print '{:>18}  {:>18}  {:>18}  {:>18}'.format("Category",
                                                  "Num Projects",
                                                  "Succ Ratio",
                                                  "Ave Raised")
    for c in cats:
        if c is '': continue
        catProjects = getProjectsOfCategory(c, projects)
        succRatio = sum([1 for p in catProjects if p.result == 1])*1./len(catProjects)
        aveRaised = sum([p.raised for p in catProjects])*1./len(catProjects)
        print '{:>18}  {:>18}  {:>18}  {:>18}'.format(c,
                                                      len(catProjects),
                                                      succRatio,
                                                      aveRaised)

def getCategories(projects):
    return set([x.category for x in projects])

def getProjectsOfCategory(category, allProjects):
    returnList = []
    for p in allProjects:
        if p.category == category:
            returnList.append(p)

    return returnList

def main():
    projects = loadProjects('output')
    projects = [p for p in projects if len(p.category) != 0]
    categoryValueTest(projects)

if __name__ == "__main__":
    main()
