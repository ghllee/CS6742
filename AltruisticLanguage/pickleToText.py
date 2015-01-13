import EDA
import KickstarterParser
from KickstarterParser import Project, Reward, FAQ

def main():
    projects = EDA.loadProjects("output", numFiles = 10)
    for i in range(len(projects)):
        curProject = projects[i]
        with open('writing/' + str(i) + '.txt', 'w') as f:
            f.write(curProject.text)

if __name__ == "__main__":
    main()
