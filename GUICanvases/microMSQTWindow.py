from __future__ import unicode_literals
import os
from PyQt4 import QtGui, QtCore

from CoordinateMappers import supportedCoordSystems
from CoordinateMappers import connectedInstrument

from ImageUtilities.slideWrapper import SlideWrapper
from ImageUtilities import blobUtilities
from ImageUtilities.enumModule import Direction, StepSize

from GUICanvases.histCanvas import HistCanvas
from GUICanvases.slideCanvas import SlideCanvas
from GUICanvases.popup import blbPopupWindow, gridPopupWindow, histPopupWindow
from GUICanvases.microMSModel import MicroMSModel
from GUICanvases import GUIConstants

class MicroMSQTWindow(QtGui.QMainWindow):
    '''
    A QT implementation of the MicroMS window.
    Interacts with the MicroMSModel, a SlideCanvas and a HistCanvas
    Mainly handles the menu, key presses, and coordinating canvases
    '''
    def __init__(self):
        '''
        intialize a new microMSQT window, setting up the layout and some instance variables
        '''
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.main_widget = QtGui.QWidget(self)

        #model with slide and blob data
        self.model = MicroMSModel(self)

        self.layout = QtGui.QHBoxLayout(self.main_widget)

        #new slide canvas for displaying the image and handling mouse interactions.
        self.slideCanvas = SlideCanvas(self, self.model, self.main_widget, width=6, height=6, dpi=100)
        self.layout.addWidget(self.slideCanvas, stretch = 1)   
        
        #histogram canvas for showing and interacting with population level measurements
        self.histCanvas = HistCanvas(master=self, model=self.model, width=6, height=6, dpi=100)
        self.layout.addWidget(self.histCanvas, stretch = 1)
        self.histCanvas.hide()
        
        self.showHist = False

        self.fileName = None
        
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        self.setupMenu()

    def setupMenu(self):
        '''
        setup the menubar and connect instance functions
        '''
        #file menu
        self.file_menu = QtGui.QMenu('&File', self)
        
        #open button
        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.fileOpen)
        self.file_menu.addAction(openFile)
        
        #decimation submenu
        decSub = QtGui.QMenu('Decimate...',self)
        self.file_menu.addMenu(decSub)
        decSub.addAction('Single Image', self.decimateImageSingle)
        decSub.addAction('Image Group', self.decimateImageGroup)
        decSub.addAction('Directory', self.decimateDirectory)
        
        #instrument selection
        instSub = QtGui.QMenu('&Instrument...', self)
        self.file_menu.addMenu(instSub)
        self.instruments = QtGui.QActionGroup(self, exclusive=True)
        self.instruments.triggered.connect(self.mapperChanged)
        #populate with all instruments currently supported
        for s in supportedCoordSystems.supportedNames:
            a = self.instruments.addAction(QtGui.QAction(s, instSub, checkable=True))
            instSub.addAction(a)
        self.instruments.actions()[0].setChecked(True)
        
        #save submenu
        saveSub = QtGui.QMenu('&Save...',self)
        self.file_menu.addMenu(saveSub)
        
        saveSub.addAction('&Image', self.saveImg,
                          QtCore.Qt.CTRL + QtCore.Qt.Key_S)
        saveSub.addAction('&Whole Image', self.saveWholeImg)
        saveSub.addSeparator()
        saveSub.addAction('&All', self.saveAll)
        saveSub.addSeparator()
        saveSub.addAction('&Registration', self.saveReg)
        saveSub.addAction('&Current Cells', self.saveCurrentFind)
        saveSub.addAction('&Histogram Divisions', self.saveHistogramBlobs)
        saveSub.addAction('All Lists of Cells', self.saveAllBlobs)
        saveSub.addSeparator()

        saveSub.addAction('&Sample Positions', self.saveInstrumentPositions)
        saveSub.addAction('&Fiducial Positions', self.saveFiducialPositions)
        
        #load submenu
        loadSub = QtGui.QMenu('&Load...',self)
        self.file_menu.addMenu(loadSub)
        
        loadSub.addAction('&Registration', self.loadReg)
        loadSub.addAction('&Found Cells', self.loadCellFind)
        loadSub.addAction('&Sample Positions', self.loadInstrumentPositions)
        
        #quit button
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        #tools menu
        self.tools_menu = QtGui.QMenu('&Tools',self)

        #cell find
        self.tools_menu.addAction('&Cell Find', self.globalCell)
        #blob options
        self.tools_menu.addAction('&Blob Options',self.blbPopup,
                                  QtCore.Qt.CTRL + QtCore.Qt.Key_B)
        #tsp optimize toggle
        self.tspOpt = QtGui.QAction('TSP Optimize', self.tools_menu, checkable=True)
        self.tspOpt.setChecked(True)
        self.tools_menu.addAction(self.tspOpt)
        #limit drawn cells toggle
        self.limitDraw = QtGui.QAction('Limit Drawn Cells', self.tools_menu, checkable=True)
        self.limitDraw.setChecked(True)
        self.tools_menu.addAction(self.limitDraw)
        self.tools_menu.addSeparator()
        #Histogram options
        self.tools_menu.addAction('Histogram Window',self.showHistWindow,
                                  QtCore.Qt.CTRL + QtCore.Qt.Key_F)
        self.tools_menu.addAction('Histogram Options',self.histOptions)
        self.tools_menu.addAction('Pick Extremes',self.histSelect)
        self.tools_menu.addAction('Save Histogram Image',self.histSaveImage)
        self.tools_menu.addAction('Save Histogram Values',self.histSaveValues)
        self.tools_menu.addAction('Apply Filter',self.histFilter,
                                  QtCore.Qt.CTRL + QtCore.Qt.Key_A)
        #cell position options
        self.tools_menu.addSeparator()
        self.tools_menu.addAction('Distance Filter',self.distanceFilter)
        self.tools_menu.addAction('Rectangular Pack', self.rectPack)
        self.tools_menu.addAction('Hexagonal Pack', self.hexPack)
        self.tools_menu.addAction('Circular Pack', self.circPack)

        #instrument settings
        self.tools_menu.addSeparator()
        self.tools_menu.addAction('Instrument Setting',self.gridPopup,
                                  QtCore.Qt.CTRL + QtCore.Qt.Key_G)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.tools_menu)

        #device submenu
        self.inst_menu = QtGui.QMenu('Device', self)
        self.inst_menu.addAction('Establish Connection', self.initializeInstrument)
        self.inst_menu.addAction('Set Dwell Time', self.setDwell)
        self.inst_menu.addAction('Analyze All', self.analyzeAll)

        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.inst_menu)
        self.inst_menu.setEnabled(self.model.coordinateMapper.isConnectedToInstrument)

        #help menu
        self.help_menu = QtGui.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&Image Hotkeys', self.imgHotkeyMsg)
        self.help_menu.addAction('&Instrument Hotkeys', self.instHotkeyMsg)
        self.help_menu.addAction('&Histogram Hotkeys', self.histHotkeyMsg)

    ###most of the following functions are simple popups to parse input and pass to canvases
    def fileOpen(self, extras=None):
        '''
        open and setup a slide.  only ndpi and tif are supported
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getOpenFileName(
                self, 'Open File',
                filter='Slide Scans (*.ndpi *.tif)')  

        else:
            fileName = extras.fileName

        if fileName:
            self.setupCanvas(fileName)

    def decimateImageGroup(self, extras = None):
        '''
        decimate a tif file (to speed up zooming out) and open the file
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getOpenFileName(
                self, 'Open File to Decimate',
                filter='Slide Scans (*.tif)') 

        else:
            fileName = extras.fileName

        if fileName:
            SlideWrapper.generateDecimatedImgs(fileName)
            #open file once done
            self.setupCanvas(fileName)

    def decimateImageSingle(self, extras = None):
        '''
        decimate a single file and open the image group
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getOpenFileName(
                self, 'Open File to Decimate',
                filter='Slide Scans (*.tif)') 

        else:
            fileName = extras.fileName

        if fileName:
            (path, file) = os.path.split(fileName)
            SlideWrapper.generateDecimatedImage(path, file)
            #open file once done
            self.setupCanvas(fileName)

    def decimateDirectory(self, extras = None):
        '''
        decimate a tif file (to speed up zooming out) and open the file
        '''
        if extras is None or not hasattr(extras, 'directory'):
            directory = QtGui.QFileDialog.getExistingDirectory(self, 'Open Directory to Decimate')

        else:
            directory = extras.directory

        if directory:
            SlideWrapper.decimateDirectory(directory)

    def setupCanvas(self, fileName):
        '''
        opens the file specified by filename and sets up some instance variables
        '''
        self.model.setupMicroMS(fileName)
        self.statusBar().showMessage("Opened {}".format(fileName))
        self.directory = os.path.dirname(fileName)
        self.fileName = os.path.splitext(os.path.basename(fileName))[0]
        self.setWindowTitle('MicroMS: ' + self.fileName)
        self.showHist = False
        self.histCanvas.resetVariables(True, True)
        self.model.reportSize((float(self.slideCanvas.size().width()),
                               float(self.slideCanvas.size().height())))
        self.model.slide.resetView()
        self.slideCanvas.draw()

    def mapperChanged(self, action):
        '''
        action triggered by the mapper changing in the instrument submenu
        Changes the mapper of imagecanvas to the selected one and updates the device menu and canvas
        '''
        i = supportedCoordSystems.supportedNames.index(action.text())
        self.model.setCoordinateMapper(supportedCoordSystems.supportedMappers[i])
        self.inst_menu.setEnabled(self.model.coordinateMapper.isConnectedToInstrument)
        self.slideCanvas.draw()
        
    def saveImg(self, extras = None):
        '''
        save the image of the image canvas to the selected location
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                                                     "Select save file",
                                                     self.directory,
                                                     filter='*.png')

        else:
            fileName = extras.fileName

        if fileName:
            self.slideCanvas.savePlt(fileName)
            
    def saveWholeImg(self, extras = None):
        '''
        saves the entire image at the selected zoom to the selected location
        Can produce large images!!
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                                                     "Select save file",
                                                     self.directory,
                                                     filter='*.png')

        else:
            fileName = extras.fileName

        if fileName:
            self.model.saveEntirePlot(fileName)
            if extras is None or not hasattr(extras, 'fileName'):
                msg = QtGui.QMessageBox(self)
                msg.setText("Finished saving")
                msg.setWindowTitle("")
                msg.exec_()
            
    def saveAll(self, extras = None):
        '''
        saves files necessary for replicating the cell finding, specifically:
        -Cell finding file with pixel locations of spots and find parameters
        -Registration file with pixel to physical locations of fiducials
        '''
        if extras is None or not hasattr(extras, 'text'):
            text, ok = QtGui.QInputDialog.getText(self,'Save All', 
                                                      'Enter base filename:')

        else:
            text = extras.text
            ok = extras.ok

        if ok:
            self.statusBar().showMessage(
                self.model.saveCurrentBlobFinding(os.path.join(self.directory, text+"_find.txt"))
            )
            self.statusBar().showMessage(
                self.model.saveCoordinateMapper(os.path.join(self.directory, text+".msreg"))
            )

    def saveReg(self, extras = None):
        '''
        save just the msreg file
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                                                     "Select save file",
                                                     self.directory,
                                                     filter='*.msreg')

        else:
            fileName = extras.fileName

        if fileName:
            self.statusBar().showMessage(
                self.model.saveCoordinateMapper(fileName)
            )
    
    def saveCurrentFind(self, extras = None):
        '''
        save cell finding of the current blob list
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                                                     "Select save file",
                                                     self.directory,
                                                     filter='*.txt')
        else:
            fileName = extras.fileName

        if fileName:
            self.statusBar().showMessage(
                self.model.saveCurrentBlobFinding(fileName)
            )       

    def saveHistogramBlobs(self, extras = None):
        '''
        save cell finding of all histogram filters
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                                                     "Select save file",
                                                     self.directory,
                                                     filter='*.txt')
        else:
            fileName = extras.fileName

        if fileName:
            self.statusBar().showMessage(
                self.model.saveHistogramBlobs(fileName)
            )       

    def saveAllBlobs(self, extras = None):
        '''
        save cell finding of all blob lists
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                                                     "Select save file",
                                                     self.directory,
                                                     filter='*.txt')
        else:
            fileName = extras.fileName

        if fileName:
            self.statusBar().showMessage(
                self.model.saveAllBlobs(fileName)
            )   
        
    def saveInstrumentPositions(self, extras = None):
        '''
        save instrument-specific file for sample positions
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                                                 "Select save file",
                                                 self.directory,
                                                 filter='*' + self.model.currentInstrumentExtension())
        else:
            fileName = extras.fileName

        if fileName:
            if extras is None or not hasattr(extras, 'fileName'):
                text,ok = QtGui.QInputDialog.getText(self, "Input Required",  
                                                        "Input max number of spots  or OK for all " + str(self.model.currentBlobLength()) )
            else:
                ok = extras.ok
                text = extras.text
                                
            if ok and not text == '':
                maxnum = int(float(text))
            elif ok:
                maxnum = 0
            else:
                return
            self.statusBar().showMessage(
                self.model.saveInstrumentPositions(
                    fileName,
                    self.tspOpt.isChecked(),
                    maxnum)
            )
                 
    def saveFiducialPositions(self, extras = None):
        '''
        save instrument specific file for fiducial locations to check registration
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                            "Select save file",
                            self.directory,
                            filter='*' + self.model.currentInstrumentExtension())
        else:
            fileName = extras.fileName

        if fileName:
            self.statusBar().showMessage(
                self.model.saveInstrumentRegistrationPositions(fileName)    
            )

    def loadReg(self, extras = None):
        '''
        load a registration file
        sets the instrument and loads pixel and physical positions of fiducials
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getOpenFileName(
                self, 'Open File',
                self.directory,
                filter='*.msreg')  
        else:
            fileName = extras.fileName

        if fileName:
            message, index = self.model.loadCoordinateMapper(fileName)
            self.statusBar().showMessage(
                message
            )
            
            self.inst_menu.setEnabled(self.model.coordinateMapper.isConnectedToInstrument)
            self.instruments.actions()[index].setChecked(True)
            self.slideCanvas.draw()   
            
    def loadCellFind(self, extras = None):        
        '''
        load sample positions and cell finding parameters
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getOpenFileName(
                self, 'Open File',
                self.directory,
                filter='*.txt')  
        else:
            fileName = extras.fileName

        if fileName:
            self.statusBar().showMessage(
                self.model.loadBlobFinding(fileName)
            )
            if self.model.currentBlobLength() > GUIConstants.TSP_LIMIT:
                self.tspOpt.setChecked(False)
            self.slideCanvas.draw()   

            self.histCanvas.clearFilt()
                
    def loadInstrumentPositions(self, extras = None):        
        '''
        loads samples from an instrument file to display pixel positions
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getOpenFileName(
                self, 'Open File',
                self.directory,
                filter='*' + self.model.currentInstrumentExtension())  
        else:
            fileName = extras.fileName

        if fileName:
            self.statusBar().showMessage(
                self.model.loadInstrumentPositions(fileName)
                )
            self.tspOpt.setChecked(self.model.currentBlobLength() < GUIConstants.TSP_LIMIT)
            self.slideCanvas.draw()
            
    def fileQuit(self):
        '''
        quit through the file -> quit button
        '''
        self.close()
        
    def closeEvent(self, ce):
        '''
        print the filename of the image that was displayed prior to closing
        '''
        if self.model.coordinateMapper.isConnectedToInstrument == True  and\
            self.model.coordinateMapper.connectedInstrument.connected == True:
            self.model.coordinateMapper.connectedInstrument.homeAll()
        if self.fileName is not None:
            print("Exiting from file {}".format(self.fileName))
        
    def globalCell(self, extras = None):
        '''
        cell find over the entire slide area or ROI
        '''
        self.statusBar().showMessage('Starting cell finding')
        self.statusBar().showMessage(
            self.model.runGlobalBlobFind()    
        )
        if self.model.currentBlobLength() > GUIConstants.TSP_LIMIT:
            self.tspOpt.setChecked(False)
        self.saveAll(extras)
        self.slideCanvas.draw()
        
    def blbPopup(self):
        '''
        popup the blob finding parameters
        '''
        if self.model.blobFinder is not None:
            self.blbPop = blbPopupWindow(self.model.blobFinder, self)
            self.blbPop.exec_()

    def showHistWindow(self):   
        '''
        toggles the display of the histogram canvas and initializes the instance
        '''
        self.showHist = not self.showHist
        if self.showHist:
            self.histCanvas.show()
            self.histCanvas.calculateHist()
        else:
            self.histCanvas.hide()
            self.histCanvas.clearFilt()
            
    def histOptions(self):
        '''
        pops up a window to adjust histogram canvas display
        also resets the sample positions (globalBlbs)
        '''
        self.histOpt = histPopupWindow(self.histCanvas, self)
        self.histOpt.exec_()
                
    def histSelect(self, extras =  None):
        '''
        select the top and bottom X cells from the histogram
        '''
        if extras is None or not hasattr(extras, 'text'):
            text,ok = QtGui.QInputDialog.getText(self, "Input Required",  "Input number of highest and lowest intensity cells to find")
        else:
            text = extras.text
            ok = extras.ok
        if ok and not text == '':
            self.histCanvas.setCellNum(int(text))

    def histSaveImage(self, extras = None):
        '''
        Saves the current figure image as a png
        extras: optional extra parameters to bypass GUI input
        '''
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                            "Select image file to save",
                            self.directory,
                            filter='*.png')
        else:
            fileName = extras.fileName

        if fileName:
            self.statusBar().showMessage(
                self.histCanvas.saveHistImage(fileName)   
            )

    def histSaveValues(self, extras = None):
        '''
        Saves all the cell locations and values of the current histogram metric
        extras: optional data to bypass GUI display
        '''
        if self.showHist == False:
            return
        if extras is None or not hasattr(extras, 'fileName'):
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                            "Select save file",
                            self.directory,
                            filter='*.txt')
        else:
            fileName = extras.fileName

        if fileName:
            self.statusBar().showMessage(
                self.histCanvas.savePopulationValues(fileName)   
            )

    def histFilter(self):
        '''
        applies the filter to the histogram, updating the cell find positions to those matching the filter
        the filter is also recorded for writing the cell find file
        '''
        filt = self.histCanvas.getFilteredBlobs()
               
        if filt is not None:
            message = self.histCanvas.getFilterDescription()
            self.model.filters.append(message)
            oldBlbs = self.model.updateCurrentBlobs(filt)
            self.statusBar().showMessage(
                message + "; original set in list {}".format(oldBlbs+1))
            self.histCanvas.calculateHist()
            self.slideCanvas.draw()
        else:
            self.statusBar().showMessage('Invalid histogram filter')

    def distanceFilter(self, extras = None):
        '''
        Performs distance filter of the sample positions and updates histogram display
        '''
        if extras is None or not hasattr(extras, 'text'):
            text,ok = QtGui.QInputDialog.getText(self, "Input Required",  "Input distance filter in pixels")
        else:
            text = extras.text
            ok = extras.ok

        if ok and not text == '':
            self.statusBar().showMessage('Starting distance filter')
            self.statusBar().showMessage(
                self.model.distanceFilter(int(text))
            )
            if self.showHist:
                self.histCanvas.calculateHist()
            self.slideCanvas.draw()

    def rectPack(self, extras = None):
        '''
        expand each spot into a rectangularly packed grid
        Get the separation and number of layers from the user
        '''
        if self.model.currentBlobLength() > 0:
            
            if extras is None or not hasattr(extras, 'sep'):
                text,ok = QtGui.QInputDialog.getText(self, "Input Required",  "Input separation in pixels" )
                if ok: 
                    sep = int(text)
                else:
                    sep = 50
                
                text,ok = QtGui.QInputDialog.getText(self, "Input Required",  "Input number of layers" )
                if ok: 
                    layers = int(text)
                else:
                    layers = 1

                dynamicLayering = QtGui.QMessageBox.question(self, 'Input Required', 
                                                             'Adjust layering to blob size?',
                                                             QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

                if dynamicLayering == QtGui.QMessageBox.Yes:
                    dynamicLayering = True
                else:
                    dynamicLayering = False

            else:
                sep = extras.sep
                layers = extras.layers
                dynamicLayering = extras.dynamicLayering

            self.model.rectPackBlobs(sep, layers, dynamicLayering)
            self.slideCanvas.draw()

    def hexPack(self, extras = None):
        '''
        expand each spot into a hexagonally closed packed grid
        Get the separation and number of layers from the user
        '''
        if self.model.currentBlobLength() > 0:
            if extras is None or not hasattr(extras, 'sep'):
                text,ok = QtGui.QInputDialog.getText(self, "Input Required",  "Input separation in pixels" )
                if ok: 
                    sep = int(text)
                else:
                    sep = 50
                
                text,ok = QtGui.QInputDialog.getText(self, "Input Required",  "Input number of layers" )
                if ok: 
                    layers = int(text)
                else:
                    layers = 1

                dynamicLayering = QtGui.QMessageBox.question(self, 'Input Required', 
                                                             'Adjust layering to blob size?',
                                                             QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

                if dynamicLayering == QtGui.QMessageBox.Yes:
                    dynamicLayering = True
                else:
                    dynamicLayering = False

            else:
                sep = extras.sep
                layers = extras.layers
                dynamicLayering = extras.dynamicLayering

            self.model.hexPackBlobs(sep, layers, dynamicLayering)
            self.slideCanvas.draw()

    def circPack(self, extras = None):
        '''
        expand each spot into circularly spaced positions around the spot circumference
        get separation, max number of spots and offset from user
        '''
        if self.model.currentBlobLength() > 0:
            if extras is None or not hasattr(extras, 'sep'):
                text,ok = QtGui.QInputDialog.getText(self, "Input Required",  "Input minimum separation in pixels" )
                if ok: 
                    sep = int(text)
                else:
                    sep = 50
                
                text,ok = QtGui.QInputDialog.getText(self, "Input Required",  "Input max number of spots" )
                if ok: 
                    shots = int(text)
                else:
                    shots = 10
                                
                text,ok = QtGui.QInputDialog.getText(self, "Input Required",  "Input offset in pixels" )
                if ok: 
                    offset = int(text)
                else:
                    offset = 10

            else:
                sep = extras.sep
                shots = extras.shots
                offset = extras.offset

        self.model.circularPackBlobs(sep, shots, offset)
        self.slideCanvas.draw()
        
    def gridPopup(self):
        '''
        popup a window to edit the intermeidate map of the mapper instance
        '''
        self.gridPop = gridPopupWindow(self.model)
        self.gridPop.exec_()     
        
    def initializeInstrument(self, extras = None):
        '''
        Initialize instrument on the user specified COM port
        '''
        if extras is None or not hasattr(extras, 'text'):
            text,ok = QtGui.QInputDialog.getText(self, "Enter COM Port",  
                                                 "Connections at {}".format(self.model.coordinateMapper.connectedInstrument.findPorts())
                                                 )    
        else:
            text = extras.text
            ok = extras.ok        
                                                                        
        if ok: 
            try:
                self.model.coordinateMapper.connectedInstrument.initialize(text)
                self.statusBar().showMessage('Connected to {}'.format(text))
            except:
                self.statusBar().showMessage('Error connecting to {}'.format(text))

    def setDwell(self, extras = None):
        '''
        Set the dwell time for analysis with a connected instrument
        '''
        if extras is None or not hasattr(extras, 'text'):
            text,ok = QtGui.QInputDialog.getText(self, "Input Required",  
                                                 "Set dwell time (s)"
                                                 )   
        else:
            text = extras.text
            ok = extras.ok    

        if ok:
            try:
                self.model.coordinateMapper.connectedInstrument.dwellTime = float(text)
            except:
                self.statusBar().showMessage('Input error')    
    
    def analyzeAll(self):
        '''
        analyze all positions of the specified samples, acquire for time specified by dwell time
        '''
        self.statusBar().showMessage(
            self.model.analyzeAll()
            ) 

    def report_blbsubset(self, blbSubset):
        self.model.setBlobSubset(blbSubset)
        self.slideCanvas.draw()
        
    
    '''
    These are popup messages with the hotkeys defined in the included canvases
    '''
    def imgHotkeyMsg(self):
        msg = ("w,s,a,d\t\tMove\n"
        "W,S,A,D\tMove Farther\n"
        "q,e\t\tZoom out/in\n"
        "r\t\tReset view\n"
        "t\t\tSwitch views\n"
        "b\t\tTest cell find\n"
        "B\t\tSwitch to threshold view\n"
        "m\t\tMirror x axis\n"
        "p\t\tToggle predicted location\n"
        "o\t\tToggle drawn shapes\n"
        "O\t\tToggle drawing all cell lists\n"
        "C\t\tClear found cells\n"
        "c\t\tClear ROI\n\n"
        "#\t\tToggle channel\n"
        "Ctrl+#\t\tSet channel\n"
        "Alt+#\t\tSet manual cell list\n\n"
        "LMB\t\tMove to center\n"
        "LMB+Shift\tAdd/remove points\n"
        "LMB+Ctrl\tDraw ROI\n"
        "MMB\t\tGet pixel values\n"
        "RMB\t\tAdd slide coordinate\n"
        "RMB+Shift\tRemove slide coordinate\n"
        "Scroll\t\tZoom in/out")
        QtGui.QMessageBox.about(self,
                                "Hotkeys",
                                msg)
        
    def instHotkeyMsg(self):
        msg = ("i,k,j,l\t\tMove\n"
        "I,K,J,L\t\tMove Farther\n"
        "+,-\t\tMove probe up/down\n"
        "V\t\tSet probe position\n"
        "v\t\tToggle probe position\n"
        "h\t\tHome stage\n"
        "x\t\tSingle analysis\n\n"
        "LMB+Alt\tMove to spot\n"
        "RMB\t\tAdd coordinate\n"
        "RMB+Shift\tRemove coordinate\n"
        )
        QtGui.QMessageBox.about(self,
                                "Hotkeys",
                                msg)
        
    def histHotkeyMsg(self):
        msg = ("LMB\t\tSet lower threshold\n"
        "LMB+Shift\tSet lower cutoff\n"
        "MMB\t\tSet single bar\n"
        "RMB\t\tSet upper threshold\n"
        "RMB+Shift\tSet upper cutoff\n"
        "Scroll\t\tZoom in/out")
        QtGui.QMessageBox.about(self,
                                "Hotkeys",
                                msg)
                
    def keyPressEvent(self, event):
        '''
        key press event handler.  Key presses on parent GUI are forwarded here
        '''
        if self.model.slide is not None:
            shift = event.modifiers() & QtCore.Qt.ShiftModifier
            #move with wsad
            if shift and event.modifiers() & QtCore.Qt.ControlModifier:
                stepSize = StepSize.medium
            elif shift:
                stepSize = StepSize.large
            else:
                stepSize = StepSize.small
            if event.key() == QtCore.Qt.Key_A:
                self.model.reportSlideStep(Direction.left, stepSize)
            elif event.key() == QtCore.Qt.Key_D:
                self.model.reportSlideStep(Direction.right, stepSize)
            elif event.key() == QtCore.Qt.Key_W:
                self.model.reportSlideStep(Direction.up, stepSize)
            elif event.key() == QtCore.Qt.Key_S:
                self.model.reportSlideStep(Direction.down, stepSize)
    
            #zoom in and out
            elif event.key() == QtCore.Qt.Key_Q:
                self.model.slide.zoomOut()
            elif event.key() == QtCore.Qt.Key_E:
                self.model.slide.zoomIn()

            #reset view to top left corner
            elif event.key() == QtCore.Qt.Key_R:
                self.model.slide.resetView()

            #toggle display of target blob locations
            elif event.key() == QtCore.Qt.Key_O:
                if shift:
                    self.model.drawAllBlobs = not self.model.drawAllBlobs
                else:
                    self.model.showPatches= not self.model.showPatches
                
            #toggle between saved and global blobs.  This is set by hex or circ packing and distance filtering
            elif event.key() == QtCore.Qt.Key_Z and event.modifiers() & QtCore.Qt.ControlModifier:
                self.model.restoreSavedBlobs()
    
            #cycle between image channels with t or z
            elif event.key() == QtCore.Qt.Key_T or event.key() == QtCore.Qt.Key_Z:
                self.model.slide.switchType()
                
            #toggle display of predicted locations from mapper
            elif event.key() == QtCore.Qt.Key_P:   
                self.model.showPrediction = not self.model.showPrediction
            
            #toggle left/right mirror
            elif event.key() == QtCore.Qt.Key_M:                   
                self.model.mirrorImage = not self.model.mirrorImage          
                
            elif event.key() == QtCore.Qt.Key_B:
                #toggle threshold view
                if shift:
                    self.model.showThreshold = not self.model.showThreshold
                #perform cell finding on max zoom image
                else:
                    self.model.testBlobFind()    

            elif event.key() == QtCore.Qt.Key_C:
                ##clears all target positions
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    self.model.resetVariables()
                    self.histCanvas.resetVariables(True, True)
                #clears filters and ROI positions
                else:
                    self.model.ROI = []
                    self.histCanvas.clearFilt()
                
            keys = [QtCore.Qt.Key_1, QtCore.Qt.Key_2, QtCore.Qt.Key_3, 
                    QtCore.Qt.Key_4, QtCore.Qt.Key_5, QtCore.Qt.Key_6, 
                    QtCore.Qt.Key_7, QtCore.Qt.Key_8, QtCore.Qt.Key_9]
                
            #for each numeric key    
            for i,k in enumerate(keys):
                if event.key() == k:
                    #set global blobs to the multiblob specified
                    if event.modifiers() & QtCore.Qt.AltModifier:
                        self.model.setCurrentBlobs(i)
                        self.statusBar().showMessage('Picking cells into list #{}'.format(i+1))
                        if self.showHist:
                            self.histCanvas.calculateHist()
                    #switch to image channel i
                    elif event.modifiers() & QtCore.Qt.ControlModifier:
                        self.model.slide.switchToChannel(i)

                    #toggle image channel on and off
                    else:
                        self.model.slide.toggleChannel(i)
                    break
            mapper = self.model.coordinateMapper    
            if mapper.isConnectedToInstrument == True and \
                mapper.connectedInstrument.connected == True:

                #move instrument position with ikjl
                if event.key() == QtCore.Qt.Key_I:
                    mapper.connectedInstrument.move(
                        Direction.up,
                        stepSize)
                elif event.key() == QtCore.Qt.Key_K:
                    mapper.connectedInstrument.move(
                        Direction.down,
                        stepSize)
                elif event.key() == QtCore.Qt.Key_J:
                    mapper.connectedInstrument.move(
                        Direction.left,
                        stepSize)
                elif event.key() == QtCore.Qt.Key_L:
                    mapper.connectedInstrument.move(
                        Direction.right,
                        stepSize)

                elif event.key() == QtCore.Qt.Key_V:
                    #set probe position
                    if shift:
                        mapper.connectedInstrument.setProbePosition()

                    #toggle probe position
                    else:
                        mapper.connectedInstrument.toggleProbe()

                #perform single collection
                elif event.key() == QtCore.Qt.Key_X:
                    mapper.connectedInstrument.collect()

                #move probe up and down
                elif event.key() == QtCore.Qt.Key_Equal:
                    mapper.connectedInstrument.moveProbe(
                        Direction.up,
                        stepSize)
                elif event.key() == QtCore.Qt.Key_Minus:
                    mapper.connectedInstrument.moveProbe(
                        Direction.down,
                        stepSize)
                elif event.key() == QtCore.Qt.Key_Plus:
                    mapper.connectedInstrument.moveProbe(
                        Direction.up,
                        stepSize)
                elif event.key() == QtCore.Qt.Key_Underscore:
                    mapper.connectedInstrument.moveProbe(
                        Direction.down,
                        stepSize)

                #home all positions
                elif event.key() == QtCore.Qt.Key_H:
                    mapper.connectedInstrument.homeAll()

            self.slideCanvas.draw()
        else:
            #debug autoload
            if event.key() == QtCore.Qt.Key_D and event.modifiers() & QtCore.Qt.ControlModifier:
                self.debugLoad()
        
    def debugLoad(self):
        '''
        a debugging function that automatically sets up an example image and data set
        '''
        #check if debug data exists
        if os.path.isdir(GUIConstants.DEBUG_DIR):
            #image filename
            fileName = GUIConstants.DEBUG_IMG_FILE
            self.setupCanvas(fileName)
            #preset position and zoom level
            self.model.slide.pos = [30500, 30000]
            self.model.slide.lvl = 0
        
            #the blob finding file
            self.model.loadBlobFinding(GUIConstants.DEBUG_CELL_FIND)
            #the registration file
            self.model.loadCoordinateMapper(GUIConstants.DEBUG_REG_FILE)
            self.slideCanvas.draw()

    def reportFromModel(self, message = "", redrawSlide = False, redrawHist = False):
        '''
        Method for the model to interact with the GUI and windows.
        Displays the supplied message and redraws selected canvases
        message: String message to display
        redrawSlide: boolean to dictate if slideCanavas should be redrawn
        redrawHist: boolean to dictate if histCanavas should be redrawn
        '''
        self.statusBar().showMessage(message)
        if redrawSlide:
            self.slideCanvas.draw()
        if redrawHist and self.showHist:
            self.histCanvas.update_figure()

    def requestFiducialInput(self, defaultStr):
        '''
        Method for microMSModel to recieve input from the user
        defaultStr: the string to initially display to the user
        '''
        return QtGui.QInputDialog.getText(self,'Coordinate Dialog', 
                                                    'Enter plate coordinate:',
                                                    text=defaultStr)
