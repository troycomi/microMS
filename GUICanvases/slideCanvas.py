from __future__ import unicode_literals

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor

import numpy as np
import random
import os

import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from PIL import ImageDraw, ImageFont, Image

from GUICanvases.mplCanvas import MplCanvas
from GUICanvases import GUIConstants
from ImageUtilities import blobFinder
from ImageUtilities import TSPutil
from ImageUtilities import blob

from CoordinateMappers import supportedCoordSystems
from CoordinateMappers import connectedInstrument

class SlideCanvas(MplCanvas):
    '''
    A QWidget for displaying and interfacing slide images
    This also has quite a bit of control code
    '''
    def __init__(self, master, model, *args, **kwargs):
        '''
        initialize a new instance of a slide canvas
        sets up several instance variables and default display settings
        model: the microMSModel shared with the window GUI
        '''
        MplCanvas.__init__(self, *args, **kwargs)

        #modify display defualts
        self.axes.xaxis.set_visible(False)
        self.axes.yaxis.set_visible(False)
        self.axes.set_axis_bgcolor(GUIConstants.IMAGE_BACKGROUND)
        self.setCursor(QCursor(Qt.CrossCursor))

        #temporary image for drawing rectangles, circles, etc quickly
        self.tempIm = None
        
        #variables related to mouse actions
        self.mDown = False          #mouse button pressed down for drawing a square ROI
        self.startP = None          #starting position of a mouse drag
        self.endP = None            #end position of a mouse drag
        self.mDownCirc = False      #mouse down for drawing a global blob
        self.mMoveCirc = False      #mouse moved while drawing a global blob
        self.mMoveROI = False       #mouse moved while drawing ROI with control alt

        self.model = model
        self.master = master

        #connect mouse events
        self.mpl_connect('button_release_event', self.mouseUp)
        self.mpl_connect('button_press_event', self.mouseDown)
        self.mpl_connect('motion_notify_event', self.mouseMove)
        self.mpl_connect('scroll_event', self.mouseZoom)

    def compute_initial_figure(self):
        '''
        Draw the intitial image shown before anything is loaded.
        Shows a high res version of the icon image
        '''
        tdir,f = os.path.split(__file__)
        icon = Image.open(os.path.join(tdir, 'Icon', 'icon.png'))
        self.axes.imshow(icon)

    def draw(self):
        '''
        redraw canvas with markups using current settings
        '''
        if self.mMoveROI == True:
            return#redrawROI handles redraws here
        if self.model.slide is not None:
            #reset size as needed
            self.model.reportSize((float(self.size().width()), float(self.size().height())))

            #get base image from slideWrapper and show
            self.tempIm = self.model.getCurrentImage()
            self.axes.imshow(self.tempIm)

            #add on the blobs, predicted coordinates, and fiducial set
            self.axes.add_collection(self.model.getPatches(self.master.limitDraw.isChecked()))
            #the text labels can't be patches, have to pass in the axes object to draw
            self.model.drawLabels(self.axes)
                        
        #mirror left/right as needed
        if self.model.mirrorImage:
            self.axes.invert_xaxis()
        super().draw()
            
    def mouseUp(self,event, extras = None):
        '''
        handles mouse events when the user releases
        event: an mpl mouse event
        '''
        if event.xdata is None or event.ydata is None:
            return

        if self.model.slide is None:
            return

        if extras is not None and hasattr(extras, 'modifiers'):
            modifiers = extras.modifiers
        else:
            modifiers = QtWidgets.QApplication.keyboardModifiers()

        #left mouse button click without dragging 
        #generally handles image movement and interaction with target locations
        if(event.button == 1 and not self.mDown):
            #remove or add global blob with shift click
            if modifiers == QtCore.Qt.ShiftModifier:

                #check if gobal blbs exists, if any points are within click
                globalPnt = self.model.slide.getGlobalPoint((event.xdata, event.ydata))
                
                #if shift click and drag, add blob with specified radius
                if self.mDownCirc and self.mMoveCirc:
                    rad = np.sqrt((globalPnt[0]-self.startPC[0])**2 + (globalPnt[1]-self.startPC[1])**2)
                    #minimum size of default radius pixels
                    rad = GUIConstants.DEFAULT_RADIUS if \
                        rad < GUIConstants.DEFAULT_RADIUS else rad 

                #just a shift click
                else:
                    rad = GUIConstants.DEFAULT_RADIUS

                #reset manual drawing flags
                self.mDownCirc = False
                self.mMoveCirc = False

                self.master.reportFromModel(
                    self.model.reportBlobRequest((event.xdata, event.ydata), radius = rad)
                   )

            #control + alt + LMB to add ROI point
            elif modifiers & QtCore.Qt.AltModifier and \
                modifiers & QtCore.Qt.ControlModifier:
                self.model.reportROI(self.model.slide.getGlobalPoint(
                                    (event.xdata, event.ydata)))

            #control + shift + LMB to append ROI point
            elif modifiers & QtCore.Qt.ShiftModifier and \
                modifiers & QtCore.Qt.ControlModifier:
                self.model.reportROI(self.model.slide.getGlobalPoint(
                                    (event.xdata, event.ydata)),
                                     append = True)

            #alt + LMB to move connected instrument to specified position
            elif modifiers == QtCore.Qt.AltModifier:
                self.master.reportFromModel(
                    self.model.requestInstrumentMove((event.xdata, event.ydata))
                    )

            #plain LMB moves the image center to the mouse position
            else:
                self.model.slide.moveCenter((event.xdata, event.ydata))

        #right button to interact with fiducial registration
        elif(event.button == 3):
            self.master.reportFromModel(
                self.model.reportFiducialRequest((event.xdata, event.ydata),
                                             removePoint = modifiers == QtCore.Qt.ShiftModifier,
                                             extras = extras)
                )

        #middle mouse button to get information on mouse position
        elif(event.button == 2):
            self.master.reportFromModel(
                self.model.reportInfoRequest((event.xdata, event.ydata)),
                redrawHist = self.master.showHist
                )

        #mouse was dragged to draw an ROI
        if(self.mDown):
            #convert two point to a 4point rectangle
            p1 = self.model.slide.getGlobalPoint((event.xdata, event.ydata))
            p2 = self.model.slide.getGlobalPoint(self.ROI)
            xlow, ylow = min(p1[0], p2[0]), min(p1[1], p2[1])
            xhigh, yhigh = max(p1[0], p2[0]), max(p1[1], p2[1])
            self.model.blobCollection[self.model.currentBlobs].ROI = [ (xlow, ylow),
                                                                      (xlow, yhigh),
                                                                      (xhigh, yhigh),
                                                                      (xhigh, ylow)]

            self.mDown = False                                                                                             
        self.draw()
        
    def mouseDown(self, event, extras = None):
        '''
        mouseDown sets variables for drawing ROIs or target positions with variable radii
        event: an mpl mouse down event
        '''
        if event.xdata is None or event.ydata is None:
            return
        
        if self.model.slide is None:
            return

        if extras is not None and hasattr(extras, 'modifiers'):
            modifiers = extras.modifiers
        else:
            modifiers = QtWidgets.QApplication.keyboardModifiers()

        #ROI drawing
        if event.button == 1 and \
            modifiers == QtCore.Qt.ControlModifier:
            self.mDown = True
            self.ROI = (event.xdata, event.ydata)

        #target drawing
        elif event.button == 1 and \
            modifiers == QtCore.Qt.ShiftModifier:
            self.mDownCirc = True
            self.startPC = self.model.slide.getGlobalPoint((event.xdata, event.ydata))
    
    def mouseMove(self,event, extras = None):
        '''
        mouse moves redraw ROI or blob positions as appropriate
        event: an mpl mouse move event
        '''
        if event.xdata is None or event.ydata is None:
            return

        if self.model.slide is None:
            return

        #ROI movement

        if extras is not None and hasattr(extras, 'modifiers'):
            modifiers = extras.modifiers
        else:
            modifiers = QtWidgets.QApplication.keyboardModifiers()

        if self.mDown == True:
            self.redrawRect((event.xdata, event.ydata))

        elif modifiers & QtCore.Qt.AltModifier and \
                modifiers & QtCore.Qt.ControlModifier:
            self.redrawROI((event.xdata, event.ydata))
            self.mMoveROI = True

        elif modifiers & QtCore.Qt.ShiftModifier and \
                modifiers & QtCore.Qt.ControlModifier:
            self.redrawROI((event.xdata, event.ydata), append = True)
            self.mMoveROI = True

        elif self.mMoveROI == True:
            self.mMoveROI = False
            self.draw()


        #target drawing
        elif self.mDownCirc == True:
            self.redrawCirc((event.xdata, event.ydata))
            self.mMoveCirc = True

    def mouseZoom(self,event):
        '''
        handle scroll wheel movement, which zooms the slide in and out
        event: an mple mouse wheel event
        '''
        if event.xdata is None or event.ydata is None:
            return
        
        if self.model.slide is None:
            return

        #zoom in or out
        if event.button == 'up':
            self.model.slide.zoomIn()
            self.model.slide.moveCenter((event.xdata, event.ydata))
        else:
            self.model.slide.zoomOut()

        #reset temporary blobs and update
        self.draw()

    def redrawROI(self, pnt, append = False):
        '''
        helper method to draw ROI polygon during mouse movement
        pnt: the current point in local (image) coordinates
        '''
        if self.tempIm is not None:
            self.axes.imshow(self.tempIm)
            roi = self.model.getROIPatches(self.model.slide.getGlobalPoint(pnt), append)
            self.axes.add_collection(PatchCollection(roi, match_original=(len(roi) != 0)))
            if self.model.mirrorImage:
                self.axes.invert_xaxis()
            super().draw() 

    def redrawRect(self, pnt):
        '''
        helper method to draw the yellow ROI rectangle during mouse movement
        pnt: the current point in local (image) coordinates
        '''
        if self.tempIm is not None:
            tempStartP = self.ROI
            self.axes.imshow(self.tempIm)
            lowerL = ((min(tempStartP[0], pnt[0]), 
                              min(tempStartP[1], pnt[1])))
            x = abs(tempStartP[0]- pnt[0])   
            y = abs(tempStartP[1]- pnt[1])                               
            r = plt.Rectangle(lowerL, x, y, color=GUIConstants.ROI, fill=False)
            self.axes.add_patch(r)        
            if self.model.mirrorImage:
                self.axes.invert_xaxis()
            super().draw() 
        
    def redrawCirc(self, pnt):
        '''
        helper method to draw the green circle for manually added blobs
        pnt: the current mouse position in local (image) coordinates
        '''
        if self.tempIm is not None:
            tempStartP = self.model.slide.getLocalPoint(self.startPC)
            self.axes.imshow(self.tempIm)
            rad = np.sqrt((tempStartP[0]-pnt[0])**2 + (tempStartP[1]-pnt[1])**2)
                  
            c = plt.Circle(pnt, rad,
                           color=GUIConstants.MULTI_BLOB[self.model.currentBlobs], 
                           linewidth=1,
                           fill=False)
            self.axes.add_patch(c)  
            if self.model.mirrorImage:
                self.axes.invert_xaxis()
            super().draw()        
     
    def savePlt(self, fileName):
        '''
        saves the current figure
        fileName: the file to write to
        '''
        self.fig.savefig(fileName, dpi = 1200)
            