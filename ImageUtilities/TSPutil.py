from scipy.spatial.distance import pdist
import numpy as np
import time
import random

def TSPRoute(inlist, optT1 = 30, optT2 = 60):
    '''
    optimizes the traversal order of a list of points
    should be close to optimal after completing all iterations
    returns a list of indices to visit in optimized order
    inlist: a list of the positions
    optT1: max optimization time for the initial, nearest neighbor optimization in seconds
    optT2: max optimization time for the 2-opt in seconds
    '''

    if inlist is None or len(inlist) == 0:
        return None

    dat = np.array([])
    
    #strip off just the x and y values
    for l in inlist:
        dat = np.append(dat,[l[0], l[1]])
    
    dat = np.reshape(dat,(np.size(dat)//2,2))
    #calculate pair-wise distances
    dists = pdist(dat)
    #map the i,j values of a square form matrix to the flat form returned by pdist
    def sqr(i,j,n=dat.shape[0]):
        if i < j:
            return int(n*i-(i+1)*i/2 + (j-i-1))
        return int(n*j-(j+1)*j/2 + (i-j-1))
        
    #nearest neighbor traversal
    bestDist = float("inf")
    inds = list(range(dat.shape[0]))

    #randomize starting index
    random.seed(0)#for testing purposes
    random.shuffle(inds)

    iterat = 0
    start_time = time.time();
    #while not timed out
    while time.time()-start_time < optT1 and iterat < dat.shape[0]:
        #the current solution start point
        soln = [inds.pop()]
        #current iteration
        iterat += 1
        #remaining points to visit in this iteration
        remaining = [i for i in range(0,dat.shape[0])]
        remaining.pop(soln[0])
            
        #for each point
        for count in range(1,dat.shape[0]):
            #visit next closest neighbor
            nextI = np.argmin(list(map(lambda i: dists[sqr(i,soln[-1])], remaining)))
            #add to solution and remove from remaining
            soln.append(remaining.pop(nextI))
            
        #calculate the total traversed distance
        dist = sum(map(lambda i: dists[sqr(soln[i],soln[i+1])],range(dat.shape[0]-1)))
        #if better than previous nearest neighbor traversal
        if dist<bestDist:
            #update best path and print update
            bestDist = dist
            bestSoln = soln[:]
            print("{0} iterations of nearest neighbor in {1:.1f} seconds".format(iterat, time.time()-start_time))  
    
    print("{} iterations of nearest neighbor".format(iterat))
    soln=bestSoln

    #add a blank node to end, won't move from the end
    #allows the start position to move around
    soln.append(len(soln))
    dists = np.append(dists, np.zeros(len(soln)))
        
    start_time = time.time();
    iterat=0
    
    #2-opt
    #while not timing out and still optimizing
    while time.time()-start_time < optT2:
        iterat += 1
        #keep track of if a switch in the path was made
        pathChanged = False
        #for each point
        for i in range(1,dat.shape[0]):
            #for each point between i and end
            for j in range(i+1,dat.shape[0]-1):
                #check if switching i-1 -> i to i-1 -> j is improvement
                if dists[sqr(soln[i-1],soln[i])] + dists[sqr(soln[j],soln[j+1])] > \
                    dists[sqr(soln[i],soln[j+1])] + dists[sqr(soln[j],soln[i-1])]:
                    #reverse the order of points visited
                    soln[i:j+1] = reversed(soln[i:j+1])
                    pathChanged = True
                    break #go to next i
        if pathChanged == False:
            break #stop if no switches were made over each for loop
        if iterat % 5 == 0:
            print("{0} iterations of TSP in {1:.1f} seconds".format(iterat, time.time()-start_time))  
    print("{0} iterations of TSP in {1:.1f} seconds".format(iterat, time.time()-start_time))  

    del soln[-1] #remove last, dummy point
    print("TSP optimization finished!")
    return soln