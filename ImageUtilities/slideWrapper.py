import openslide
from PIL import Image, TiffImagePlugin
import PIL.ImageOps
import numpy as np
import numpy.matlib
import os
import fnmatch
import matplotlib as mpl
from matplotlib.path import Path

from ImageUtilities.enumModule import Direction, StepSize
from ImageUtilities import blob

class SlideWrapper(object):
    '''
    Class to encapsulate interactions with microscopy experiments.
    Wraps the openslide package to support multiple channels/images and zoom levels.
    Keeps track of current view window so movement is called by step functions.
    '''
    def __init__(self, fileName, size = [1024,1024], startLvl = 0):
        '''
        Create a new slideWrapper instance with the fileName experiment
        Automatically looks for multiple images.  Ndpi image pairs should end in
        Brightfield or Triple.  Single Ndpi images are also supported.  Tif images
        should end in c#.tif (e.g. c1.tif) to be grouped together.  The tif image set
        doesn't need to be consecutive.  Single Tif images are also supported
        fileName: a tif or ndpi image 
        size: The width and height of the image to load
        startLvl: the starting zoom level.  0 <= startLvl, with 0 being the max zoom
        '''
        
        (p,f) = os.path.split(fileName)
        (f,ex) = os.path.splitext(f)
        
        self.slides = []
        self.filetype = ex
            
        #nanozoomer, ends in triple or brighfield
        if ex == '.ndpi':
            #brightfield image selected
            if "Brightfield" == f[-11:]:
                self.slides.append([openslide.open_slide(fileName)])
                if os.path.exists(os.path.join(p,f[:-11]+'Triple'+ex)):
                    self.slides.append([openslide.open_slide(os.path.join(p,f[:-11]+'Triple'+ex))])
                
            #fluorescence image selected
            elif "Triple" == f[-6:]:
                if os.path.exists(os.path.join(p,f[:-6]+'Brightfield'+ex)):
                    self.slides.append([openslide.open_slide(os.path.join(p,f[:-6]+'Brightfield'+ex))])
                self.slides.append([openslide.open_slide(fileName)])
                
            #single image selected
            else:
                self.slides.append([openslide.open_slide(fileName)])
        
        #zeiss, ends in c#.tif        
        elif ex == '.tif':
            #iterate through each number, 1-9
            if "c" == f[-2] and f[-1].isdigit():
                for i in range(1,9):
                    if os.path.exists(os.path.join(p,f[:-1]+str(i) + ex)):
                        self.slides.append([openslide.open_slide(os.path.join(p,f[:-1]+str(i) + ex))])
                        if os.path.exists(os.path.join(p,'64x' + f[:-1]+str(i) + ex)):
                            self.slides[-1].append(openslide.open_slide(os.path.join(p,'8x' + f[:-1]+str(i) + ex)))
                            self.slides[-1].append(openslide.open_slide(os.path.join(p,'64x' + f[:-1]+str(i) + ex)))
                    else:
                        self.slides.append(None)
            #single image
            else:
                self.slides.append([openslide.open_slide(os.path.join(p,f + ex))])
                #load decimated images if they exist
                if os.path.exists(os.path.join(p,'64x' + f + ex)):
                    self.slides[-1].append(openslide.open_slide(os.path.join(p,'8x' + f + ex)))
                    self.slides[-1].append(openslide.open_slide(os.path.join(p,'64x' + f + ex)))
            #remove end until not empty
            while self.slides[-1] is None:
                self.slides.pop()
                
        else:
            raise ValueError("Only tif and ndpi currently supported")

        ind = 0
        #get first non-blank channel
        while self.slides[ind] is None:
            ind += 1        
        
        #initialize variables
        self.level_count = self.slides[ind][0].level_count   
        self.dimensions = self.slides[ind][0].dimensions       
        
        self.displaySlides = [True]*len(self.slides)
        self.brightInd = ind #index of brightfield image, determines how channels are merged
        self.size = size
        self.lvl = startLvl
        self.lvl = 0 if self.lvl < 0 else self.lvl
        limit = self.level_count-1+2
        if len(self.slides[ind]) > 2:
            limit += 6
        self.lvl = limit if self.lvl > limit else self.lvl
        self.pos = [size[0]*2**(self.lvl-1), size[1]*2**(self.lvl-1)]
        
    def getImg(self):
        '''
        Reads the slide image from disk at the current position, zoom, and channels

        '''
        fluorImg = None
        brightImg = None
        for i,display in enumerate(self.displaySlides):
            #read in brightfield and fluorescence images
            if display == True:
                #only one image is designated as brightfield
                if i == self.brightInd:
                    brightImg = self._getImg(i)
                #fluorescence images are merged by summing the intensity in each channel
                #this can lead to overflow in images that are not 'pure' R,G,B
                else:                    
                    if fluorImg is None:
                        fluorImg = self._getImg(i)
                    else:
                        imgs = []
                        splitOld = fluorImg.split()
                        splitNew = self._getImg(i).split()
                        for j in range(4):#skip alpha
                            if np.max(splitOld[j]) < np.max(splitNew[j]):
                                imgs.append(splitNew[j])
                                #tempnp = np.asarray(splitOld[j]) + np.asarray(splitNew[j])
                                #tempnp[tempnp > 255] = 255
                                #imgs.append(Image.fromarray(np.uint8(tempnp)))
                            else:
                                imgs.append(splitOld[j])
                        fluorImg = Image.merge('RGBA', imgs)

        #merge bright and fluroescence image, or return one of them
        if brightImg is None and fluorImg is None:
            slideImg = Image.new("RGB",self.size,"black")
        elif brightImg is not None and fluorImg is None:
            slideImg = brightImg
        elif fluorImg is not None and brightImg is None:
            slideImg = fluorImg
        else:
            slideImg =Image.blend(brightImg, fluorImg,0.5)
        
        return slideImg

    def _getImg(self, imageInd):
        '''
        Helper method to read in an image from a single channel.  Uses instance position and zoom
        imageInd: the image index to read
        '''
        #have to convert the position to keep self.pos at the center
        #read_region take the top left point
        tempPos = list(map(lambda x, y: int(x-y*2**(self.lvl-1)), 
                   self.pos, self.size))
        #if zoom level is in bounds for openslide
        if self.lvl < self.level_count:
            if self.slides[imageInd] is None:
                return None
            return self.slides[imageInd][0].read_region(tempPos, self.lvl, self.size)
        #decimate image to desired zoom level
        else:         
            #read in larger area and resize down to desired size
            if self.lvl - self.level_count < 2:
                tempPos = list(map(lambda x, y: int(x-y*2**(self.lvl-1)), 
                   self.pos, self.size))
                tempSize = list(map(lambda x: int(x*2**(self.lvl-self.level_count+1)), self.size))
                return self.slides[imageInd][0].read_region(tempPos, self.level_count-1, tempSize).resize(self.size)
                
            #same as above, but with 8x decimated image
            elif self.lvl - self.level_count < 5 and len(self.slides[imageInd]) > 1:
                tempPos[0] //= 8
                tempPos[1] //= 8
                tempSize = list(map(lambda x: int(x*2**(self.lvl-3)), self.size))
                return self.slides[imageInd][1].read_region(tempPos, 0, tempSize).resize(self.size)
            
            #same as above, but with 64x decimated image
            elif  len(self.slides[imageInd]) > 2 and self.lvl-self.level_count < 8: 
                tempPos[0] //= 64
                tempPos[1] //= 64
                tempSize = list(map(lambda x: int(x*2**(self.lvl-6)), self.size))
                return self.slides[imageInd][2].read_region(tempPos, 0, tempSize).resize(self.size)

            #zoom is outside of bounds for this channel
            else:
                return None
    
    def getMaxZoomImages(self, baseDir, positions, size = None, prefix = '', invert = False, imgInd = 1):
        '''
        Saves images of each position provided.
        baseDir: Directory to save all images
        positions: list of tuples with x,y positions of blobs
        size: size of images to save in pixels
        prefix: prefix of images to save
        invert: toggle color inversion.  Can be useful for printing
        imgInd: the image index to use
        '''
        if size is None:
            size = self.size
        for p in positions: 
            imgInd = min(len(self.slides), imgInd)
            tempPos = list(map(lambda x, y: int(x-y/2), p, size))
            if invert:
                fp = os.path.join(baseDir, "{}{}_{}_inv.png".format(prefix,p[0], p[1]))
                img = self.slides[imgInd][0].read_region(tempPos, 0, size)
                img = Image.merge('RGB', img.split()[0:3])
                PIL.ImageOps.invert(img).save(fp)
            else:
                fp = os.path.join(baseDir, "{}{}_{}.png".format(prefix,p[0], p[1]))
                self.slides[imgInd][0].read_region(tempPos, 0, size).save(fp)
    
    def getMaxZoomImage(self, position = None, size = None, imgInd = 1):
        '''
        Get the image at the maximum zoom level.  Used in blob finding
        position: tuple of x,y position of image center.  None to use self.position
        size: tuple of width and height, None for self.size
        imgInd: the image index to read
        '''
        imgInd = min(len(self.slides)-1, imgInd)
        if position is None:
            position = self.pos
        if size is None:
            size = self.size
        tempPos = list(map(lambda x, y: int(x-y/2), 
                            position, size))
        return (self.slides[imgInd][0]).read_region(tempPos, 0, size)
        
    def step(self, direction, stepSize):
        '''
        Step the position in the designated direction.
        direction: a slideWrapper.Direction enum
        stepSize: enum of step size. large = image size, medium 1/2, small 1/10 that size
        '''
        if stepSize == StepSize.large:
            factor = 1
        elif stepSize == StepSize.medium:
            factor = 2
        else:
            factor = 10
        dirMap = {
            Direction.left : [-1,0], 
            Direction.right : [1,0],   
            Direction.up : [0,-1],
            Direction.down : [0,1],   
        }
        self._movePos(factor, dirMap[direction])
    
    def _movePos(self, factor, direction):
        '''
        Helper method to perform position movement.
        factor: division factor to step size
        direction: an x,y list of the step to perform
        '''
        #have to scale position movement by the current zoom level
        self.pos[0] += direction[0] * self.size[0]//factor*2**self.lvl
        self.pos[1] += direction[1] * self.size[1]//factor*2**self.lvl
        
    def _zoom(self, amt):
        '''
        Zoom helper method to bound self.lvl properly
        amt: integer change in zoom level.  <0 is zooming in
        '''
        self.lvl += amt
        #keep >= 0
        self.lvl = 0 if self.lvl < 0 else self.lvl
        #limit sets the amount of software decimation to use.  2 doesn't cause too much lag on GUI
        limit = self.level_count-1+2
        ind = 0
        while self.slides[ind] is None:
            ind += 1     
        #if the images have 8 and 64x decimations available, extra zoom levels are possible
        if len(self.slides[ind]) > 2:
            limit += 6
        self.lvl = limit if self.lvl > limit else self.lvl
    
    def zoomIn(self):
        '''
        Zoom the image in one step (2x smaller pixels)
        '''
        self._zoom(-1)
    
    def zoomOut(self):
        '''
        Zoom the image out one step (2x larger pixels)
        '''
        self._zoom(1)
        
    def resetView(self):
        '''
        Reset the position and zoom level
        Useful for debugging if the position gets far out of bounds
        '''
        self.lvl = 0
        self.pos = [self.size[0]/2, self.size[1]/2]
        
    def switchType(self):
        '''
        Cycle through image channels available, moving +1 from first true
        '''
        ind = 0
        for i in range(len(self.slides)):
            if self.displaySlides[i] == True:
                ind = i+1
                break
        ind %= len(self.slides)
            
        self.switchToChannel(ind)
        
    def switchToChannel(self, ind):
        '''
        Turn the target image channel on and the rest off    
        ind: image channel to activate.  Performs index out of bounds checks
        '''
        self.displaySlides = [False]*len(self.slides)
        if ind < len(self.slides):
            ind = 0 if ind < 0 else ind
            self.displaySlides[ind] = True
        
    def toggleChannel(self,ind):
        '''
        Toggle the supplied image channel on or off
        ind: the image channel to toggle
        '''
        ind = 0 if ind < 0 else ind
        if ind < len(self.slides):
            self.displaySlides[ind] = not self.displaySlides[ind]
        
    def setBrightfield(self,ind):
        '''
        Set the index of the brightfield image.
        If the supplied index is the current brightfield index, turns off the brightfield
        ind: the image channel to set as brightfield
        '''
        if ind == self.brightInd:
            self.brightInd = -1
        else:
            self.brightInd = ind
        
    def moveCenter(self, imgPos):
        '''
        Move self.pos to the supplied image position, in pixels.
        imgPos: the x,y pixel position to move to
        '''
        #have to modify by the current zoom level 
        self.pos[0] += int((imgPos[0]-self.size[0]/2)*2**self.lvl)
        self.pos[1] += int((imgPos[1]-self.size[1]/2)*2**self.lvl)
        
    def getGlobalPoint(self, point):
        """
        Convert the local point in the image view to a slide global point
        point: the local pixel position as tuple
        returns the same point, relative to the top left of the image at max zoom
        """
        result = [0,0]           
        result[0] = self.pos[0] + round((point[0]-self.size[0]/2)*2**self.lvl)
        result[1] = self.pos[1] + round((point[1]-self.size[1]/2)*2**self.lvl)
        return (result[0], result[1])
        
    def getLocalPoint(self, point):
        """
        Convert the global point in slide to position in the current image
        point: the global pixel point
        returns the pixel position in the current image view
        """
        return [round((point[0] - self.pos[0])/2**self.lvl + self.size[0]/2),
            round((point[1] - self.pos[1])/2**self.lvl + self.size[1]/2)]
  
    def getPointsInBounds(self, points):
        """
        Test the supplied global points to see if they land in the current image.
        points: list of global slide pixel positions 
        returns the points in bounds translated into local image coordinate system
            and the indices of those points in the input list
        """
        #get bounds of image in global coordinate
        xlow, ylow = self.getGlobalPoint((0,0))
        xhigh, yhigh = self.getGlobalPoint(self.size)
        zero = (xlow,ylow)
        result = []
        indices = []
        #for each point
        for i, p in enumerate(points):
            #if in bounds
            if p[0] >= xlow and p[0] <= xhigh and p[1] >= ylow and p[1] <=yhigh:
                #add local point and the index of that point
                result.append(((p[0]-zero[0])/2**self.lvl, (p[1]-zero[1])/2**self.lvl))
                indices.append(i)
        return result, indices

    def getBlobsInBounds(self, blobs):
        """
        Test the supplied global points to see if they land in the current image.
        blobs: a list of blobs in global coordinates
        returns a list of (x,y,r) translated into local image coordinate system with radius scaled to zoom level
        """
        if len(blobs) == 0:
            return []
        #get bounds of image in global coordinate
        xlow, ylow = self.getGlobalPoint((0,0))
        xhigh, yhigh = self.getGlobalPoint(self.size)

        return [((b.X-xlow)/2**self.lvl, 
                (b.Y-ylow)/2**self.lvl, 
                b.radius/2**self.lvl)
                for b in blobs
                if b.X > xlow and b.X < xhigh and\
                    b.Y > ylow and b.Y < yhigh]


    def getSize(self):
        '''
        Returns the dimensions of the slide image
        '''
        return self.dimensions
         
    def getFluorInt(self, blobs, channel, imageInd, offset = 0, reduceMax = False):
        '''
        Determines the intensity of pixels around each blob
        blobs: list of blob objects to analyze
        channel: the R,G,B channel to analyze (0, 1, 2)
        imageInd: the image channel to analyze
        offset: adjusts the blob radius to consider smaller or larger regions
        reduceMax: toggle between returning the average (False) or max (True) intensity
        '''
        result = []
        #use the max or mean intensity
        if reduceMax:
            reduction = lambda x: np.max(np.array(x.split()[channel]))
        else:
            reduction = lambda x: np.mean(np.array(x.split()[channel]))
        for i,b in enumerate(blobs):
            #note that this considers the square circumscribing the blob
            img = self.getMaxZoomImage((int(b.X),int(b.Y)), 
                                     (int(b.radius+offset)*2,int(b.radius+offset)*2), 
                                     imgInd=imageInd)
            #calc summed intens in area
            result.append(reduction(img))
            #report every 100 blobs
            if (i+1)%100 == 0:
                print(str(i+1) + ' blobs read')
        return result
   
    @staticmethod                
    def decimateImg(img, factor):
        '''
        Static utility to decimate the image provided
        img: a openslide instance
        factor: integer factor to reduce size by
        returns a PIL.Image of img at the reduced size
        '''
        result = Image.new('RGB', tuple(map(lambda x: x//factor,img.dimensions)))
        import time
        start = time.time()

        #determines how large of a region to read in at once,  works in strips of image
        loadFac = 64      
          
        #read in horizontal strips, this seems to be moderately faster than 
        for i in range(result.size[1]//loadFac):
            result.paste(img.read_region((0,i*factor*loadFac),0,(result.size[0]*factor,factor*loadFac)).resize((result.size[0],loadFac)),
                         (0,i*loadFac,result.size[0],(i+1)*loadFac))
            if i!= 0 and i % 10 == 0 or i == 1:
                print("finished %d of %d subareas, %d seconds left" %
                      (i, result.size[1]//loadFac, 
                        (time.time()-start)/ i * (result.size[1]//loadFac-i)))
        
        #copy remainder
        if result.size[1] % loadFac != 0:
            result.paste(img.read_region((0,result.size[1]//loadFac*loadFac*factor), 0, 
                                         (result.size[0]*factor, result.size[1] % loadFac*factor))
                         .resize((result.size[0], result.size[1]%loadFac)), 
                            (0,result.size[1]//loadFac*loadFac, result.size[0], result.size[1]))

        return result

    @staticmethod
    def generateDecimatedImage(path, baseFile):
        '''
        Saves 8x and 64x image of the single file
        path: path containing image file.  New images written here
        baseFile: base file name with extension, 8x and 64x will be prepended onto base name
        '''
        TiffImagePlugin.WRITE_LIBTIFF = True
        SlideWrapper.decimateImg(openslide.open_slide(os.path.join(path,baseFile)),8).save(os.path.join(path,'8x' + baseFile), compression='tiff_lzw')
        SlideWrapper.decimateImg(openslide.open_slide(os.path.join(path,'8x' + baseFile)),8).save(os.path.join(path,'64x' + baseFile), compression='tiff_lzw')        
        TiffImagePlugin.WRITE_LIBTIFF = False

    @staticmethod
    def generateDecimatedImgs(filename):
        '''
        Saves 8x and 64x images of given image in filename as 8xFILENAME and 64xFILENAME
        filename: Full path to tif image
        '''
        
        (p,f) = os.path.split(filename)
        (f,ex) = os.path.splitext(f)
        #zeiss, ends in c#.tif        
        if ex == '.tif':
            #filename has c# form, decimate each
            if "c" == f[-2] and f[-1].isdigit():
                totimgs = 0
                for i in range(1,9):
                    if os.path.exists(os.path.join(p,f[:-1]+str(i) + ex)):
                        totimgs += 1
                for i in range(1,9):
                    if os.path.exists(os.path.join(p,f[:-1]+str(i) + ex)):
                        print("starting channel {} of {}".format(i, totimgs))
                        SlideWrapper.generateDecimatedImage(p, f[:-1]+str(i) + ex)    
            #filename is a single tif image
            else:
                SlideWrapper.generateDecimatedImage(p,f + ex)    

    @staticmethod
    def decimateDirectory(dirName):
        #get all dirs in parent dir
        for subd in [os.path.join(dirName,o) for o in os.listdir(dirName) if os.path.isdir(os.path.join(dirName,o))]:
            targetFiles = [os.path.join(subd, o) for o in os.listdir(subd) if fnmatch.fnmatch(o, '*.tif')]
            for fname in targetFiles:
                (path, file) = os.path.split(fname)
                if (not os.path.exists(os.path.join(path, '8x' + file)) or not os.path.exists(os.path.join(path, '64x' + file))) \
                    and file[0:2] != '8x' and file[0:3] != '64x':
                    print(fname)
                    SlideWrapper.generateDecimatedImage(path, file)
        print('Finished!')