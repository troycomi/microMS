
from PIL import ImageDraw, ImageFont
import matplotlib as mpl
from matplotlib.path import Path
from matplotlib.collections import PatchCollection
import matplotlib.pyplot as plt
import os
import random
from scipy.spatial.distance import pdist
import numpy as np
from copy import deepcopy, copy

from GUICanvases import GUIConstants

from ImageUtilities import slideWrapper
from ImageUtilities import blobFinder
from ImageUtilities import blob
from ImageUtilities import TSPutil
from ImageUtilities.enumModule import Direction, StepSize
from ImageUtilities import blobList

from CoordinateMappers import supportedCoordSystems

class MicroMSModel(object):
    '''
    The model of a microMS experiment consisting of a slide, blob finder, and blobs
    Performs several vital functions for interacting with each object and maintains a list of blobs
    '''
    def __init__(self, GUI):
        '''
        Initialize a new model setup.  Slide starts as None.
        The coordinateMapper is set as the first mapper of the supported mappers.
        Also calls self.resetVariables to clear other instance variables.
        GUI: the supporting GUI
        '''
        self.slide = None
        self.coordinateMapper = supportedCoordSystems.supportedMappers[0]
        self.resetVariables()
        self.GUI = GUI

    def setupMicroMS(self, filename):
        '''
        Loads an image and sets up a new session
        filename: the image to load
        '''
        self.slide = slideWrapper.SlideWrapper(filename)
        self.resetVariables()

    def resetVariables(self):
        '''
        Clears and initializes all instance variables
        '''
        self.blobCollection = [blobList.blobList(self.slide) for i in range(10)]

        self.currentBlobs = 0
        self.tempBlobs = None
        self.histogramBlobs = None
        self.histColors = None
        self.coordinateMapper.clearPoints()
        self.mirrorImage = False
        self.showPatches = True
        self.drawAllBlobs = False
        self.showPrediction = False
        self.showThreshold = False

    def setCoordinateMapper(self, newMapper):
        '''
        Sets a new coordinate mapper and clears its points
        newMapper: the new instance of coordinateMapper to use
        '''
        self.coordinateMapper = newMapper
        self.coordinateMapper.clearPoints()

    def saveEntirePlot(self, fileName):
        '''
        saves the entire slide image at the current zoom level
        fileName: the file to write to
        *NOTE: this can take a while to run and generate large files at max zoom
        '''
        #save the current size and position
        size, pos = self.slide.size, self.slide.pos
        #match size to whole slide, position at center
        self.slide.size, self.slide.pos = \
            (self.slide.dimensions[0]//2**self.slide.lvl, 
             self.slide.dimensions[1]//2**self.slide.lvl), \
            (self.slide.dimensions[0]//2, self.slide.dimensions[1]//2)
        
        #get whole image
        wholeImg = self.slide.getImg()
        draw = ImageDraw.Draw(wholeImg)
        
        #markup image
        linWid = 1 if 6-self.slide.lvl < 1 else 6-self.slide.lvl
        tfont = ImageFont.truetype("arial.ttf",linWid+6)
        #for each blob list
        for ii in range(len(self.blobCollection)):
            if self.blobCollection[ii].length() > 0:
                    drawnlbls = set()
                    drawlbl = self.blobCollection[ii].blobs[0].group is not None      
                    #for each blob      
                    for i,gb in enumerate(self.blobCollection[ii].blobs):
                        p = self.slide.getLocalPoint((gb.X,gb.Y))
                        rad = gb.radius/2**self.slide.lvl
                        #draw blob outline
                        draw.ellipse((p[0]-rad, p[1]-rad, p[0]+rad, p[1]+rad), outline=GUIConstants.MULTI_BLOB[ii])
                        #draw label if group exists
                        if drawlbl and gb.group not in drawnlbls:
                            draw.text((p[0]+10/2**self.slide.lvl,p[1]-10/2**self.slide.lvl),
                                           str(gb.group),
                                            font=tfont, fill=GUIConstants.EXPANDED_TEXT)
                            drawnlbls.add(gb.group)
        
        #save image
        wholeImg.save(fileName)

        #restore size and position
        self.slide.size, self.slide.pos = size, pos 

    def saveCurrentBlobFinding(self, filename):
        '''
        Save the current blob finder and currently selected blob list
        filename: file to save to
        '''
        #slide not set up
        if self.slide is None:
            return "No slide loaded"
        #current list is empty
        if self.blobCollection[self.currentBlobs].length() == 0:
            return "List {} contains no blobs!".format(self.currentBlobs +1) #plus one for GUI display
        #save blobs
        self.blobCollection[self.currentBlobs].saveBlobs(filename)
        return "Saved blob information"

    def saveHistogramBlobs(self, filename):
        '''
        Save up to 3 files for different histogram filters
        filename: the filename to save
        '''
        #slide not set up
        if self.slide is None:
            return "No slide loaded"
        #no histogram blobs to save
        if self.histogramBlobs is None or len(self.histogramBlobs) == 0:
            return "No histogram divisions provided"
        #save different divisions
        f, ex = os.path.splitext(filename)
        for blbs in self.histogramBlobs:
            if blbs.length() > 0:
                blbs.saveBlobs('{}_{}_{}{}'.format(f, blbs.description, blbs.threshCutoff, ex))
        return "Saved histogram divisions with base name {}".format(os.path.split(f)[1])

    def saveAllBlobs(self, filename):
        '''
        Save each list of blobs in it's own list
        filename: a full filename with extension.  The list number will be added as such:
            dir/test.txt -> dir/test_1.txt
        '''
        #slide not set up
        if self.slide is None:
            return "No slide loaded"
        f, ex = os.path.splitext(filename)
        #save each blob list
        for i, blbs in enumerate(self.blobCollection):
            if blbs.length() > 0:
                blbs.saveBlobs('{}_{}{}'.format(f, i, ex))

        return "Saved blobs with base name '{}'".format(os.path.split(f)[1])

    def saveCoordinateMapper(self, filename):
        '''
        Save the current coordinate mapper
        filename: file to save to
        '''
        #no fiducials trained
        if len(self.coordinateMapper.pixelPoints) < 1:
            return "No coordinates to save"

        self.coordinateMapper.saveRegistration(filename)
        return "Saved coordinate mapper"

    def saveInstrumentPositions(self, filename, tspOpt, maxPoints = None):
        '''
        save positions of blobs in instrument coordinate system
        fileName: file to save to
        tspOpt: bool indicating whether or not to perform traveling salesman optimization
        maxPoints: maximum number of blobs to save.  Default (None) saves all
        '''
        #check if the file can be saved
        if len(self.coordinateMapper.physPoints) < 2:
            return "Not enough training points to save instrument file"

        if self.blobCollection[self.currentBlobs].length() == 0:
            return "No blobs to save"

        #get current blob list
        blobs = self.blobCollection[self.currentBlobs].blobs
        #if maxPoints is valid
        if maxPoints is not None and maxPoints > 0 and maxPoints < self.currentBlobLength():
            #obtain a randome sample of blobs
            blobs = random.sample(blobs,maxPoints)
                         
        #if tspOpt is requested       
        if tspOpt == True:
            #reorder visit order
            soln = TSPutil.TSPRoute(blob.blob.getXYList(blobs))
            blobs = [blobs[i] for i in soln]

        #save list of blobs
        self.coordinateMapper.saveInstrumentFile(filename, 
                                                 blobs)
        return "Saved instrument file of list {}".format(self.currentBlobs +1 )

    def saveInstrumentRegistrationPositions(self, filename):
        '''
        Save fiducial locations in the instrument coordinate system
        '''
        if len(self.coordinateMapper.physPoints) < 2:
            return "Not enough training points to save fiducial locations"
        self.coordinateMapper.saveInstrumentRegFile(filename)
        return "Saved instrument registration positions"

    def loadCoordinateMapper(self,filename):
        '''
        load a prior registration file
        changes the current mapper to the one specified in the file
        filename: file to load
        returns a status string to display, and the index of the new mapper
        '''
        #get old index
        old = supportedCoordSystems.supportedMappers.index(self.coordinateMapper)
        #get first line in file
        reader = open(filename,'r')
        line = reader.readline().strip()
        reader.close()
        #see if that is a name of a coordinatemapper
        try:
            i = supportedCoordSystems.supportedNames.index(line)
        except:
            return 'Unsupported instrument: {}'.format(line), old

        #See if mapper has changed to warn the user
        result = 'Loaded {} registration'.format(line)
        if i != old:
            result = 'Warning, changing instrument to {}'.format(line)
            self.coordinateMapper = supportedCoordSystems.supportedMappers[i]
        self.coordinateMapper.loadRegistration(filename)
        return result, i

    def loadBlobFinding(self, filename):
        '''
        Loads the blobs in the provided filename to the current list of blobs and sets the blobfinder to the preivous values
        filename: file to load
        '''
        self.blobCollection[self.currentBlobs].loadBlobs(filename)
        return "Finished loading blob positions"

    def loadInstrumentPositions(self, filename):
        '''
        Load a instrument position file to the current blob list.
        Will not have proper radius, but should retain the groups.
        filename: file to load
        '''
        self.blobCollection[self.currentBlobs].blobs = \
            self.coordinateMapper.loadInstrumentFile(filename)
        self.blobCollection[self.currentBlobs].generateGroupLabels()
        return "Finished loading instrument file"

    def currentBlobLength(self):
        '''
        Gets the length of the current blob list
        '''
        return self.blobCollection[self.currentBlobs].length()

    def currentInstrumentExtension(self):
        '''
        Gets the instrument extension of the current coordinate mapper
        '''
        return self.coordinateMapper.instrumentExtension

    def runGlobalBlobFind(self):
        '''
        Performs global blob finding on the current slide and sets to current blob list
        '''
        if self.slide is None:
            return "No slide was open"
        return self.blobCollection[self.currentBlobs].blobSlide()

    def updateCurrentBlobs(self, newBlobs):
        if not isinstance(newBlobs, blobList.blobList):
            raise ValueError('New blobs must be a blobList')
        
        #find first unused blob index
        for i in range(len(self.blobCollection)):
            if self.blobCollection[i].length() == 0:
                #add new blobs
                self.blobCollection[i] = newBlobs
                self.currentBlobs = i
                return

    def distanceFilter(self, distance):
        '''
        filters the global blob list to remove blobs which are closer than 'distance' pixels
        the prior list is stored in previous current index
        distance: distance threshold
        '''
        if self.currentBlobLength() == 0:
            return "No blobs to filter"
        
        self.updateCurrentBlobs(self.blobCollection[self.currentBlobs].distanceFilter(distance, verbose = True))

        return "Finished distance filter"

    def roiFilter(self):
        if self.currentBlobLength() == 0:
            return "No blobs to filter"
        if len(self.blobCollection[self.currentBlobs].ROI) < 3:
            return "No ROI selected"
        startLen = self.currentBlobLength()
        self.updateCurrentBlobs(self.blobCollection[self.currentBlobs].roiFilter())
        endLen = self.currentBlobLength()
        return "{} blobs removed, {} remain".format(startLen - endLen, endLen)


    def hexPackBlobs(self, separation, layers, dynamicLayering = False):
        '''
        expands each blob into hexagonally closest packed positions
        sep: minimum separation between points
        layers: number of layers to generate
        dynamicLayering: adjust the number of layers with the blob radius
        '''
        self.updateCurrentBlobs(self.blobCollection[self.currentBlobs]\
            .hexagonallyClosePackPoints(separation, layers, dynamicLayering = dynamicLayering))

    
    def rectPackBlobs(self, separation, layers, dynamicLayering = False):
        '''
        expands each blob into rectangularly packed positions
        sep: minimum separation between points
        layers: number of layers to generate
        dynamicLayering: adjust the number of layers with the blob radius
        '''
        self.updateCurrentBlobs(self.blobCollection[self.currentBlobs]\
            .rectangularlyPackPoints(separation, layers, dynamicLayering = dynamicLayering))
        
    def circularPackBlobs(self, separation, maxShots, offset):
        '''
        expands each blob into circularly packed positions around the blob
        sep: minimum separation between spots
        shots: maximum number of spots to place around each blob
        offset: offset from the current circumference, 
        offset > 0 places spots outside the current blob
        '''
        self.updateCurrentBlobs(self.blobCollection[self.currentBlobs]\
            .circularPackPoints(separation, maxShots, offset, minSpots = 4))

    def analyzeAll(self):
        '''
        if the current mapper is connected to an instrument, triggers analysis of all blobs currently found
        '''
        #get all pixel points and translate to motor coords
        if self.currentBlobLength() == 0:
           return "No targets currently selected"
        if len(self.coordinateMapper.physPoints) <= 2:
           return "Not enough training points"
        if self.coordinateMapper.connectedInstrument is None or \
            self.coordinateMapper.connectedInstrument.connected == False:
           return "No connected instrument"

        targets = list(map(lambda b: self.coordinateMapper.translate((b.X, b.Y)), 
                            self.blobCollection[self.currentBlobs].blobs))

        #send to connected instrument
        self.coordinateMapper.connectedInstrument.collectAll(targets)

        return "Finished collection"

    def setBlobSubset(self, blobSubset):
        '''
        Sets the histogram blobs supplied by a histcanvas
        blobSubset: an odd object, tuple of lists, first is a blobList, second a list of colors
        '''
        self.histogramBlobs = blobSubset[0]
        self.histColors = blobSubset[1]

    def reportSlideStep(self, direction, stepSize):
        '''
        Moves the slide in the specified direction, taking into account mirroring
        direction: a slideWrapper.direction in the observed direction
        stepSize: enum dictating if the step size
        '''
        if self.slide is not None:
            if self.mirrorImage:
                if direction == Direction.left:
                    self.slide.step(Direction.right, stepSize)
                elif direction == Direction.right:
                    self.slide.step(Direction.left, stepSize)
                else:
                    self.slide.step(direction, stepSize)

            self.slide.step(direction, stepSize)

    def testBlobFind(self):
        '''
        Performs a test blob find on the current position
        Sets the zoom level to the maximum value to match test blob finding
        '''
        self.slide.lvl = 0
        if self.slide is not None:
            self.tempBlobs = self.blobCollection[self.currentBlobs].blobFinder.blobImg()

    def setCurrentBlobs(self, ind):
        '''
        Sets the current blob index to the specified value
        ind: integer value of list to show
        '''
        self.currentBlobs = ind

    def reportSize(self, newSize):
        '''
        Sets the size of the slidewrapper to the specified value.
        Sets the max number of pixels to 600 but keeps the aspect ratio
        newSize = (width, height)
        '''
        w,h = newSize
        factor = 600/max(w,h)
        w, h = int(w*factor), int(h*factor)
        self.slide.size = [w, h]

    def getCurrentImage(self):
        '''
        gets the image to display, accounting for showing thresholds
        '''
        #show the threshold image produced by blobfinder helper method
        if self.showThreshold:
            im, num = blobFinder.blobFinder._blbThresh(self.slide.getImg(),
                                                        self.blobCollection[self.currentBlobs].blobFinder.colorChannel,
                                                        self.blobCollection[self.currentBlobs].blobFinder.threshold)
            return im                                  
        #else, use current image view     
        else:
            return self.slide.getImg()

    def getPatches(self, limitDraw):
        '''
        Gets the patches of all blobs, registration marks and predicted points.
        limitDraw: boolean toggle to limit the number of blobs to draw
        '''
        ptches = []
        #nothing requested or nothing to show
        if self.showPatches == False or self.slide is None:
            return PatchCollection(ptches)

        #temp blobs from blob finding test.  Only drawn once and the only displayed thing
        if self.tempBlobs is not None:
            ptches = [plt.Circle((blb.X, blb.Y),
                                  blb.radius,
                                  color = GUIConstants.TEMP_BLOB_FIND,
                                  linewidth = 1,
                                  fill = False)
                       for blb in self.tempBlobs]
            #reset temp blobs
            self.tempBlobs = None
            #return patches, if none to show match_original needs to be false
            return PatchCollection(ptches, match_original=(len(ptches) != 0))
        
        #draw predicted points from coordinate mapper
        lineWid = 1 if 6-self.slide.lvl < 1 else 6-self.slide.lvl   
        if self.showPrediction and len(self.coordinateMapper.physPoints) >= 2:
            points, inds = self.slide.getPointsInBounds(self.coordinateMapper.predictedPoints())
            ptches.extend(
                    [plt.Circle(p, GUIConstants.FIDUCIAL_RADIUS/2**self.slide.lvl,
                                color = GUIConstants.PREDICTED_POINTS,
                                linewidth = lineWid,
                                fill = False)
                     for p in points]
                )

        #draw fiducial locations, showing the worst FLE in a different color
        worstI = -1
        if len(self.coordinateMapper.physPoints) > 2:
            worstI = self.coordinateMapper.highestDeviation()
        points, inds = self.slide.getPointsInBounds(self.coordinateMapper.pixelPoints)
        for i,p in enumerate(points):
            if inds[i] == worstI:
                ptches.append(
                    plt.Circle(p, GUIConstants.FIDUCIAL_RADIUS/2**self.slide.lvl,
                               color = GUIConstants.FIDUCIAL_WORST,
                               linewidth = lineWid,
                               fill=False)
                    )
            else:
                ptches.append(
                    plt.Circle(p, GUIConstants.FIDUCIAL_RADIUS/2**self.slide.lvl,
                               color = GUIConstants.FIDUCIAL,
                               linewidth = lineWid,
                               fill=False)
                    )

        #draw region of interest
        ptches.extend(self.getROIPatches())

        #draw histogram blobs
        if self.histogramBlobs is not None and len(self.histogramBlobs) != 0:
            for i, blbs in enumerate(self.histogramBlobs):
                ptches.extend(blbs.getPatches(limitDraw, self.slide, self.histColors[i]))

        #draw blobs
        else:
            #draw all blob lists with their own color
            if self.drawAllBlobs == True:
                for j, blobs in enumerate(self.blobCollection):
                    ptches.extend(blobs.getPatches(limitDraw, self.slide, GUIConstants.MULTI_BLOB[j]))

            #show only the current blob list
            else:
                ptches.extend(self.blobCollection[self.currentBlobs].getPatches(limitDraw, self.slide,
                                                                                GUIConstants.MULTI_BLOB[self.currentBlobs]))

        #return list of patches as a patch collection, if none match_original must be false
        return PatchCollection(ptches, match_original=(len(ptches) != 0))

    def getROIPatches(self, newPoint = None):
        ptches = []
        tROI = self.blobCollection[self.currentBlobs].getROI(newPoint, GUIConstants.ROI_DIST *2**self.slide.lvl)

        if len(tROI) > 1:
            verts = []
            for roi in tROI:
                verts.append(self.slide.getLocalPoint(roi))
            verts.append(self.slide.getLocalPoint(tROI[0]))
            ptches.append(mpl.patches.PathPatch(Path(verts, None),
                                                color = GUIConstants.ROI,
                                                fill = False))

        return ptches

    def reportROI(self, point):
        '''
        Handles ROI additions and removals based on position
        point: the point in global coordinates
        '''
        self.blobCollection[self.currentBlobs].ROI = \
            self.blobCollection[self.currentBlobs].getROI(point, GUIConstants.ROI_DIST *2**self.slide.lvl)

    def drawLabels(self, axes):
        '''
        draw text labels on the supplied axis.  Assume the axis is displaying the
        slide image and blobs of the current state of everything.
        '''
        if self.slide is None or self.showPatches == False:
            return

        #fiducial labels
        lineWid = 1 if 6-self.slide.lvl < 1 else 6-self.slide.lvl   
        #draw fiducial labels, showing the worst FLE in a different color
        worstI = -1
        if len(self.coordinateMapper.physPoints) > 2:
            worstI = self.coordinateMapper.highestDeviation()
        points, inds = self.slide.getPointsInBounds(self.coordinateMapper.pixelPoints)
        for i,p in enumerate(points):
            if inds[i] == worstI:
                col = GUIConstants.FIDUCIAL_WORST
            else:
                col = GUIConstants.FIDUCIAL
            axes.text(p[0] + GUIConstants.FIDUCIAL_RADIUS/2**self.slide.lvl,
                        p[1] - GUIConstants.FIDUCIAL_RADIUS/2**self.slide.lvl,
                        self.coordinateMapper.predictLabel(self.coordinateMapper.physPoints[inds[i]]),
                        fontsize = lineWid + 6,
                        fontweight='bold',
                        color = col,
                        bbox=dict(facecolor=GUIConstants.FIDUCIAL_LABEL_BKGRD))
        #show group labels
        #hist blobs have no text
        if self.histogramBlobs is not None and len(self.histogramBlobs) != 0:
            pass
        #normal blobs can have group labels
        else:
            pass
            #show group names of all lists
            if self.drawAllBlobs == True:
                for blobs in self.blobCollection:
                    self._drawBlobLabels(axes, blobs, lineWid)

            #show only the current list
            else:
                self._drawBlobLabels(axes, self.blobCollection[self.currentBlobs], lineWid)

    def _drawBlobLabels(self, axes, blobs, lineWid):
        '''
        Helper method to draw blob labels onto the provided axis
        axes: matplotlib axes to draw text to
        blobs: blobList with labels to draw
        lineWid: the linewidth to use for drawing 
        '''
        #get grouplabels from blobs
        labels = list(blobs.groupLabels.keys())
        pos = list(blobs.groupLabels.values())
        if len(labels) != 0:
            points, inds = self.slide.getPointsInBounds(pos)
            for i,p in enumerate(points):
                #add offset from normal position
                axes.text(p[0]+GUIConstants.DEFAULT_RADIUS/2**self.slide.lvl,
                                p[1]-GUIConstants.DEFAULT_RADIUS/2**self.slide.lvl,
                                labels[inds[i]],
                                fontsize=lineWid+6, 
                                color=GUIConstants.EXPANDED_TEXT)

    def reportInfoRequest(self, localPoint):
        '''
        Handles a request for image/blob information at the supplied local point
        localPoint: (x,y) tuple of the query point in the local coordinate space
            of the slide image
        returns a string description of the point
        '''
        #nothing to query against
        if self.slide is None:
            return "No slide loaded"

        point = self.slide.getGlobalPoint(localPoint)
        #if the histogram canvas is shown, highlight that blob's location
        if self.GUI is not None and self.GUI.showHist:
            #find blob if user clicked in bounds
            if self.blobCollection[self.currentBlobs] is not None and \
                self.blobCollection[self.currentBlobs].length() > 0:

                points, inds = self.slide.getPointsInBounds(blob.blob.getXYList(self.blobCollection[self.currentBlobs].blobs))
                found = False
                for i,p in enumerate(points):
                    #see if click point is within radius
                    if (localPoint[0]-p[0])**2 + (localPoint[1] - p[1])**2 <= \
                        (self.blobCollection[self.currentBlobs].blobs[inds[i]].radius/2**self.slide.lvl)**2:
                            self.GUI.histCanvas.singleBlob = inds[i]
                            found = True
                            break
                #if not found, set to None
                if not found:
                    self.GUI.histCanvas.singleBlob = None

        #get pixel color and alpha (discarded)
        try:
            r,g,b,a = self.slide.getImg().getpixel(localPoint)
        except IndexError:
            r,g,b = 0,0,0

        #get the size and circ of an area > thresh if on blb view
        if self.showThreshold:
            area,circ = self.blobCollection[self.currentBlobs].blobFinder.getBlobCharacteristics(localPoint)
            return "x = %d, y = %d r,g,b = %d,%d,%d\tArea = %d\tCirc = %.2f"%(point[0], point[1], r, g, b, area, circ)
        #show rgb and x,y location
        else:
            return "x = %d, y = %d r,g,b = %d,%d,%d"%(point[0], point[1], r, g, b)

    def reportFiducialRequest(self, localPoint, removePoint, extras = None):
        '''
        handles a fiducial request.
        localpoint: (x,y) tuple in the image coordinate system
        removePoint: boolean toggle.  If true, the closest fiducial is removed
        extras: a debuging object to bypass GUI display. Must define text and ok
        '''
        #no slide to register against
        if self.slide is None:
            return "No slide loaded"

        globalPos = self.slide.getGlobalPoint(localPoint)

        #shift RMB to remove closest fiducial
        if removePoint:
            if len(self.coordinateMapper.physPoints) == 0:
                return "No points to remove"
            self.coordinateMapper.removeClosest(globalPos)
            return "Removed fiducial"

        #get physical location from user
        else:
            #mapper returns predicted location
            predicted = self.coordinateMapper.predictName(globalPos)

            #prompt user
            if self.GUI is None and extras is None:
                return "No input provided"
            if extras is not None:#make this check first for debugging
                text = extras.text
                ok = extras.ok
            elif self.GUI is not None:
                text, ok = self.GUI.requestFiducialInput(predicted)
                
            if ok:
                #validate entry
                if self.coordinateMapper.isValidEntry(text):
                    #add position to mapper
                    self.coordinateMapper.addPoints(globalPos, 
                                                    self.coordinateMapper.extractPoint(text))
                    return "%s added at %d,%d" % (text, globalPos[0], globalPos[1])
                else:
                    return "Invalid entry: {}".format(text)

    def reportBlobRequest(self, localPoint, radius):
        '''
        Tries to add the blob to the current blob list.  
        If overlap with current blob, remove that point
        localPoint: (x,y) tuple in the image coordinate space
        radius: the radius of the new blob to be added
        '''
        #no slide to add blobs onto
        if self.slide is None:
            return "No slide loaded"
        
        globalPnt = self.slide.getGlobalPoint(localPoint)
        added, removeInd = self.blobCollection[self.currentBlobs].blobRequest(globalPnt, radius)
        if added == True:
            if self.GUI is not None and self.GUI.showHist:
                self.GUI.toggleHistWindow()
            return "Adding blob at {}, {}".format(globalPnt[0], globalPnt[1])
        else:
            if self.GUI is not None and self.GUI.showHist:
                self.GUI.histCanvas.removeBlob(removeInd)
            return "Removed blob at {}, {}".format(globalPnt[0], globalPnt[1])

    def requestInstrumentMove(self, localPoint):
        '''
        Handles requests for moving the connected istrument
        localPoint: (x,y) tuple in the current image coordinate system
        returns a string summarizing the effect of the action
        '''
        #no slide is set up
        if self.slide is None:
            return "No slide loaded"

        #the connected instrument isn't initialized or present
        if self.coordinateMapper.connectedInstrument is None or \
            not self.coordinateMapper.connectedInstrument.connected:
            return "Instrument not connected"

        #perform actual movement
        pixelPnt = self.slide.getGlobalPoint(localPoint)
        if len(self.coordinateMapper.physPoints) >= 2:
            motorPnt = self.coordinateMapper.translate(pixelPnt)
            self.coordinateMapper.connectedInstrument.moveToPositionXY(motorPnt)
            return "Moving to {:.0f}, {:.0f}".format(motorPnt[0], motorPnt[1])
        #not enough registration points
        else:
            return "Not enough training points"