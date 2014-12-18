from KickstarterParser import *
from EDA import loadProjects

def main():
    projects = loadProjects('output')
    projects = [p for p in projects if len(p.category) != 0]
    print len(projects)

if __name__ == "__main__":
    main()
