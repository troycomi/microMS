from __future__ import unicode_literals

import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
from copy import copy

from GUICanvases.mplCanvas import MplCanvas
from GUICanvases import GUIConstants

from ImageUtilities.blobFinder import blobFinder
from ImageUtilities.blobList import blobList

class HistCanvas(MplCanvas):
    '''
    HistCanvas is an implementation of MplCanvas that interacts with a slideCanvas 
    to display population level information on a collection of blob objects.
    Most of the control logic is contained here as the view is simply a bar chart
    '''
    def __init__(self, master, model, *args, **kwargs):
        '''
        Initialize and connect listeners
        master: the master widget, a microMSQT
        slideCanvas: the connected slideCanvas to interact with
        '''
        MplCanvas.__init__(self, *args, **kwargs)
        self.draw()
        #start by showing the blob areas
        self.populationMetric = 3
        self.populationValues = None
        self.blobSet = None
        #the image of the collection from slideWrapper to analyze
        self.imgInd = 1
        #toggle to move the slide position to the first single blob
        self.moveSlide = False
        
        #listeners for mouse interaction
        self.mpl_connect('button_release_event', self.mouseUp)
        self.mpl_connect('scroll_event', self.mouseZoom)
                                      
        self.master = master
        self.model = model
    
        #offset from blob radius to consider when extracting fluorescence
        self.offset = 0

        #x axis limits for zooming
        self.xlo = None
        self.xhi = None

        #toggle to indicate if the maximum or average intensity should be displayed
        self.reduceMax = False

        #a list of the currently available metrics
        self.metrics = ['Red', 'Green', 'Blue', 'Size', 'Circularity', 'Distance']

        #initialize display variables
        self.resetVariables()

    def resetVariables(self, resetZoom = True, resetBlobs = False):
        '''
        reset variables related to splitting the population and display
        resetZoom: reset the zoom on the x axis
        resetBlobs: reset the list of blobs curretly investigated
        '''
        #lowIntens and lowLimit hold thresholds for low values of the population
        #low blobs have I such that lowLimit < I < lowIntens
        self.lowIntens = None
        self.lowLimit = None
        #high blobs have I such that highIntens < I < highLimit
        self.highIntens = None
        self.highLimit = None
        #single bar is a value bin in the histogram
        self.singleBar = None
        #single blob contains the index of a single blob to show the position of in the histogram
        self.singleBlob = None

        if resetZoom:
            #zoom level on the x axis
            self.zoomLvl = 0
            #center of the x axis
            self.xcent = None        

        if resetBlobs:
            #the color channel or morphology
            self.populationMetric = 3
            #set of population values
            self.populationValues = None
            #the actual blob list
            self.blobSet = None

    def removeBlob(self, index):
        #return immediately if globalBlbs is not set
        if self.populationValues is None or self.populationValues.size < index:
            return

        self.populationValues = np.delete(self.populationValues, index)
        self._calculateHist(resetVars = False)

    def _calculateHist(self, resetVars = True):
        #return immediately if globalBlbs is not set
        if self.populationValues is None:
            self.update_figure()
            return

        #metric >= 3 -> look at morphology
        if self.populationMetric >= 3:
            self.counts, self.bins, patches = self.axes.hist(self.populationValues, bins = 100) 

        #metric == [0, 1, 2] -> look at intensities of [r, g, b] channel of image at imgInd
        else:
            self.counts, self.bins, patches = self.axes.hist(self.populationValues, bins=100, range=(0,255))

        self.bins = self.bins[1:]

        #reset limits and redraw
        if resetVars == True:
            self.resetVariables()  
        self.update_figure()



    def calculateHist(self):
        '''
        calculate the population values with either the current set of blobs from the model
        this can require some calculation time to complete due to repeated disk reads on the image
        '''
        #set a new set of global blbs
        self.blobSet = self.model.blobCollection[self.model.currentBlobs]

        #return immediately if globalBlbs is not set
        if self.blobSet is None or len(self.blobSet.blobs) == 0:
            self.populationValues = None
            self._calculateHist()
            return

        #metric == 3 -> look at the area (= pi * r^2)
        if self.populationMetric == 3:
            self.populationValues = np.array([x.radius*x.radius*3.14 for x in self.blobSet.blobs])

        #metric == 4 -> look at circularity
        elif self.populationMetric == 4:
            self.populationValues = np.array([x.circularity for x in self.blobSet.blobs])
            
        #metric == 5 -> look at minimum distance between samples
        elif self.populationMetric == 5:
            self.populationValues = np.array(self.blobSet.minimumDistances())
            
        #metric == [0, 1, 2] -> look at intensities of [r, g, b] channel of image at imgInd
        else:
            self.populationValues = np.array(self.model.slide.getFluorInt(self.blobSet.blobs, self.populationMetric, self.imgInd, self.offset, self.reduceMax))
            
        self._calculateHist()
    
    def mouseUp(self,event):
        '''
        handles click events by updating the high and low limits
        event: mpl mouse click event
        '''
        #click out of bounds
        if event.xdata is None or event.ydata is None or self.populationValues is None:
            return

        #LMB to set low values
        if event.button == 1:
            #shift LMB to set the lower limit
            if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                self.lowLimit = event.xdata
            #LMB to set a lower threshold
            else:
                self.lowIntens = event.xdata
            #display a message if a lower threshold is set
            if self.lowIntens is not None:    
                if self.lowLimit is not None:
                    self.master.statusBar().showMessage(str(sum((self.populationValues < self.lowIntens) & (self.populationValues > self.lowLimit))) 
                                                        + ' below {:.1f} and above {:.1f}'.format(self.lowIntens, self.lowLimit))
                else:
                    self.master.reportFromModel(str(sum(self.populationValues < self.lowIntens)) 
                                                        + ' below {:.1f}'.format(self.lowIntens))
        
        #MMB to select a single bin
        if event.button == 2:
            self.singleBar = event.xdata
            self.master.reportFromModel('Clicked on {:.1f}'.format(event.xdata))
            self.moveSlide = True
        
        #RMB to set high values
        if event.button == 3:
            #shift RMB to set the higher limit
            if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                self.highLimit = event.xdata

            #RMB to set the higher threshold
            else:
                self.highIntens = event.xdata

            #display message if a higher threshold is set
            if self.highIntens is not None:    
                if self.highLimit is not None:
                    self.master.statusBar().showMessage(str(sum((self.populationValues > self.highIntens) & (self.populationValues < self.highLimit)))
                                                        + ' above {:.1f} and below {:.1f}'.format(self.highIntens,self.highLimit))
                else:
                    self.master.statusBar().showMessage(str(sum(self.populationValues > self.highIntens)) 
                                                        + ' above {:.1f}'.format(self.highIntens))
        
        #redraw figure    
        self.update_figure()

    def mouseZoom(self,event):
        '''
        handle mouse scrolling by zooming in and out
        event: mpl mouse scroll event
        '''
        if self.populationValues is not None and event.xdata is not None:

            if event.button == 'up':
                self.zoomLvl += 1#zoom in
            else:
                self.zoomLvl -= 1#zoom out

            self.zoomLvl = 0 if self.zoomLvl < 0 else (10 if self.zoomLvl > 10 else self.zoomLvl)
            self.xcent = int(event.xdata)

            #redraw the zoom lvl
            self.redraw_zoom()
               
    def setBlobNum(self, target):
        '''
        automatically sets a high and low threshold to select 
        approximately the same number of blobs in each condition
        target: the target number of blobs to find
        '''
        #return when values not set
        if self.populationValues is None:
            return
        #subdivide the population by a larger factor
        counts, bins= np.histogram(self.populationValues, bins = 2560)

        #find lower cutoff, binary search
        left = 0
        right = len(counts)
        c = 0
        lowlimit = 0 if self.lowLimit is None else np.argmin(np.abs(bins - self.lowLimit))
        while left < right and c < 20:
            ind = (left + right) // 2
            tempCount = sum(counts[lowlimit:ind])
            if tempCount < target:
                left = ind +1
            elif tempCount > target:
                right = ind -1
            else:
                break
            c += 1
        self.lowIntens = bins[ind+1]
        tclow =   sum(counts[lowlimit:ind])      
        
        #find upper cutoff, binary search
        left = 0
        right = len(counts)
        c = 0
        highlimit = len(counts)-1 if self.highLimit is None else np.argmin(np.abs(bins - self.highLimit))
        while left < right and c < 20:
            ind = (left + right) // 2
            tempCount = sum(counts[ind:highlimit])
            if tempCount < target:
                right = ind -1
            elif tempCount > target:
                left = ind +1
            else:
                break
            c += 1
        self.highIntens = bins[ind-1]
        tchigh = sum(counts[ind:highlimit])
        self.update_figure()
        
        self.master.reportFromModel('Found ' + str(tclow) + ' below and ' + str(tchigh) + ' above')
        
    def clearFilt(self):
        '''
        Clear the current set of filter parameters and redraw figure
        '''
        self.resetVariables(False)
        self.update_figure();

    def savePopulationValues(self, filename):
        '''
        saves the mopulation values of the currently displayed histogram
        filename: text file to save
        '''
        if self.populationValues is None or len(self.populationValues) == 0:
            return 'Nothing to save'
        output = open(filename, 'w')
        output.write('Blob\t{}\n'.format(self.metrics[self.populationMetric]))
        for i,b in enumerate(self.model.blobCollection[self.model.currentBlobs].blobs):
            output.write('0_x_{0:.0f}y_{1:.0f}\t{2}\n'.format(b.X, b.Y, 
                                                              self.populationValues[i]))
        return 'Saved histogram values'

    def saveHistImage(self, filename):
        '''
        Saves the current histogram image
        filename: image file to write
        '''
        self.fig.savefig(filename, dpi = 1200)

    def getFilteredBlobs(self):
        '''
        Get the set of blobs which pass the current filters
        returns list of blobLists with the filters already set
        '''
        result = []
        #low intensity
        if self.lowIntens is not None:
            if self.lowLimit is not None:
                tempbool = (self.populationValues < self.lowIntens) & (self.populationValues > self.lowLimit)
            else:
                tempbool = self.populationValues < self.lowIntens

            lowblbs = [self.blobSet.blobs[i] for i in np.where(tempbool)[0]]
            result.append(self.blobSet.partialDeepCopy(lowblbs))
            result[-1].filters.append(self._getFilterDescription(self.lowLimit, self.lowIntens))
                
        #high intensity
        if self.highIntens is not None:
            if self.highLimit is not None:
                tempbool = (self.populationValues >  self.highIntens) & (self.populationValues < self.highLimit)
            else:
                tempbool = self.populationValues >  self.highIntens
                
            highblbs = [self.blobSet.blobs[i] for i in np.where(tempbool)[0]]
            result.append(self.blobSet.partialDeepCopy(highblbs))
            result[-1].filters.append(self._getFilterDescription(self.highIntens, self.highLimit))

        return result

    def _getFilterDescription(self, lowVal, highVal):
        '''
        returns a succienct string description of the current filter set
        lowVal: low value, part of # < channel < #
        highVal: high value, other part of # < channel < #
        '''
        result = ''
        if lowVal is None and highVal is None:
            return None

        channel = 'c{}[{}]'.format(self.imgInd, self.metrics[self.populationMetric])

        if lowVal is not None:
            result += "{:.1f}<".format(lowVal)
        result += channel
        if highVal is not None:
            result += "<{:.1f}".format(highVal)
        result += ';'

        result += 'max' if self.reduceMax else 'mean'
        result += ';offset={}'.format(self.offset)

        return result

    def redraw_zoom(self):
        '''
        redraw the widget after a zoom change, does not update the underlying graph
        '''
        #find range of the x axis scaled by zoom
        rng = (self.xhi - self.xlo) / 2**(self.zoomLvl+1)
        #determine center position
        if self.xcent is None:
            self.xcent = (self.xhi - self.xlo) / 2
        #find high and low positions, center +/- range
        (low, high) = (self.xcent - rng, self.xcent + rng)
        #keep low and high bounded by the min and max
        (low, high) = (self.xlo if low < self.xlo else low, self.xhi if high > self.xhi else high)
        #if no zoom, autoscale
        if self.zoomLvl == 0: 
            self.axes.autoscale(True, 'both')
        else:#autoscale y but use high and low for x
            self.axes.set_xlim([low,high]) 
            self.axes.autoscale(True, 'y')            

        self.draw()

    def update_figure(self):
        '''
        redraw the figure by recalculating the graph and recoloring
        The blob subsets are passed back to the model
        '''
        if self.populationValues is None:
            self.axes.cla()
        else:
            #draw bar chart of entire population
            self.axes.bar(self.bins, self.counts, width = self.bins[0] - self.bins[1], 
                          color = GUIConstants.BAR_COLORS[self.populationMetric])
            self.axes.hold(True)
            blbSubset = []
            blbColors = []
            #handle low intens
            if self.lowIntens is not None:
                if self.lowLimit is not None:
                    #tempbool is the bins that pass the filter
                    tempbool = (self.bins < self.lowIntens) & (self.bins > self.lowLimit)
                    #tempbool2 is the blobs that pass the filter
                    tempbool2 = (self.populationValues < self.lowIntens) & (self.populationValues > self.lowLimit)
                else:
                    tempbool = self.bins < self.lowIntens
                    tempbool2 = self.populationValues < self.lowIntens
                #draw the low threshold bars
                self.axes.bar(self.bins[tempbool], self.counts[tempbool], 
                              width = self.bins[0]-self.bins[1], color = GUIConstants.LOW_BAR)
                #add the low threshold blobs to the blob subset to pass to slideCanvas
                if np.any(tempbool2):
                    blbSubset.append(copy(self.blobSet))
                    blbSubset[-1].blobs = [self.blobSet.blobs[i] for i in np.where(tempbool2)[0]]
                    blbSubset[-1].description = 'low'
                    blbSubset[-1].threshCutoff = int(self.lowIntens)
                    blbColors.append(GUIConstants.LOW_BAR)
                
            #handle high intens
            if self.highIntens is not None:
                if self.highLimit is not None:
                    tempbool = (self.bins >  self.highIntens) & (self.bins < self.highLimit)
                    tempbool2 = (self.populationValues >  self.highIntens) & (self.populationValues < self.highLimit)
                else:
                    tempbool = self.bins >  self.highIntens
                    tempbool2 = self.populationValues >  self.highIntens
                #draw the high threshold bars
                self.axes.bar(self.bins[tempbool], self.counts[tempbool], 
                              width = self.bins[0]-self.bins[1], color = GUIConstants.HIGH_BAR)
                #add the high threshold blobs to the blob subset to pass to slideCanvas
                if np.any(tempbool2):
                    blbSubset.append(copy(self.blobSet))
                    blbSubset[-1].blobs = [self.blobSet.blobs[i] for i in np.where(tempbool2)[0]]
                    blbSubset[-1].color = GUIConstants.HIGH_BAR
                    blbSubset[-1].description = 'high'
                    blbSubset[-1].threshCutoff = int(self.highIntens)
                    blbColors.append(GUIConstants.HIGH_BAR)

            #handle single bar selected
            if self.singleBar is not None:
                temp = self.bins - self.singleBar
                ind = int(np.sum(temp < 0))
                ind = 0 if ind < 0 else len(self.bins)-1 if ind >= len(self.bins) else ind
                #draw the single bar
                self.axes.bar(self.bins[ind], self.counts[ind], 
                              width = self.bins[0]-self.bins[1], color = GUIConstants.SINGLE_BAR)
                #add the single bar blobs to the subset for slideCanvas
                tempbool = (self.populationValues < self.bins[ind])
                if ind == len(self.bins) -1:
                    tempbool = self.populationValues >= self.bins[ind-1]
                elif ind != 0:
                    tempbool = tempbool & (self.populationValues >= self.bins[ind-1])
                if np.any(tempbool):
                    blbSubset.append(copy(self.blobSet))
                    blbSubset[-1].blobs = [self.blobSet.blobs[i] for i in np.where(tempbool)[0]]
                    blbSubset[-1].description = 'single'
                    blbSubset[-1].threshCutoff = int(self.bins[ind])
                    if self.moveSlide == True:
                        firstBlob = blbSubset[-1].blobs[0]
                        self.model.slide.pos = [firstBlob.X, firstBlob.Y]
                        self.moveSlide = False
                    blbColors.append(GUIConstants.SINGLE_BAR)


            #draw lines displaying the values used for filtering
            #a single blob to highlight
            if self.singleBlob is not None:
                if self.singleBlob >= 0 and self.singleBlob < len(self.populationValues):
                    self.axes.vlines(self.populationValues[self.singleBlob], 0, 
                                     self.axes.get_ylim()[1], colors = GUIConstants.SINGLE_BLOB)
            #draw limits
            if self.lowLimit is not None:
                self.axes.vlines(self.lowLimit, 0, self.axes.get_ylim()[1], colors = GUIConstants.LOW_BAR, linestyles='dashed')
            if self.highLimit is not None:
                self.axes.vlines(self.highLimit, 0, self.axes.get_ylim()[1], colors = GUIConstants.HIGH_BAR, linestyles='dashed')
            
            #draw thresholds
            if self.lowIntens is not None:
                self.axes.vlines(self.lowIntens, 0, self.axes.get_ylim()[1], colors = GUIConstants.LOW_BAR, linestyles='dashdot')
            if self.highIntens is not None:
                self.axes.vlines(self.highIntens, 0, self.axes.get_ylim()[1], colors = GUIConstants.HIGH_BAR, linestyles='dashdot')

            #tell slide canvas about the new subset
            self.master.report_blbsubset((blbSubset, blbColors))

        self.axes.hold(False)
        #update the axes labels and x axis limits
        self.axes.set_ylabel('Count')
        if self.populationMetric == 3:
            self.axes.set_xlabel('Size (pixels)')
            self.xlo, self.xhi = self.axes.get_xlim()
        elif self.populationMetric == 4:
            self.axes.set_xlabel('Circularity')
            self.xlo, self.xhi = self.axes.get_xlim()
        elif self.populationMetric == 5:
            self.axes.set_xlabel('Distance (pixels)')
            self.xlo, self.xhi = self.axes.get_xlim()

        #colors are labeled as intensity and limited to 0,255 
        else:
            self.xlo, self.xhi = 0,255
            self.axes.set_xlabel('Intensity')

        self.redraw_zoom()
        