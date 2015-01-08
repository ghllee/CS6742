import numpy as np

def emissionProb(initProb, transProb, observation, lms):
    '''Log-scale forward algorithm from
    http://bozeman.genome.washington.edu/compbio/mbt599_2006/hmm_scaling_revised.pdf
    Assumption: everything already comes in logscale.
    initProb: {state -> initProb}
    transProb: {(state1, state2) -> transProb}
    observation: [sentence1, sentence2, ...]
    lms: {state -> language model (with logProb function)}'''
    def elnsum(elnx,elny):
        if elnx == "LZ" or elny == "LZ":
            if elnx == "LN":
                return elny
            else:
                return elnx
        else:
            if elnx > elny:
                return elnx + np.log(1 + np.exp(elny-elnx))
            else:
                return elny + np.log(1 + np.exp(elnx-elny))
    def elnprod(elnx, elny):
        if elnx == "LZ" or elny == "LZ":
            return "LZ"
        else:
            return elnx + elny

    states = lms.keys()
    M = np.zeros(len(lms), len(observation))
    for i in range(len(states)):
        curState = states[i]
        M[i,0] = elnprod(initProb[i], lms[curState].logProb(observation[0]))
    for i in range(1, len(observation)):
        for j in range(len(states)):
            curObs = observation[i]
            curState = states[j]
            logalpha = "LZ"
            for k in range(len(states)):
                logalpha = elnsum(logalpha, elnprod(M[k, i-1], transProbs[(states[k],curState)]))
            M[j,i] = elnprod(logalpha, states[j].logProb(curObs))
    

    finalAns = "LZ"
    for i in range(len(states)):
        finalAns = elnsum(finalAns, M[states[i], len(observation)-1])
    return finalAns

def getStartProbs(inFile, smooth = .01):
    '''Given a paths file, return a dictionary {states -> logged init prob}'''
    return -1

def main():
    pass

if __name__ == "__main__":
    main()
