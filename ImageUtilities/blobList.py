import numpy as np
import scipy
from scipy.spatial.distance import pdist
import matplotlib.pyplot as plt
from matplotlib.path import Path
from copy import deepcopy
import ast

from GUICanvases import GUIConstants

from ImageUtilities import blob
from ImageUtilities import blobFinder

class blobList(object):
    """
    A collection of blob objects.
    Underlying data is the list self.blobs and supplies several
    utilities for filtering, drawing and expanding blobs.
    Each bloblist also contains its own blobfinder and filters
    """

    def __init__(self, slide = None):
        self.blobs = []
        self.blobFinder = blobFinder.blobFinder(slide)
        self.filters = []
        self.description = None
        self.threshCutoff = None
        self.ROI = []
        self.groupLabels = dict()
        ##Add any new instance vars to deepcopy!

    def append(self, blb):
        if isinstance(blb, blob.blob):
            self.blobs.append(blb)

    def length(self):
        return len(self.blobs)

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        result.blobs = deepcopy(self.blobs)
        result.filters = deepcopy(self.filters)
        result.description = deepcopy(self.description)
        result.ROI = deepcopy(self.ROI)
        result.threshCutoff = self.threshCutoff
        result.groupLabels = deepcopy(self.groupLabels)

        result.blobFinder = blobFinder.blobFinder(self.blobFinder.slide)
        result.blobFinder.copyParameters(self.blobFinder)

        return result

    def partialDeepCopy(self, newBlobs):
        cls = self.__class__
        result = cls.__new__(cls)

        result.blobs = newBlobs
        result.generateGroupLabels()
        result.filters = deepcopy(self.filters)
        result.description = deepcopy(self.description)
        result.ROI = deepcopy(self.ROI)
        result.threshCutoff = self.threshCutoff

        result.blobFinder = blobFinder.blobFinder(self.blobFinder.slide)
        result.blobFinder.copyParameters(self.blobFinder)

        return result


    def saveBlobs(self, filename):
        '''
        save the current blob coordinates in pixels and the set of blob find parameters
        and histogram filters applied to generate the set
        fileName: file to save to
        '''
        if len(self.blobs) == 0:
            return
        output = open(filename,'w')
        #save blob finding parameters
        for key, val in self.blobFinder.getParameters().items():
            output.write("{}\t{}\n".format(key,val))
        #save ROI
        output.write('ROI: {}\n'.format(self.ROI))
        #save histogram filters 
        if len(self.filters) != 0:
            output.write("->{}->\n".format('->'.join(self.filters)))
        else:
            output.write("->\n")
        #blb parameter header
        output.write("x\ty\tr\tc\n")    
        #save blobs
        for b in self.blobs:
            output.write("{}\n".format(b.toString()))
            
        output.close()

    def loadBlobs(self, filename):
        '''
        Loads the blobs and sets the blob finding parameters from a filename
        filename: the txt file to read in.  Formatted from saveBlobs
        '''
        reader = open(filename,'r')
        lines = reader.readlines()
        self.blobs = []
        for l in lines:
            toks = l.split('\t')
            if len(toks) == 2:
                #set blob finder parameters
                self.blobFinder.setParameterFromSplitString(toks)
            elif toks[0] != 'x' and len(toks) > 2:
                #add new blob
                self.blobs.append(blob.blob.blobFromSplitString(toks))    
            else:
                #get filters
                toks = l.split('->')
                if len(toks) > 1:
                    self.filters = toks[1:-1]
                elif l[0:3] == 'ROI':
                    self.ROI = ast.literal_eval(l[5:])

        self.generateGroupLabels()

    def blobRequest(self, globalPoint, radius):
        '''
        Tries to add the blob to the current blob list.  
        If overlap with current blob, remove that point
        globalPoint: (x,y) tuple in the image coordinate space
        radius: the radius of the new blob to be added
        returns true if a blob was added, false if one was removed
        '''
        for i,b in enumerate(self.blobs):
            if (globalPoint[0]-b.X)**2 + (globalPoint[1]-b.Y)**2 <= \
                b.radius**2:
                self.blobs.pop(i)
                return False, i

        self.blobs.append(blob.blob(globalPoint[0], globalPoint[1], radius))
        return True, -1


    def blobSlide(self):
        if len(self.ROI) < 3:
            self.blobs = self.blobFinder.blobSlide()
            return "Finished blob finding on whole slide, found {} blobs".format(len(self.blobs))
        else:
            self.blobs = self.blobFinder.blobSlide(ROI = self.ROI)
            if len(self.blobs) != 0:
                roi = Path(self.ROI)
                points = np.array([ (b.X,b.Y) for b in self.blobs])
                self.blobs = [self.blobs[i] for i in np.where(roi.contains_points(points))[0]]
            return "Finished blob finding in ROI, found {} blobs".format(len(self.blobs))

    def getROI(self, point, distCutoff):
        '''
        Performs checks and additions to interacting with an ROI. Does not alter ROI
        point: global point to check
        returns a new list of tuples of the ROI
        '''
        result = self.ROI.copy()
        if point is not None and len(self.ROI) > 2:
            #find distances between point and ROI
            dists = pdist([point] + result)[:len(result)]
            #remove first point with dist <= ROI_DIST
            for i,d in enumerate(dists):
                if d < distCutoff:
                    result.pop(i)
                    return result

            #add between the two closest dists
            dists = np.append(dists, dists[0])
            dist2 = []
            for i in range(len(dists) -1):
                dist2.append(dists[i] + dists[i+1])
            #quick, no check for intersection
            #result.insert(np.argmin(dist2)+1, point)

            #slower, checks for overlapping, returns the shortest distance without overlap
            pos = np.argsort(dist2)
            for p in pos:
                #check first leg of path
                segment = Path([result[p], point])
                testSeg = Path(result[p+1:] + result[:p], [Path.MOVETO] + [Path.LINETO]*(len(result)-2))
                if testSeg.intersects_path(segment):
                    continue

                #check second leg of path
                if p+1 == len(result):
                    segment = Path([point, result[0]])
                    testSeg = Path(result[1:], [Path.MOVETO] + [Path.LINETO]*(len(result)-2))
                    if testSeg.intersects_path(segment):
                        continue
                else:
                    segment = Path([point, result[p+1]])
                    testSeg = Path(result[p+2:] + result[:p+1], [Path.MOVETO] + [Path.LINETO]*(len(result)-2))
                    if testSeg.intersects_path(segment):
                        continue

                #passed, return:
                result.insert(p+1, point)
                return result

        elif point is not None:
            result.append(point)
            
        return result

    def roiFilter(self):
        if len(self.ROI) < 3:
            return deepcopy(self)
        roi = Path(self.ROI)
        points = np.array([ (b.X,b.Y) for b in self.blobs])
        if points.size == 0:
            return self.partialDeepCopy([])
        result = self.partialDeepCopy([self.blobs[i] for i in np.where(roi.contains_points(points))[0]])
        return result

    def distanceFilter(self, dist, subblocks = None, verbose = False):
        '''
        Filter blob positions based on a set separation distance.
        Implemented by dividing the area into different subregions.
        Blobs are binned into at least one region, then all pairwise distances
        are compared to the distance cutoff.
        Returns list of bool with result[i] == true if i has a neighbor too close (< dist away)

        blobs: list of blobs
        dist: the distance cutoff
        subblocks: specify the number of sublocks to divide the area into.
            Divides the x and y into subblocks sections
            = None allows the function to dynamically determine number of subblocks 
        verbose: set if output message is printed to console
        '''
        if self.blobs is None or len(self.blobs) == 0:
            return
        #initialize result and determine subblocks
        result = [False] * len(self.blobs)
        if subblocks is None:
            subblocks = int(np.ceil(np.sqrt(len(self.blobs)/100)))
            subblocks = min(subblocks, 5)

        subLocs = self._groupBlobs(dist, subblocks)

        #perform distance filtering on each sub block
        for i in range(subblocks+1):
            for j in range(subblocks+1):
                #number of points in sub region
                n = len(subLocs[i][j])
                #np array of points
                locs = np.zeros((n,2))
                #populate locs
                for ii,v in enumerate(subLocs[i][j]):
                    locs[ii,0] = self.blobs[v].X
                    locs[ii,1] = self.blobs[v].Y
                #distance filter the sub region list
                #tooClose[i] == true if point[i] is too close to a neighbor
                tooClose = blobList._distFilter(locs, dist)
                #set result, index is the subLocs[x][y] and the kth point in that subregion list
                for k in np.where(tooClose)[0]:
                    result[subLocs[i][j][k]] = True

        #determine number of blobs passing filter
        count = np.sum(result)
        #report to console
        if verbose: print("Done! {} blobs within {} pixels, {} remaining".format(count, dist, len(result) - count))
        
        newList = self.partialDeepCopy([self.blobs[i] for i in np.where(~np.array(result))[0]])
        newList.filters.append("distance > {}".format(dist))
        return newList

    
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
        q = lambda i,j,n: int(n*j - j*(j+1)/2+i-1-j)
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

    def minimumDistances(self, subblocks = None, overlap = 250):
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

        if self.blobs is None or self.length() == 0:
            return None
        
        #initialize result
        result = [float("inf")] * len(self.blobs)
        #determine subblocks size
        if subblocks is None:
            subblocks = int(np.ceil(np.sqrt(len(self.blobs)/100)))
            subblocks = min(subblocks, 5)

        subLocs = self._groupBlobs(overlap, subblocks)

        #for each sub region list
        for i in range(subblocks+1):
            for j in range(subblocks+1):
                #number of points
                n = len(subLocs[i][j])
                #initialize temporary list of points
                locs = np.zeros((n,2))
                #add points into locs
                for ii,v in enumerate(subLocs[i][j]):
                    locs[ii,0] = self.blobs[v].X
                    locs[ii,1] = self.blobs[v].Y
                #calculate distances
                dists = blobList._minDists(locs)
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
        q = lambda i,j,n: int(n*j - j*(j+1)/2+i-1-j)
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

    def _groupBlobs(self, overlap, subblocks):
        '''
        A helper function for grouping blobs into subregions defined by the number of subblocks
        return a 2d list of indices split by the blob x and y coordinates
        overlap: amount of overlap for adding duplicate blobs
        subblocks: number of subdivisions in x and y
        '''
        #find min and max limits of x and y
        lowX = min(map(lambda x : x.X, self.blobs))
        highX = max(map(lambda x : x.X, self.blobs))
        lowY = min(map(lambda x : x.Y, self.blobs))
        highY = max(map(lambda x : x.Y, self.blobs))

        #find subblock size of x and y
        subX =  (highX - lowX)/ subblocks
        subY = (highY - lowY)/subblocks

        #initialize a 2d array of empty lists to hold each point
        result = [[[] for x in range(subblocks+1)] for y in range(subblocks+1)]
        
        #place indices of points into subLocs list
        for i,v in enumerate(self.blobs):
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

    def circularPackPoints(self, spacing, maxSpots, offset, minSpots = 4, 
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
        for blb in self.blobs:
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
                   
        result = self.partialDeepCopy(result)     
        result.generateGroupLabels()
        return result
    
    def rectangularlyPackPoints(self, spacing, numLayers, 
                                   r = GUIConstants.DEFAULT_PATTERN_RADIUS, c = 1,
                                   dynamicLayering = False):
        '''
        Expands each blob into a grid of points, with regular rectangular spacing
        blobs: list of blob objects to expand
        spacing: spacing between new blobs
        numLayers: number of layers around each blob. 1 generates a grid of 3x3 with the 
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
        for blb in self.blobs:
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

        result = self.partialDeepCopy(result)
        result.generateGroupLabels()
        return result
    
    def hexagonallyClosePackPoints(self, spacing, numLayers, 
                                   r = GUIConstants.DEFAULT_PATTERN_RADIUS, c = 1,
                                   dynamicLayering = False):
        '''
        Expands each blob into a grid of points, with hexagonal close packed spacing
        blobs: list of blob objects to expand
        spacing: spacing between new blobs
        numLayers: number of layers around each blob. 1 generates a grid of 7 with the 
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
        for blb in self.blobs:
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
        
        result = self.partialDeepCopy(result)
        result.generateGroupLabels()
        return result

    def generateGroupLabels(self):
        '''
        Populates groupLabels, a dict of NAME -> (x,y) for each group member.
        (x,y) is the top right corner (max X, min Y) in global coordinates
        '''

        self.groupLabels = dict()
        for b in self.blobs:
            if b.group is not None:
                #add in current blob
                if b.group not in self.groupLabels:
                    self.groupLabels[b.group] = (b.X, b.Y)
                else:
                    #update tuple
                    p = self.groupLabels[b.group]
                    self.groupLabels[b.group] = (max(b.X, p[0]), min(b.Y, p[1]))


    def getPatches(self, limitDraw, slideWrapper, blobColor):

        todraw = slideWrapper.getBlobsInBounds(self.blobs)

        if limitDraw and len(todraw) > GUIConstants.DRAW_LIMIT:

            todraw = [todraw[i] for i in range(0, len(todraw), 
                                               len(todraw)//GUIConstants.DRAW_LIMIT)]

        return list(map(lambda el: plt.Circle((el[0],el[1]), el[2],
                                             color = blobColor,
                                             linewidth = 1,
                                             fill = False), todraw))