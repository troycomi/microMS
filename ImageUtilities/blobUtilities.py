import numpy as np
import scipy
from scipy.spatial.distance import pdist
from GUICanvases import GUIConstants
from ImageUtilities import blob

class blobUtilities(object):
    """
    A collection of static utility methods for interacting with "blobs"
    Lists of tuples with (x, y, radius, circularity,...)
    """

    @staticmethod
    def distanceFilter(blobs, dist, subblocks = None, verbose = False):
        '''
        Filter blob positions based on a set separation distance.
        Implemented by dividing the area into different subregions.
        Cells are binned into at least one region, then all pairwise distances
        are compared to the distance cutoff.
        Returns list of bool with result[i] == true if i has a neighbor too close (< dist away)

        blobs: list of blobs
        dist: the distance cutoff
        subblocks: specify the number of sublocks to divide the area into.
            Divides the x and y into subblocks sections
            = None allows the function to dynamically determine number of subblocks 
        verbose: set if output message is printed to console
        '''
        if blobs is None or len(blobs) == 0:
            return None
        #initialize result and determine subblocks
        result = [False] * len(blobs)
        if subblocks is None:
            subblocks = int(np.ceil(np.sqrt(len(blobs)/100)))
            subblocks = min(subblocks, 5)

        subLocs = blobUtilities._groupBlobs(blobs, dist, subblocks)

        #perform distance filtering on each sub block
        for i in range(subblocks+1):
            for j in range(subblocks+1):
                #number of points in sub region
                n = len(subLocs[i][j])
                #np array of points
                locs = np.zeros((n,2))
                #populate locs
                for ii,v in enumerate(subLocs[i][j]):
                    locs[ii,0] = blobs[v].X
                    locs[ii,1] = blobs[v].Y
                #distance filter the sub region list
                #tooClose[i] == true if point[i] is too close to a neighbor
                tooClose = blobUtilities._distFilter(locs, dist)
                #set result, index is the subLocs[x][y] and the kth point in that subregion list
                for k in np.where(tooClose)[0]:
                    result[subLocs[i][j][k]] = True

        #determine number of cells passing filter
        count = np.sum(result)
        #report to console
        if verbose: print("Done! {} cells within {} pixels, {} remaining".format(count, dist, len(result) - count))

        return result

    
    @staticmethod    
    def _distFilter(locs, dist):
        '''
        A helper function for performing distance filtering of a np matrix.
        Returns a list of bool with result[i] == true if too close to another point
        locs: np array of points[n][2]
        dist: the distance cutoff
        '''
        #number of points
        n = len(locs)
        #map between square form of row i, column j, and the row vector from pdist
        q = lambda i,j,n: n*j - j*(j+1)/2+i-1-j
        #initialize result
        result = [False] * n
        #calculate euclidean distance
        dists = pdist(locs)
        #for each x,y pair
        for i in range(1,n):
            for j in range(i):
                #if distance between i and j is less than distance
                if dists[q(i,j,n)] < dist:
                    #both blobs fail, ie result = true
                    result[i] = True
                    result[j] = True
        return result

    
    @staticmethod
    def minimumDistances(blobs, subblocks = None, overlap = 250):
        '''
        Calculate the minimum distance between each blob.
        Similar algorithm to distFilter, but records the min distance
        returns a list of floats with the minimum distance between each point
        blobs: list of blobs
        subblocks: number of subdivisions of x and y dimension
            = None to dynamically choose number of subblocks
        overlap: the amount of overlap in pixels between subregions, in a sense defines
            the maximum, reliable distance reported
        '''

        if blobs is None or len(blobs) == 0:
            return None
        
        #initialize result
        result = [float("inf")] * len(blobs)
        #determine subblocks size
        if subblocks is None:
            subblocks = int(np.ceil(np.sqrt(len(blobs)/100)))
            subblocks = min(subblocks, 5)

        subLocs = blobUtilities._groupBlobs(blobs, overlap, subblocks)

        #for each sub region list
        for i in range(subblocks+1):
            for j in range(subblocks+1):
                #number of points
                n = len(subLocs[i][j])
                #initialize temporary list of points
                locs = np.zeros((n,2))
                #add points into locs
                for ii,v in enumerate(subLocs[i][j]):
                    locs[ii,0] = blobs[v].X
                    locs[ii,1] = blobs[v].Y
                #calculate distances
                dists = blobUtilities._minDists(locs)
                #recorde minimum of the reported distance and previous value
                for k, d in enumerate(dists):
                    result[subLocs[i][j][k]] = min(result[subLocs[i][j][k]], d)
        
        temp = np.array(result)
        maxVal = max(temp[temp != float("inf")])
        maxVal = max(maxVal, overlap)
        for i, r in enumerate(result):
            if r == float("inf"):
                result[i] = maxVal
        return result
    
    @staticmethod
    def _minDists(locs):
        '''
        A helper function to calculate the closest neighbor of each blob
        returns a list of floats with result[i] indicating there exists another neighbor
            that distance away.
        locs: an np array of the x,y coordinates
        '''
        #get number of points
        n = len(locs)
        #lambda function to convert index in square and row form
        q = lambda i,j,n: n*j - j*(j+1)/2+i-1-j
        #initialize result
        result = [float("inf")] * n
        #calculate euclidean distance between each point
        dists = pdist(locs)
        #for each x,y pair
        for i in range(1,n):
            for j in range(i):
                #record the minimum of the current distance an the previous value
                result[i] = min(result[i], dists[q(i,j,n)])
                result[j] = min(result[j], dists[q(i,j,n)])
        return result

    @staticmethod
    def _groupBlobs(blobs, overlap, subblocks):
        '''
        A helper function for grouping blobs into subregions defined by the number of subblocks
        return a 2d list of indices split by the blob x and y coordinates
        blobs: list of blobs
        overlap: amount of overlap for adding duplicate blobs
        subblocks: number of subdivisions in x and y
        '''
        #find min and max limits of x and y
        lowX = min(map(lambda x : x.X, blobs))
        highX = max(map(lambda x : x.X, blobs))
        lowY = min(map(lambda x : x.Y, blobs))
        highY = max(map(lambda x : x.Y, blobs))

        #find subblock size of x and y
        subX =  (highX - lowX)/ subblocks
        subY = (highY - lowY)/subblocks

        #initialize a 2d array of empty lists to hold each point
        result = [[[] for x in range(subblocks+1)] for y in range(subblocks+1)]
        
        #place indices of points into subLocs list
        for i,v in enumerate(blobs):
            #get divisor and remainder
            (xd, xm) = (0,0) if subX == 0 else divmod(v.X-lowX, subX)
            (yd, ym) = (0,0) if subY == 0 else divmod(v.Y-lowY, subY)
            xd, yd = int(xd), int(yd)
            #put into 'normal block'
            result[xd][yd].append(i)
            #place into overlap region
            #in the top left corner
            if (xm <=2*overlap and ym <= 2*overlap) and (xd-1 >=0 and yd -1 >=0):
                result[xd-1][yd-1].append(i) 
            #in the left margin
            if xm <= 2*overlap and xd-1 >= 0:
                result[xd-1][yd].append(i)
            #in the top margin
            if ym <= 2*overlap and yd -1 >= 0:
                result[xd][yd-1].append(i)

        return result

    @staticmethod
    def circularPackPoints(blobs, spacing, maxSpots, offset, minSpots = 4, 
                           r=GUIConstants.DEFAULT_PATTERN_RADIUS, c = 1):
        '''
        Expands each blob into several points surrounding the blob.
        blobs: list of blobs to expand
        spacing: minimum spacing between points
        maxSpots: max number of spots to expand for each blob
        offset: offset of circumference to space blobs
        minSpots: minimum number of spots for each blob.  Ignores spacing with min spots
        r: radius of new blobs
        c: circumference of new blobs
        returns a list of blobs of the expanded positions
        '''
        #check maxspots to ensure less than min
        maxSpots = minSpots if maxSpots < minSpots else maxSpots
        #calculate min and max r:
        maxR = maxSpots*spacing/(2* np.pi)-offset
        #angles and unit vectors of max spots
        thetas = np.linspace(0,2*np.pi,maxSpots,False)
        maxUnits = np.vstack((np.cos(thetas),np.sin(thetas)))
        
        minR = minSpots*spacing/(2*np.pi)-offset
        #angles and unit vectors at min number of spots
        thetas = np.linspace(0,2*np.pi,minSpots,False)
        minUnits = np.vstack((np.cos(thetas),np.sin(thetas)))
        
                
        result = []
        ind = 0
        for blb in blobs:
            #check radius for min, max or between
            if(blb.radius > maxR):
                unitvec =  maxUnits
            elif(blb.radius < minR):
                unitvec = minUnits
            #between min and max, use most spots as possible while retaining the spacing
            else:
                spots = np.floor(2*np.pi*(blb.radius + offset)/spacing)
                thetas = np.linspace(0,2*np.pi,spots,False)
                unitvec = np.vstack((np.cos(thetas),np.sin(thetas)))
            
            #expand each blob into a new x,y positions        
            targetSpots = unitvec*(blb.radius + offset) + \
                np.matlib.repmat(np.array((blb.X, blb.Y))
                                 ,unitvec.shape[1],1).T
            #add targets to result
            for e in targetSpots.T:
                result.append(blob.blob(x = e[0],y = e[1], radius = r, circularity = c, group = ind))
            #increment group number for next blob
            ind += 1
                        
        return result
    
    @staticmethod
    def rectangularlyPackPoints(blobs, spacing, numLayers, 
                                   r = GUIConstants.DEFAULT_PATTERN_RADIUS, c = 1,
                                   dynamicLayering = False):
        '''
        Expands each blob into a grid of points, with regular rectangular spacing
        blobs: list of blob objects to expand
        spacing: spacing between new blobs
        numLayers: number of layers around each cell. 1 generates a grid of 3x3 with the 
            initial blob in the center.  This can be adjusted for radius
        r: radius to set new blobs to
        c: circularity of new blobs
        dynamicLayering: set to True to account for blob size in making pattern positions
        '''
        #marcher is a list of directions to move to for generating the spacing
        #this starts at the right, moves down, left, up, right, down, to spiral around the blob
        #additional layers are generated by applying the marcher multiple times
        marcher = np.array([[0  ,  1],
                            [-1.   ,  0.   ],
                            [-1.   ,  0.   ],
                            [0.   ,  -1.   ],
                            [0.   ,  -1.   ],
                            [ 1.   ,  0.   ],
                            [ 1.   ,  0.   ],
                            [0  ,  1]])
        #use one mask each time
        if dynamicLayering == False:
            #start at center
            mask = np.array([[0,0]])
            for n in range(numLayers):
                #move to the right by n spaces
                current = np.array([[n+1.,0]])
                for i in range(8):
                    #add the marcher n times
                    direction = marcher[i,:]
                    for j in range(n+1):
                        current += direction
                        mask = np.append(mask,current,axis=0)
            #scale unit mask by spacing
            mask *= spacing
        
        result = []
        ind = 0
        for blb in blobs:
            #use new mask each blob, with number of layers being size dependent
            if dynamicLayering == True:
                mask = np.array([[0,0]])
                #only change from above is the blb.radius/spacing
                for n in range(numLayers + int(np.ceil(blb.radius / spacing))):
                    current = np.array([[n+1.,0]])
                    for i in range(8):
                        direction = marcher[i,:]
                        for j in range(n+1):
                            current += direction
                            mask = np.append(mask,current,axis=0)
                    
                mask *= spacing
            #expand blb by mask
            for b in map(lambda x: blob.blob(x = x[0], y = x[1], radius = r, circularity=c, group=ind), 
                         list(mask+(blb.X, blb.Y))
                         ):
                #add each point to result
                result.append(b)
            ind += 1
        return result
    
    @staticmethod
    def hexagonallyClosePackPoints(blobs, spacing, numLayers, 
                                   r = GUIConstants.DEFAULT_PATTERN_RADIUS, c = 1,
                                   dynamicLayering = False):
        '''
        Expands each blob into a grid of points, with hexagonal close packed spacing
        blobs: list of blob objects to expand
        spacing: spacing between new blobs
        numLayers: number of layers around each cell. 1 generates a grid of 7 with the 
            initial blob in the center.  This can be adjusted for radius
        r: radius to set new blobs to
        c: circularity of new blobs
        dynamicLayering: set to True to account for blob size in making pattern positions
        '''
        #this may save some computation time to precompute
        sqrt3ov2 = np.sqrt(3)/2
        #list of directions to march along to generate a layer
        marcher = np.array([[-0.5  ,  sqrt3ov2],
                            [-1.   ,  0.   ],
                            [-0.5  , -sqrt3ov2],
                            [ 0.5  , -sqrt3ov2],
                            [ 1.   ,  0.   ],
                            [ 0.5  ,  sqrt3ov2]])
        #use one mask each time
        if dynamicLayering == False:
            #start at center
            mask = np.array([[0,0]])
            for n in range(numLayers):
                current = np.array([[n+1.,0]])
                for i in range(6):
                    direction = marcher[i,:]
                    for j in range(n+1):
                        current += direction
                        mask = np.append(mask,current,axis=0)
                    
            mask *= spacing
        
        
        #strip off radius
        result = []
        ind = 0
        for blb in blobs:
            #use new mask each blob, with number of layers being size dependent
            if dynamicLayering == True:
                mask = np.array([[0,0]])
                #change number of layers by blb radius
                for n in range(numLayers + int(np.ceil(blb.radius / spacing))):
                    current = np.array([[n+1.,0]])
                    for i in range(6):
                        direction = marcher[i,:]
                        for j in range(n+1):
                            current += direction
                            mask = np.append(mask,current,axis=0)
                    
                mask *= spacing
            #expand blb into points based on mask
            for b in map(lambda x: blob.blob(x = x[0], y = x[1], radius = r, circularity=c, group=ind), 
                         list(mask+(blb.X, blb.Y))
                         ):
                result.append(b)
            ind += 1
        return result

    @staticmethod
    def saveBlobs(filename, blobs, blobFinder, filters = []):
        '''
        save the current cell coordinates in pixels and the set of cell find parameters
        and histogram filters applied to generate the set
        fileName: file to save to
        blobs: list of blob objects to save
        blobFinder: the blob finding object
        filters: list of descriptions of filters applied by histCanvas
        '''
        if blobs is None or len(blobs) == 0:
            return
        output = open(filename,'w')
        #save blob finding parameters
        for key, val in blobFinder.getParameters().items():
            output.write("{}\t{}\n".format(key,val))
        #save histogram filters 
        if len(filters) != 0:
            output.write("->{}->\n".format('->'.join(filters)))
        else:
            output.write("->\n")
        #blb parameter header
        output.write("x\ty\tr\tc\n")    
        #save blobs
        for b in blobs:
            output.write("{}\n".format(b.toString()))
            
        output.close()

    @staticmethod
    def loadBlobs(filename, blobFinder):
        '''
        Loads the blobs and sets the blob finding parameters from a filename
        returns a list of blobs and the new blob finder
        filename: the txt file to read in.  Formatted from saveBlobs
        blobFinder: the current blob finder object.  Will overwrite some parameters
        '''
        reader = open(filename,'r')
        lines = reader.readlines()
        result = []
        for l in lines:
            toks = l.split('\t')
            if len(toks) == 2:
                #set blob finder parameters
                blobFinder.setParameterFromSplitString(toks)
            elif toks[0] != 'x':
                #add new blob
                result.append(blob.blob.blobFromSplitString(toks))    

        return result, blobFinder
    