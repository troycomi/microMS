import skimage
from skimage import measure
import numpy as np
from itertools import product
import time
import scipy

from ImageUtilities.blob import blob

import matplotlib
import matplotlib.pyplot as plt

class blobFinder(object):
    '''
    performs blob finding on a slidewrapper object
    '''
    def __init__(self, slide, minSize = 50, maxSize = None,
                 minCircularity = 0.6, maxCircularity = None,
                 colorChannel = 2, threshold = 75, imageIndex = 1):
        '''
        set up the slidewrapper
        slide: slidewrapper to interact with
        minSize: minimum blob size in pixels
        maxSize: maximum blob size in pixels, None for no maximum
        minCircularity: minimum blob circularity
        maxCircularity: maximum blob circularity, None for no max
        colorChannel: [0, 1, 2] -> [R, G, B] channel to select
        threshold: maximum pixel intensity to consider a blob
        imageIndex: index of multi-slide object to consider
        '''
        self.slide = slide
        self.minSize = minSize
        self.maxSize = maxCircularity
        self.minCircularity = minCircularity
        self.maxCircularity = maxCircularity
        self.colorChannel = colorChannel
        self.threshold = threshold
        self.imageIndex = imageIndex

    def copyParameters(self, other):
        '''
        Copies cell finding parameters from another cellFinder instance
        other: blobFinder object to copy parameters from
        '''
        self.minSize = other.minSize
        self.maxSize = other.maxCircularity
        self.minCircularity = other.minCircularity
        self.maxCircularity = other.maxCircularity
        self.colorChannel = other.colorChannel
        self.threshold = other.threshold
        self.imageIndex = other.imageIndex


    def getParameters(self):
        '''
        get the set of parameters as a dictionary
        returns a dictionary of string -> value  pairs of all parameters for cell finding
        '''
        return {
                'minSize' : self.minSize,
                'maxSize' : self.maxSize,
                'minCir' : self.minCircularity,
                'maxCir' : self.maxCircularity,
                'channel' : self.colorChannel,
                'thresh' : self.threshold,
                'ImageInd' : self.imageIndex}

    def setParameterFromSplitString(self, toks):
        '''
        Sets the parameters dictated in the toks list.  String must match from getParameters
        toks: list of strings generated from string.split
        '''
        if toks is None or len(toks) < 2:
            return

        if toks[0] == 'minSize':
            if toks[1] == 'None\n':
                raise(ValueError('None type not acceptable for minSize'))
            self.minSize = int(toks[1])

        elif toks[0] == 'maxSize':
            if toks[1] == 'None\n':
                self.maxSize = None
            else:
                self.maxSize = int(toks[1])

        elif toks[0] == 'minCir':
            if toks[1] == 'None\n':
                raise(ValueError('None type not acceptable for minCirc'))
            self.minCircularity = float(toks[1])

        elif toks[0] == 'maxCir':
            if toks[1] == 'None\n':
                self.maxCircularity = None
            else:
                self.maxCircularity = float(toks[1])

        elif toks[0] == 'channel':
            if toks[1] == 'None\n':
                raise(ValueError('None type not acceptable for channel'))
            self.colorChannel = int(toks[1])

        elif toks[0] == 'thresh':
            if toks[1] == 'None\n':
                raise(ValueError('None type not acceptable for thresh'))
            self.threshold = int(toks[1])

        elif toks[0] == 'ImageInd':
            if toks[1] == 'None\n':
                raise(ValueError('None type not acceptable for ImageInd'))
            self.imageIndex = int(toks[1])

        
    def getBlobCharacteristics(self, pnt):
        '''
        Gets the area and circularity for a blob containing the supplied point
        Returns 0,0 if no blob containing point
        pnt: (x,y) of the reqested point
        '''
        #get current image
        img = self.slide.getImg()
        #threshold image
        lbl, num = blobFinder._blbThresh(img, self.colorChannel, self.threshold)
        slices = scipy.ndimage.find_objects(lbl)
        area, circ = 0,0
        #for each blob in region
        for i in range(num):
            s = slices[i]
            dx, dy = s[:2]
            #check if piont is within the bounds of the blob
            if dx.start < pnt[1] and dx.stop > pnt[1] and \
                dy.start < pnt[0] and dy.stop > pnt[0]:
                #convert blob to boolean image
                region = lbl[dx.start-1:dx.stop+1, dy.start-1:dy.stop+1]
                region = region == i+1
                #get area and circularity
                area = np.sum(region)
                perim = skimage.measure.perimeter(region)
                if perim == 0:
                    circ = 1
                else:
                    circ = min(4*np.pi * area / perim**2, 1)
                #scale area by zoom level
                #these get progressively less accurate with higher zoom level
                area = area * 2**(2*self.slide.lvl)
                break
        return area, circ
        
    @staticmethod
    def _blbHelp(img, sizes, channel = 2, threshold = 200,
                 circs = (0.7,None), xShift=0, yShift = 0):
        '''
        helper function to perform blob finding on the image
        returns a list of blobs
        img: the image to blob find
        sizes: (min, max) size to consider  max == None means not max size
        channel: r,g,b channel to threshold
        threshold: minimum pixel intensity to count as cell
        circs: (min, max) circularity to consider max == None means no max
        xShift: amount to add to x coordinate to shift into global coordinate
        yShift: amount to add to x coordinate to shift into global coordinate
        '''
        #blob find
        lbl, num = blobFinder._blbThresh(img, channel, threshold)
        slices = scipy.ndimage.find_objects(lbl)
        result = []
        #for each blob
        for i in range(num):
            #convert to boolean image
            s = slices[i]
            dx, dy = s[:2]
            region = lbl[dx.start-1:dx.stop+1, dy.start-1:dy.stop+1]
            region = region == i+1
            #area is total number of true pixels
            area = np.sum(region)
            #if passes size threshold
            if area > sizes[0] and (sizes[1] is None or area < sizes[1]):
                #calculate circularity = 4 pi area / perimeter^2
                perim = skimage.measure.perimeter(region)
                circ = 4*np.pi * area / perim**2
                #if passes circularity threshold
                if circ > circs[0] and (circs[1] is None or circ < circs[1]):
                    #determine center of mass, ignoring intensity
                    (x,y) = scipy.ndimage.measurements.center_of_mass(region)
                    #calculate radius assuming circle
                    r = np.sqrt(area/np.pi)
                    #add to result, note x,y transpose!
                    result.append(blob(y=x+dx.start-1+yShift, 
                                       x = y+dy.start-1+xShift, 
                                       radius = r, 
                                       circularity = circ))
        return result
    
    @staticmethod
    def _blbThresh(img, channel = 2, threshold = 200):
        '''
        helper function to threshold and group image
        returns the label and total number of objects from ndimage.label
        img: image to consider
        channel: r,g,b channel to threshold
        threshold: min intensity cutoff
        '''
        img = np.array(img.split()[channel])
        thresh = img > threshold 
        return scipy.ndimage.label(thresh)  
    
    def blobImg(self):
        '''
        perform blob finding on the current position of slideWrapper at max zoom
        returns a list of blobs in image
        '''
        inputImg = self.slide.getMaxZoomImage(imgInd = self.imageIndex)
        return blobFinder._blbHelp(inputImg, (self.minSize, self.maxSize), self.colorChannel, 
                                   self.threshold, (self.minCircularity, self.maxCircularity))
        
    def blobSlide(self, subSize = 8192, ROI = None):
        '''
        perform blob finding on the entire image bounded by ROI 
        only reads a subregion of the image at once, which causes an initial grouping of blobs
        returns a list of blobs in image
        subSize: size in pixels of one side of the subregion to iterate over
            larger values may use up lots of RAM
        ROI: a list of points for ROI polygon.  Only used to determine bounding box.
        '''
        #the amount of overlap between regions, would matter with larger objects but I currently ignore this
        overlap = 0

        #if ROI is none, get max size and (0,0)
        if ROI is None or len(ROI) < 2:
            botR = self.slide.getSize()
            topL = (0,0)
            ROI = [topL, botR]
        else:
            topL = (min(map(lambda x: x[0], ROI)),
                    min(map(lambda x: x[1], ROI)))
            botR = (max(map(lambda x: x[0], ROI)),
                    max(map(lambda x: x[1], ROI)))

        #set of x and y values of the center of each sub image
        xs = np.arange(topL[0] + subSize//2, botR[0]+subSize//2, subSize-overlap)
        ys = np.arange(topL[1] + subSize//2, botR[1]+subSize//2, subSize-overlap)
        
        #cortesian product of xs and ys
        centers = product(xs,ys)

        #initialize time, blob list, and iterator count
        start = time.time()
        total = len(xs) * len(ys)
        print("starting %d images" % total)
        blbs = []
        i = 1

        #for each subregion
        for cent in centers:
            #get max zoom image
            inputImg = self.slide.getMaxZoomImage((int(cent[0]),int(cent[1])), 
                                                  (subSize,subSize),imgInd = self.imageIndex)
            #blob find
            blb = blobFinder._blbHelp(inputImg, (self.minSize, self.maxSize), 
                                      self.colorChannel, self.threshold, 
                                      (self.minCircularity, self.maxCircularity),
                                      cent[0]-subSize/2, cent[1]-subSize/2)
            blbs.extend(blb)
            #print out expected time remaining, not super accurate
            if i % 10 == 0 or i == 1:
                print("finished %d of %d subareas, %d seconds left" % (i, total, (time.time()-start)/ i * (total-i)))
            i = i+1
            
        print("took {:.3f} minutes".format((time.time() - start)/60))
        
        return blbs            