import unittest
import os
import tempfile
import random
import sys

import PIL
from PIL import ImageDraw, Image
import openslide

from CoordinateMappers import supportedCoordSystems
from CoordinateMappers.ultraflexMapper import ultraflexMapper
from CoordinateMappers import zaberMapper

from GUICanvases.microMSModel import MicroMSModel
from GUICanvases.microMSQTWindow import MicroMSQTWindow
from GUICanvases.popup import blbPopupWindow, gridPopupWindow, histPopupWindow
from GUICanvases.histCanvas import HistCanvas
from GUICanvases import GUIConstants

from ImageUtilities.blob import blob
from ImageUtilities import blobFinder
from ImageUtilities import slideWrapper

from PyQt4 import QtGui
from PyQt4.QtGui import QWheelEvent
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt, QPoint

import matplotlib as mpl

from UnitTests import constants

app = QtGui.QApplication(sys.argv)

#class for passing extras to overloaded methods
class Extras:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

class test_microMSModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tiffImg1 = constants.tiffImg1
        cls.tiffImg1Reg = constants.tiffImg1Reg
        cls.tiffImg2 = constants.tiffImg2
        cls.ndpiImg1 = constants.ndpiImg1
        cls.ndpiImg2 = constants.ndpiImg2

        cls.singleNdpi = constants.singleNdpi
        cls.tiffMissC1 = constants.tiffMissC1

        cls.failImg = constants.failImg
        
        cls.noDecTif = constants.noDecTif
        cls.multiTif = constants.multiTif
        cls.smallTif = constants.smallTif
        cls.noCTif = constants.noCTif

    def test_init(self):
        model = MicroMSModel(None)
        self.assertIsNone(model.slide)
        self.assertIsNone(model.blobFinder)
        self.assertTrue(model.showPatches)
        self.assertFalse(model.mirrorImage)

        model.setupMicroMS(self.tiffImg1)
        model.showPatches = False
        model.mirrorImage = True
        self.assertFalse(model.showPatches)
        self.assertTrue(model.mirrorImage)
        self.assertIsNotNone(model.slide)
        self.assertIsNotNone(model.blobFinder)

        model.setupMicroMS(self.ndpiImg1)
        self.assertIsNotNone(model.slide)
        self.assertIsNotNone(model.blobFinder)
        self.assertTrue(model.showPatches)
        self.assertFalse(model.mirrorImage)

    def test_setCoordinateMapper(self):
        model = MicroMSModel(None)
        self.assertEqual(model.coordinateMapper, supportedCoordSystems.supportedMappers[0])
        model.setCoordinateMapper(supportedCoordSystems.supportedMappers[1])
        self.assertEqual(model.coordinateMapper, supportedCoordSystems.supportedMappers[1])
        model.coordinateMapper.addPoints((0,0), (100,100))
        self.assertEqual(len(model.coordinateMapper.physPoints), 1)
        model.setCoordinateMapper(supportedCoordSystems.supportedMappers[2])
        self.assertEqual(model.coordinateMapper, supportedCoordSystems.supportedMappers[2])
        model.setCoordinateMapper(supportedCoordSystems.supportedMappers[1])
        self.assertEqual(len(model.coordinateMapper.physPoints), 0)

    def test_saveEntirePlot(self):
        model = MicroMSModel(None)
        model.setupMicroMS(self.noCTif)
        model.slide.zoomOut()
        model.slide.zoomOut()
        model.slide.zoomOut()
        tdir = tempfile.TemporaryDirectory()
        fn = os.path.join(tdir.name, 'image.tif')
        model.saveEntirePlot(fn)
        blbs = model.blobCollection[0]
        for i in range(100):
            blbs.append(blob(random.uniform(0, 1000), random.uniform(0,1000)))
        model.saveEntirePlot(fn)
        for i,blbs in enumerate(model.blobCollection):
            if i % 2 == 0:
                for j in range(100):
                    blbs.append(blob(random.uniform(0, 1000), random.uniform(0,1000)))
            else:
                for j in range(100):
                    blbs.append(blob(random.uniform(j//10*10, j//10*10 + 10), random.uniform(j//10*10, j//10*10+10),group = j//10))
        model.saveEntirePlot(fn)

    def test_saveCurrentBlobFinding(self):
        model = MicroMSModel(None)
        tdir = tempfile.TemporaryDirectory()
        fn = os.path.join(tdir.name, 'cells.txt')

        self.assertEqual(model.saveCurrentBlobFinding(fn),
                         "No slide loaded")

        model.setupMicroMS(self.tiffImg1)
        self.assertEqual(model.saveCurrentBlobFinding(fn),
                         "List 1 contains no blobs!")
        model.blobCollection[model.currentBlobs].append(blob())
        self.assertEqual(model.saveCurrentBlobFinding(fn),
                         "Saved blob information")
        model.setCurrentBlobs(1)
        self.assertEqual(model.saveCurrentBlobFinding(fn),
                         "List 2 contains no blobs!")

    def test_saveHistogramBlobs(self):
        model = MicroMSModel(None)
        tdir = tempfile.TemporaryDirectory()
        fn = os.path.join(tdir.name, 'cells.txt')

        self.assertEqual(model.saveHistogramBlobs(fn),
                         "No slide loaded")
        model.setupMicroMS(self.ndpiImg1)

        self.assertEqual(model.saveHistogramBlobs(fn),
                         "No histogram divisions provided")

    def test_saveAllBlobs(self):
        model = MicroMSModel(None)
        tdir = tempfile.TemporaryDirectory()
        fn = os.path.join(tdir.name, 'cells.txt')

        self.assertEqual(model.saveAllBlobs(fn),
                         "No slide loaded")
        model.setupMicroMS(self.ndpiImg1)
        #this will actually not crash, but will not write any files
        self.assertEqual(model.saveAllBlobs(fn),
                         "Saved blobs with base name 'cells'")
        model.blobCollection[0].append(blob())
        model.blobCollection[3].append(blob())
        self.assertEqual(model.saveAllBlobs(fn),
                         "Saved blobs with base name 'cells'")

    def test_saveCoordinateMaper(self):
        model = MicroMSModel(None)
        tdir = tempfile.TemporaryDirectory()
        fn = os.path.join(tdir.name, 'test.msreg')

        self.assertEqual(model.saveCoordinateMapper(fn),
                         "No coordinates to save")
        model.coordinateMapper.addPoints((0,0), (0,0))
        self.assertEqual(model.saveCoordinateMapper(fn),
                         "Saved coordinate mapper")

    def test_saveInstrumentPositions(self):
        model = MicroMSModel(None)
        tdir = tempfile.TemporaryDirectory()
        fn = os.path.join(tdir.name, 'test.txt')

        self.assertEqual(model.saveInstrumentPositions(fn, False),
                         "Not enough training points to save instrument file")

        #the coordinates aren't inverted, so an identity is good here
        model.setCoordinateMapper(zaberMapper.zaberMapper())
        model.coordinateMapper.addPoints((0,0), (0,0))
        model.coordinateMapper.addPoints((1,0), (1,0))
        model.coordinateMapper.addPoints((0,1), (0,1))

        self.assertEqual(model.saveInstrumentPositions(fn, False),
                         "No blobs to save")

        for i in range(40):
            model.blobCollection[0].append(blob(random.uniform(0, 100), random.uniform(0,200)))

        for i in range(40):
            model.blobCollection[1].append(blob(random.uniform(0, 100), random.uniform(0,200)))
            
        self.assertEqual(model.saveInstrumentPositions(fn, False),
                         "Saved instrument file of list 1")
        model.currentBlobs = 1
        self.assertEqual(model.saveInstrumentPositions(fn, False),
                         "Saved instrument file of list 2")
        #with tsp
        self.assertEqual(model.saveInstrumentPositions(fn, True),
                         "Saved instrument file of list 2")
        #with only 10 points
        self.assertEqual(model.saveInstrumentPositions(fn, False, 10),
                         "Saved instrument file of list 2")
        #with only 100 points (should default to all 40
        self.assertEqual(model.saveInstrumentPositions(fn, False, 100),
                         "Saved instrument file of list 2")

    def test_saveInstrumentRegistrationPositions(self):
        model = MicroMSModel(None)
        tdir = tempfile.TemporaryDirectory()
        fn = os.path.join(tdir.name, 'test.txt')

        self.assertEqual(model.saveInstrumentRegistrationPositions(fn),
                         "Not enough training points to save fiducial locations")

        #the coordinates aren't inverted, so an identity is good here
        model.setCoordinateMapper(zaberMapper.zaberMapper())
        model.coordinateMapper.addPoints((0,0), (0,0))
        model.coordinateMapper.addPoints((1,0), (1,0))
        model.coordinateMapper.addPoints((0,1), (0,1))

        self.assertEqual(model.saveInstrumentRegistrationPositions(fn),
                         "Saved instrument registration positions")

    def test_loadCoordinateMapper(self):
        model = MicroMSModel(None)

        tempDir, f = os.path.split(__file__)
        fname = os.path.join(tempDir, 'test.msreg')
        tmapper = ultraflexMapper()
        tmapper.instrumentName = 'failure'
        tmapper.addPoints((0,0), (0,0))
        tmapper.saveRegistration(fname)

        self.assertEqual(model.loadCoordinateMapper(fname),
                         ('Unsupported instrument: failure', 0))

        model.coordinateMapper.addPoints((0,0), (0,0))
        self.assertEqual(len(model.coordinateMapper.physPoints), 1)
        model.coordinateMapper.saveRegistration(fname)
        name = model.coordinateMapper.instrumentName

        self.assertEqual(model.loadCoordinateMapper(fname),
                         ('Loaded {} registration'.format(name), 0))

        model.setCoordinateMapper(supportedCoordSystems.supportedMappers[1])
        self.assertEqual(model.loadCoordinateMapper(fname),
                         ('Warning, changing instrument to {}'.format(name), 0))

        os.remove(fname)

    def test_loadInstrumentPositions(self):
        model = MicroMSModel(None)

        tempDir, f = os.path.split(__file__)
        fname = os.path.join(tempDir, 'test.xeo')

        #zaber mapper for easy registration
        model.setCoordinateMapper(supportedCoordSystems.supportedMappers[4])

        model.coordinateMapper.addPoints((0,0), (0,0))
        model.coordinateMapper.addPoints((1,0), (1,0))
        model.coordinateMapper.addPoints((1,1), (1,1))

        for i in range(100):
            model.blobCollection[0].append(blob(i, i*2, group = i // 10))

        model.saveInstrumentPositions(fname, False)
        model.currentBlobs = 1

        self.assertEqual(model.loadInstrumentPositions(fname),
                         "Finished loading instrument file")

        for i in range(100):
            self.assertEqual(model.blobCollection[0][i].X, model.blobCollection[1][i].X)
            self.assertEqual(model.blobCollection[0][i].Y, model.blobCollection[1][i].Y)
            self.assertEqual(model.blobCollection[0][i].group, model.blobCollection[1][i].group)

        os.remove(fname)

    def test_currentInstrumentExtension(self):
        model = MicroMSModel(None)

        for c in supportedCoordSystems.supportedMappers:
            model.setCoordinateMapper(c)
            self.assertEqual(model.currentInstrumentExtension(),
                             model.coordinateMapper.instrumentExtension)

    def test_runGlobalBlobFind(self):
        model = MicroMSModel(None)

        self.assertEqual(model.runGlobalBlobFind(),
                         "No slide was open")

        model.setupMicroMS(self.smallTif)
        self.assertEqual(model.runGlobalBlobFind(),
                         "Finished blob finding on whole slide")

        model.ROI.append((10,0))
        model.ROI.append((100,200))
        self.assertEqual(model.runGlobalBlobFind(),
                         "Finished blob finding in ROI")

    def test_updateBlobs(self):
        model = MicroMSModel(None)
        blbs1 = []
        blbs2 = []
        blbs3 = []
        for i in range(100):
            blbs1.append(blob(random.uniform(0,100), random.uniform(0,100)))
            blbs2.append(blob(random.uniform(0,100), random.uniform(0,100)))
            blbs3.append(blob(random.uniform(0,100), random.uniform(0,100)))

        for i in range(9):
            self.assertEqual(len(model.blobCollection[i]), 0)

        model.updateCurrentBlobs(blbs1)
        
        for i in range(1, 9):
            self.assertEqual(len(model.blobCollection[i]), 0)

        for i in range(100):
            self.assertEqual(blbs1[i], model.blobCollection[0][i])

        model.updateCurrentBlobs(blbs2)
        for i in range(2, 9):
            self.assertEqual(len(model.blobCollection[i]), 0)

        for i in range(100):
            self.assertEqual(blbs1[i], model.blobCollection[1][i])
            self.assertEqual(blbs2[i], model.blobCollection[0][i])

        model.updateCurrentBlobs(blbs3)
        for i in range(3, 9):
            self.assertEqual(len(model.blobCollection[i]), 0)

        for i in range(100):
            self.assertEqual(blbs1[i], model.blobCollection[1][i])
            self.assertEqual(blbs2[i], model.blobCollection[2][i])
            self.assertEqual(blbs3[i], model.blobCollection[0][i])

    def test_restoreSavedBlobs(self):
        model = MicroMSModel(None)

        model.restoreSavedBlobs()
        blbs1 = []
        for i in range(100):
            blbs1.append(blob(random.uniform(0,100), random.uniform(0,100)))

        model.updateCurrentBlobs(blbs1)
        for i in range(100):
            self.assertEqual(blbs1[i], model.blobCollection[0][i])
        self.assertEqual([], model.savedBlobs)

        model.restoreSavedBlobs()
        for i in range(100):
            self.assertEqual(blbs1[i], model.savedBlobs[i])
        self.assertEqual([], model.blobCollection[0])

        
        model.restoreSavedBlobs()
        for i in range(100):
            self.assertEqual(blbs1[i], model.blobCollection[0][i])
        self.assertEqual([], model.savedBlobs)

    def test_distanceFilter(self):
        model = MicroMSModel(None)
        self.assertEqual(model.distanceFilter(5),
                         "No blobs to filter")

        blbs1 = []
        
        blbs1.append(blob(random.uniform(0,100), random.uniform(0,100)))
        model.updateCurrentBlobs(blbs1)
        self.assertEqual(model.distanceFilter(5),
                         "Finished distance filter")

        for i in range(100):
            blbs1.append(blob(random.uniform(0,100), random.uniform(0,100)))

        model.updateCurrentBlobs(blbs1)
        self.assertEqual(model.distanceFilter(5),
                         "Finished distance filter")

    def test_hexPackBlobs(self):
        model = MicroMSModel(None)
        model.hexPackBlobs(5, 1)

        blbs1 = []
        for i in range(100):
            blbs1.append(blob(random.uniform(0,100), random.uniform(0,100)))
        model.updateCurrentBlobs(blbs1)
        model.hexPackBlobs(5, 1)

    def test_rectPackBlobs(self):
        model = MicroMSModel(None)
        model.rectPackBlobs(5, 1)

        blbs1 = []
        for i in range(100):
            blbs1.append(blob(random.uniform(0,100), random.uniform(0,100)))
        model.updateCurrentBlobs(blbs1)
        model.rectPackBlobs(5, 1)

    def test_circularPackBlobs(self):
        model = MicroMSModel(None)
        model.circularPackBlobs(5, 10, 10)

        blbs1 = []
        for i in range(100):
            blbs1.append(blob(random.uniform(0,100), random.uniform(0,100)))
        model.updateCurrentBlobs(blbs1)
        model.circularPackBlobs(5, 10, 10)

    def test_analyzeAll(self):
        model = MicroMSModel(None)
        self.assertEqual(model.analyzeAll(),
                         'No targets currently selected')

        model.blobCollection[0].append(blob(10,10))
        self.assertEqual(model.analyzeAll(),
                         'Not enough training points')

        model.coordinateMapper.addPoints((0,0), (0,0))
        model.coordinateMapper.addPoints((0,10), (0,-10))
        model.coordinateMapper.addPoints((10,10), (10,-10))

        self.assertEqual(model.analyzeAll(),
                         'No connected instrument')

    def test_analyzeAllWInstrument(self):
        model = MicroMSModel(None)

        model.setCoordinateMapper(zaberMapper.zaberMapper())
        ports = model.coordinateMapper.connectedInstrument.findPorts()
        goodPort = 'COM3' #expected port to find instrument

        if goodPort in ports:
            model.coordinateMapper.connectedInstrument.initialize(goodPort)
            model.coordinateMapper.addPoints((0,0), (10000, 10000))
            model.coordinateMapper.addPoints((1000,0), (11000, 10000))
            model.coordinateMapper.addPoints((0,1000), (10000, 11000))

            model.blobCollection[0].append(blob(0,0))
            model.blobCollection[0].append(blob(1000,0))
            model.blobCollection[0].append(blob(0,1000))

            self.assertEqual(model.analyzeAll(),
                             'Finished collection')

    def test_reportSlideStep(self):
        model = MicroMSModel(None)

        model.reportSlideStep(slideWrapper.Direction.left, False)
        model.reportSlideStep(slideWrapper.Direction.right, False)
        model.reportSlideStep(slideWrapper.Direction.down, False)
        model.reportSlideStep(slideWrapper.Direction.up, False)

        model.setupMicroMS(self.tiffImg1)
        model.reportSlideStep(slideWrapper.Direction.left, False)
        model.reportSlideStep(slideWrapper.Direction.right, False)
        model.reportSlideStep(slideWrapper.Direction.down, False)
        model.reportSlideStep(slideWrapper.Direction.up, False)
        
        model.mirrorImage = True
        model.reportSlideStep(slideWrapper.Direction.left, False)
        model.reportSlideStep(slideWrapper.Direction.right, False)
        model.reportSlideStep(slideWrapper.Direction.down, False)
        model.reportSlideStep(slideWrapper.Direction.up, False)

    def test_getPatchesBasic(self):
        model = MicroMSModel(None)

        model.setupMicroMS(self.tiffImg1)
        #add fiducials for predicted points and worst fiducial
        model.setCoordinateMapper(supportedCoordSystems.supportedMappers[4])
        model.coordinateMapper.addPoints((0,0), (0,0))
        model.coordinateMapper.addPoints((100,0), (1000,0))
        model.coordinateMapper.addPoints((0,100), (0,1000))
        model.coordinateMapper.addPoints((0,100), (0,1100))
        #should show the last point as the worst
        model.getPatches(False)

        #change to experimental data/reg points on ultraflex
        model.loadCoordinateMapper(self.tiffImg1Reg)
        model.slide._zoom(5)
        model.showPrediction = True
        #should have predictions
        model.getPatches(False)

        #draw regions of interest
        model.ROI.append((0,0))
        model.ROI.append((100,200))
        model.getPatches(False)

    def test_getPatchesBlobs(self):
        model = MicroMSModel(None)
        model.setupMicroMS(self.tiffImg1)

        for i in range(500):
            model.blobCollection[0].append(blob(random.uniform(0,100), random.uniform(0,100)))
            model.blobCollection[2].append(blob(random.uniform(0,100), random.uniform(0,100)))
            model.blobCollection[4].append(blob(random.uniform(0,100), random.uniform(0,100)))

        #hit limit
        model.getPatches(True)

        #all patches
        model.getPatches(False)

        #all blobs, with limits
        model.drawAllBlobs = True
        model.getPatches(True)

    def test_reportInfoRequest(self):
        model = MicroMSModel(None)

        self.assertEqual(model.reportInfoRequest((100,100)),
                         "No slide loaded")

        model.setupMicroMS(self.tiffImg1)
        model.reportInfoRequest((100,100))

        model.showThreshold = True
        model.reportInfoRequest((100,100))

    def test_reportFiducialRequest(self):
        model = MicroMSModel(None)

        self.assertEqual(model.reportFiducialRequest((100,100), False),
                         "No slide loaded")

        model.setupMicroMS(self.tiffImg1)
        self.assertEqual(model.reportFiducialRequest((100,100), False),
                         "No input provided")

        extra = Extras(text="C5", ok=False)
        #does nothing, clicked cancel
        model.reportFiducialRequest((100,100), False, extra)
        self.assertEqual(len(model.coordinateMapper.physPoints), 0)

        extra = Extras(text="C5", ok=True)
        #does nothing, nothing to remove
        self.assertEqual(model.reportFiducialRequest((100,100), True),
                         "No points to remove")
        self.assertEqual(len(model.coordinateMapper.physPoints), 0)

        #adds point
        self.assertEqual(model.reportFiducialRequest((100,100), False, extra),
                         "C5 added at 100,100")
        self.assertEqual(len(model.coordinateMapper.physPoints), 1)

        #remove point
        self.assertEqual(model.reportFiducialRequest((100,100), True),
                         "Removed fiducial")
        self.assertEqual(len(model.coordinateMapper.physPoints), 0)

        #invalid entry
        extra = Extras(text="C4", ok=True)
        self.assertEqual(model.reportFiducialRequest((100,100), False, extra),
                         "Invalid entry: C4")

    def test_reportBlobRequest(self):
        model = MicroMSModel(None)
        
        self.assertEqual(model.currentBlobLength(), 0)
        #does nothing, no slide
        self.assertEqual(model.reportBlobRequest((10,10), 8),
                         "No slide loaded")
        self.assertEqual(model.currentBlobLength(), 0)

        model.setupMicroMS(self.tiffImg1)

        self.assertEqual(model.currentBlobLength(), 0)
        model.reportBlobRequest((10,10), 8)
        self.assertEqual(model.currentBlobLength(), 1)
        model.reportBlobRequest((10,110), 8)
        self.assertEqual(model.currentBlobLength(), 2)
        model.reportBlobRequest((110,110), 8)
        self.assertEqual(model.currentBlobLength(), 3)
        model.reportBlobRequest((10,10), 8)
        self.assertEqual(model.currentBlobLength(), 2)
        model.reportBlobRequest((110,110), 8)
        self.assertEqual(model.currentBlobLength(), 1)
        model.reportBlobRequest((10,110), 8)
        self.assertEqual(model.currentBlobLength(), 0)

    def test_requestInstrumentMove(self):
        model = MicroMSModel(None)

        self.assertEqual(model.requestInstrumentMove((100,100)), 
                         "No slide loaded")

        model.setupMicroMS(self.tiffImg1)
        self.assertEqual(model.requestInstrumentMove((100,100)),
                         "Instrument not connected")

        #change to zaber
        model.setCoordinateMapper(supportedCoordSystems.supportedMappers[4])
        self.assertEqual(model.requestInstrumentMove((100,100)),
                         "Instrument not connected")

        #connect
        ports = model.coordinateMapper.connectedInstrument.findPorts()
        goodPort = 'COM3' #expected port to find instrument

        if goodPort in ports:
            model.coordinateMapper.connectedInstrument.initialize(goodPort)
            self.assertEqual(model.requestInstrumentMove((100,100)),
                             "Not enough training points")

            model.coordinateMapper.addPoints((0,0), (0,0))
            model.coordinateMapper.addPoints((100,0), (1000,0))
            model.coordinateMapper.addPoints((0,100), (0,1000))
            
            self.assertEqual(model.requestInstrumentMove((100,100)),
                             "Moving to 1000, 1000")

            model.coordinateMapper.connectedInstrument.homeAll()
            
class test_popups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.img = constants.tiffImg1

    def setUp(self):
        self.GUI = MicroMSQTWindow()


    def test_blobPopup(self):
        blbFinder = blobFinder.blobFinder(None)
        blbPopup = blbPopupWindow(blbFinder)
        self.assertEqual(blbPopup.channel.currentIndex(), blbFinder.colorChannel)

        #test good values for changing everything
        minSize = 40
        maxSize = 600
        minCirc = 0.5
        maxCirc = 1
        thresh = 150
        imgChannel = 1
        color = 0

        blbPopup.minText.setText(str(minSize))
        blbPopup.maxText.setText(str(maxSize))
        blbPopup.minCirText.setText(str(minCirc))
        blbPopup.maxCirText.setText(str(maxCirc))
        blbPopup.intens.setText(str(thresh))
        blbPopup.imgInd.setText(str(imgChannel+1)) #note +1 for display purposes
        blbPopup.channel.setCurrentIndex(color)

        blbPopup.setParams()

        #check if blobfinder is changed
        self.assertEqual(blbFinder.minSize, minSize)
        self.assertEqual(blbFinder.maxSize, maxSize)
        self.assertEqual(blbFinder.minCircularity, minCirc)
        self.assertEqual(blbFinder.maxCircularity, maxCirc)
        self.assertEqual(blbFinder.threshold, thresh)
        self.assertEqual(blbFinder.imageIndex, imgChannel)
        self.assertEqual(blbFinder.colorChannel, color)
        #check if text is changed for a few
        self.assertEqual(blbPopup.minText.text(), str(minSize))

        #pass none to all ("")
        blbPopup.minText.setText("")
        blbPopup.maxText.setText("")
        blbPopup.minCirText.setText("")
        blbPopup.maxCirText.setText("")
        blbPopup.intens.setText("")
        blbPopup.imgInd.setText("")
        
        blbPopup.setParams()
        
        self.assertEqual(blbFinder.minSize, minSize)
        self.assertIsNone(blbFinder.maxSize)#this can be none
        self.assertEqual(blbFinder.minCircularity, minCirc)
        self.assertIsNone(blbFinder.maxCircularity)#this can be none
        self.assertEqual(blbFinder.threshold, thresh)
        self.assertEqual(blbFinder.imageIndex, imgChannel)
        #this should have reset
        self.assertEqual(blbPopup.minText.text(), str(minSize))

        #pass all invalid strings
        QTest.keyClicks(blbPopup.minText, "asdf")
        QTest.keyClicks(blbPopup.maxText, "asdf")
        QTest.keyClicks(blbPopup.minCirText, "asdf")
        QTest.keyClicks(blbPopup.maxCirText, "asdf")
        QTest.keyClicks(blbPopup.intens, "asdf")
        QTest.keyClicks(blbPopup.imgInd, "asdf")
        
        QTest.mouseClick(blbPopup.setButton, Qt.LeftButton)
        
        self.assertEqual(blbFinder.minSize, minSize)
        self.assertIsNone(blbFinder.maxSize)#this can be none
        self.assertEqual(blbFinder.minCircularity, minCirc)
        self.assertIsNone(blbFinder.maxCircularity)#this can be none
        self.assertEqual(blbFinder.threshold, thresh)
        self.assertEqual(blbFinder.imageIndex, imgChannel)
        #this should have reset
        self.assertEqual(blbPopup.minText.text(), str(minSize))

    def test_blobPopupWMaster(self):
        self.GUI.setupCanvas(self.img)
        blbFinder = blobFinder.blobFinder(self.GUI.model.slide)
        blbPopup = blbPopupWindow(blbFinder, self.GUI)
        self.assertEqual(blbPopup.channel.currentIndex(), blbFinder.colorChannel)

        #test good values for changing everything
        minSize = 40
        maxSize = 600
        minCirc = 0.5
        maxCirc = 1
        thresh = 150
        imgChannel = 1
        color = 0

        blbPopup.minText.setText(str(minSize))
        blbPopup.maxText.setText(str(maxSize))
        blbPopup.minCirText.setText(str(minCirc))
        blbPopup.maxCirText.setText(str(maxCirc))
        blbPopup.intens.setText(str(thresh))
        blbPopup.imgInd.setText(str(imgChannel+1)) #note +1 for display purposes
        blbPopup.channel.setCurrentIndex(color)

        blbPopup.setParams()

        #check if blobfinder is changed
        self.assertEqual(blbFinder.minSize, minSize)
        self.assertEqual(blbFinder.maxSize, maxSize)
        self.assertEqual(blbFinder.minCircularity, minCirc)
        self.assertEqual(blbFinder.maxCircularity, maxCirc)
        self.assertEqual(blbFinder.threshold, thresh)
        self.assertEqual(blbFinder.imageIndex, imgChannel)
        self.assertEqual(blbFinder.colorChannel, color)
        #check if text is changed for a few
        self.assertEqual(blbPopup.minText.text(), str(minSize))

        #pass none to all ("")
        blbPopup.minText.setText("")
        blbPopup.maxText.setText("")
        blbPopup.minCirText.setText("")
        blbPopup.maxCirText.setText("")
        blbPopup.intens.setText("")
        blbPopup.imgInd.setText("")
        
        blbPopup.setParams()
        
        self.assertEqual(blbFinder.minSize, minSize)
        self.assertIsNone(blbFinder.maxSize)#this can be none
        self.assertEqual(blbFinder.minCircularity, minCirc)
        self.assertIsNone(blbFinder.maxCircularity)#this can be none
        self.assertEqual(blbFinder.threshold, thresh)
        self.assertEqual(blbFinder.imageIndex, imgChannel)
        #this should have reset
        self.assertEqual(blbPopup.minText.text(), str(minSize))

        #pass all invalid strings
        QTest.keyClicks(blbPopup.minText, "asdf")
        QTest.keyClicks(blbPopup.maxText, "asdf")
        QTest.keyClicks(blbPopup.minCirText, "asdf")
        QTest.keyClicks(blbPopup.maxCirText, "asdf")
        QTest.keyClicks(blbPopup.intens, "asdf")
        QTest.keyClicks(blbPopup.imgInd, "asdf")
        
        QTest.mouseClick(blbPopup.setButton, Qt.LeftButton)
        
        self.assertEqual(blbFinder.minSize, minSize)
        self.assertIsNone(blbFinder.maxSize)#this can be none
        self.assertEqual(blbFinder.minCircularity, minCirc)
        self.assertIsNone(blbFinder.maxCircularity)#this can be none
        self.assertEqual(blbFinder.threshold, thresh)
        self.assertEqual(blbFinder.imageIndex, imgChannel)
        #this should have reset
        self.assertEqual(blbPopup.minText.text(), str(minSize))

    def test_gridPopupForAll(self):
        model = MicroMSModel(None)
        for m in supportedCoordSystems.supportedMappers:
            intMap = m.getIntermediateMap()
            model.setCoordinateMapper(m)
            grid = gridPopupWindow(model)

            for i in range(grid.table.rowCount()):
                for j in range(3):
                    self.assertEqual(grid.table.item(i,j).text(), str(intMap[i][j]))

    def test_gridPopupForUltraflex(self):
        m = ultraflexMapper()
        intMap = m.getIntermediateMap()
        model = MicroMSModel(None)
        model.setCoordinateMapper(m)

        grid = gridPopupWindow(model)
        grid.table.item(0,0).setText("C6")
        grid.close()

        intMap2 = m.getIntermediateMap()
        #want to do this before possible test fails
        m.setIntermediateMap(intMap)
        for t in intMap2:
            self.assertNotEqual(t[0], "C20") #C20 should be overwritten

        self.assertEqual(intMap2[0][0], "C6")

    def test_histPopup(self):
        self.assertFalse(self.GUI.histCanvas.reduceMax)
        pop = histPopupWindow(self.GUI.histCanvas, self.GUI)

        pop.imgInd.setText("asdf")
        pop.offset.setText("asdf")

        pop.setParams()

        self.assertEqual(pop.imgInd.text(), str(self.GUI.histCanvas.imgInd+1))#note +1
        self.assertEqual(pop.offset.text(), str(self.GUI.histCanvas.offset))
        
        pop.imgInd.setText("1")
        pop.offset.setText("-5")
        pop.channel.setCurrentIndex(2)
        pop.max.setChecked(True)

        pop.setParams()
        self.assertEqual(self.GUI.histCanvas.imgInd, 0)#note -1!
        self.assertEqual(self.GUI.histCanvas.offset, -5)
        self.assertEqual(self.GUI.histCanvas.populationMetric, 2)
        self.assertTrue(self.GUI.histCanvas.reduceMax)
        self.assertTrue(pop.max.isChecked())
        self.assertFalse(pop.mean.isChecked())#should be exclusive
      
class test_histCanvas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.GUI = MicroMSQTWindow()
        cls.model = cls.GUI.model
        cls.model.setupMicroMS(constants.tiffImg1)
        cls.model.blobFinder.threshold = 75
        tempDir, f = os.path.split(__file__)
        cls.fname = os.path.join(tempDir, 'cells.txt')
        if not os.path.exists(cls.fname):
            cls.model.runGlobalBlobFind()
            self.model.blobCollection[0] = self.model.blobCollection[0][:1000]
            cls.model.saveCurrentBlobFinding(cls.fname)
        cls.hist = cls.GUI.histCanvas

    def setUp(self):
        self.GUI = MicroMSQTWindow()
        self.model = self.GUI.model
        self.model.setupMicroMS(constants.tiffImg1)
        self.model.loadBlobFinding(self.fname)
        self.hist = self.GUI.histCanvas

    def test_calculateHist(self):
        self.model.blobCollection[0] = self.model.blobCollection[0][:100]
        for i in range(6):
            self.hist.populationMetric = i
            self.hist.calculateHist()
        self.model.blobCollection[0] = []
        self.hist.calculateHist()
        self.assertIsNone(self.hist.populationValues)

    def test_mouseUp(self):
        #should do nothing
        QTest.mouseClick(self.hist, Qt.LeftButton)
        self.assertIsNone(self.hist.lowIntens)
        QTest.mouseClick(self.hist, Qt.RightButton)
        self.assertIsNone(self.hist.highIntens)
        QTest.mouseClick(self.hist, Qt.MiddleButton)
        self.assertIsNone(self.hist.singleBar)

        self.model.blobCollection[0] = self.model.blobCollection[0][:100]
        self.GUI.showHistWindow()
        QTest.mouseClick(self.hist, Qt.LeftButton)
        self.assertIsNotNone(self.hist.lowIntens)
        QTest.mouseClick(self.hist, Qt.RightButton)
        self.assertIsNotNone(self.hist.highIntens)
        QTest.mouseClick(self.hist, Qt.MiddleButton)
        self.assertIsNotNone(self.hist.singleBar)
        QTest.mouseClick(self.hist, Qt.LeftButton, Qt.ShiftModifier)
        self.assertIsNotNone(self.hist.lowLimit)
        QTest.mouseClick(self.hist, Qt.RightButton, Qt.ShiftModifier)
        self.assertIsNotNone(self.hist.highLimit)
        QTest.mouseClick(self.hist, Qt.MiddleButton, Qt.ShiftModifier)
        self.assertIsNotNone(self.hist.singleBar)

    def test_mouseZoom(self):
        self.model.blobCollection[0] = self.model.blobCollection[0][:100]
        self.GUI.showHistWindow()
        self.assertEqual(self.hist.zoomLvl, 0)
        evt = mpl.backend_bases.MouseEvent('scroll_event', self.hist, 10, 0, 'up')
        evt.xdata = 10
        self.hist.mouseZoom(evt)
        self.assertEqual(self.hist.zoomLvl, 1)
        evt = mpl.backend_bases.MouseEvent('scroll_event', self.hist, 10, 0, 'down')
        evt.xdata = 10
        self.hist.mouseZoom(evt)
        self.assertEqual(self.hist.zoomLvl, 0)

    def test_setCellNumber(self):
        #should return, hist not calculated
        self.hist.setCellNum(50)

        self.GUI.showHistWindow()
        self.hist.setCellNum(50)


    def test_getFilteredBlobs(self):
        self.GUI.showHistWindow()
        #no cells
        self.hist.getFilteredBlobs()
        #both cells
        self.hist.setCellNum(50)
        self.hist.getFilteredBlobs()

        #just high
        temp = self.hist.lowIntens
        self.hist.lowIntens = None
        self.hist.getFilteredBlobs()
        #with limit
        self.hist.highLimit = 250
        self.hist.getFilteredBlobs()
        self.hist.highLimit = None

        #just low
        self.hist.lowIntens = temp
        self.hist.highIntens = None
        self.hist.getFilteredBlobs()
        #with limit
        self.hist.lowLimit = 1
        self.hist.getFilteredBlobs()

    def test_getFilterDescription(self):
        self.GUI.showHistWindow()
        self.assertIsNone(self.hist.getFilterDescription())

        #set high and low
        self.hist.setCellNum(60)
        self.assertIsNone(self.hist.getFilterDescription())

        temp = self.hist.highIntens
        self.hist.highIntens = None

        self.assertEqual(self.hist.getFilterDescription(),
                         'c1[Size]<61.9;mean;offset=0')

        self.hist.reduceMax = True
        self.assertEqual(self.hist.getFilterDescription(),
                         'c1[Size]<61.9;max;offset=0')
        self.hist.imgInd = 2
        self.assertEqual(self.hist.getFilterDescription(),
                         'c2[Size]<61.9;max;offset=0')
        self.hist.offset = 10
        self.assertEqual(self.hist.getFilterDescription(),
                         'c2[Size]<61.9;max;offset=10')

        self.hist.reduceMax = False
        self.hist.imgInd = 1
        self.hist.offset = 0

        self.hist.lowLimit = 20
        self.assertEqual(self.hist.getFilterDescription(),
                         '20.0<c1[Size]<61.9;mean;offset=0')

        self.hist.highIntens = temp
        self.hist.lowIntens = None
        self.assertEqual(self.hist.getFilterDescription(),
                         '970.0<c1[Size];mean;offset=0')

        self.hist.highLimit = 1000
        self.assertEqual(self.hist.getFilterDescription(),
                         '970.0<c1[Size]<1000.0;mean;offset=0')

    def test_update_figure(self):
        self.GUI.showHistWindow()
        self.hist.setCellNum(45)

        self.hist.singleBar = 20
        self.hist.update_figure()

        self.hist.singleCell = 10
        self.hist.update_figure()

class test_slideCanvas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.GUI = MicroMSQTWindow()
        cls.GUI.setupCanvas(constants.tiffImg1)
        cls.model = cls.GUI.model
        cls.model.blobFinder.threshold = 75
        tempDir, f = os.path.split(__file__)
        cls.fname = os.path.join(tempDir, 'cells.txt')
        if not os.path.exists(cls.fname):
            cls.model.runGlobalBlobFind()
            cls.model.blobCollection[0] = cls.model.blobCollection[0][:1000]
            cls.model.saveCurrentBlobFinding(cls.fname)

        cls.slide = cls.GUI.slideCanvas

    def setUp(self):
        self.GUI = MicroMSQTWindow()
        self.GUI.setupCanvas(constants.tiffImg1)

        self.model = self.GUI.model
        self.model.loadBlobFinding(self.fname)
        self.slide = self.GUI.slideCanvas

        del supportedCoordSystems.supportedMappers[4]
        supportedCoordSystems.supportedMappers.append(zaberMapper.zaberMapper())

    def test_mouseUpLC(self):
        #click outside of widget
        evt = mpl.backend_bases.MouseEvent('button_release_event', self.slide, 0, 0)
        evt.xdata = None
        evt.ydata = 10
        
        self.slide.mouseUp(evt)

        #left click to move
        pos = (self.model.slide.pos[0], self.model.slide.pos[1])
        size = self.model.slide.size
        evt = mpl.backend_bases.MouseEvent('button_release_event', self.slide, 0, 0)
        evt.button = 1
        evt.xdata = 100
        evt.ydata = 100

        self.slide.mouseUp(evt)
        self.assertEqual(self.model.slide.pos[0],
                         pos[0]-size[0]/2+100)
        self.assertEqual(self.model.slide.pos[1],
                         pos[1]-size[1]/2+100)

        #shift left click to add/remove points
        self.model.currentBlobs = 1
        self.assertEqual(self.model.currentBlobLength(), 0)
        extras = Extras(modifiers = Qt.ShiftModifier)

        self.slide.mouseUp(evt,extras)
        self.assertEqual(self.model.currentBlobLength(), 1)
        
        self.slide.mouseUp(evt,extras)
        self.assertEqual(self.model.currentBlobLength(), 0)

        #alt left click to move instrument
        #should do nothing
        extras = Extras(modifiers = Qt.AltModifier)
        self.slide.mouseUp(evt,extras)

        #with instrument
        self.model.setCoordinateMapper(supportedCoordSystems.supportedMappers[4])
        ports = self.model.coordinateMapper.connectedInstrument.findPorts()
        goodPort = 'COM3'
        if goodPort in ports:
            self.model.coordinateMapper.connectedInstrument.initialize(goodPort)
            self.model.coordinateMapper.addPoints((0,0), (10000, 10000))
            self.model.coordinateMapper.addPoints((1000,0), (11000, 10000))
            self.model.coordinateMapper.addPoints((0,1000), (10000, 11000))
            
            self.slide.mouseUp(evt,extras)

    def test_mouseUpRC(self):
        #right click for fiducials
        evt = mpl.backend_bases.MouseEvent('button_release_event', self.slide, 0, 0)
        evt.button = 3
        evt.xdata = 100
        evt.ydata = 100

        fids = len(self.model.coordinateMapper.physPoints)
        #add fiducial
        extras = Extras(text = "C5", ok = True)
        self.slide.mouseUp(evt, extras)
        self.assertEqual(len(self.model.coordinateMapper.physPoints),
                         fids +1)
        
        #invalid, do nothing
        extras = Extras(text = "C4", ok = True)
        self.slide.mouseUp(evt, extras)
        self.assertEqual(len(self.model.coordinateMapper.physPoints),
                         fids +1)

        #shift RC remove fiducial
        extras = Extras(modifiers=Qt.ShiftModifier)
        self.slide.mouseUp(evt, extras)
        self.assertEqual(len(self.model.coordinateMapper.physPoints),
                         fids)

    def test_mouseUpMMB(self):
        evt = mpl.backend_bases.MouseEvent('button_release_event', self.slide, 0, 0)
        evt.button = 2
        evt.xdata = 100
        evt.ydata = 100
        self.slide.mouseUp(evt)

    def test_drawROI(self):
        evt = mpl.backend_bases.MouseEvent('button_press_event', self.slide, 0, 0)
        evt.button = 1
        
        evt.xdata = None
        evt.ydata = 50
        self.slide.mouseMove(evt)
        self.slide.mouseDown(evt)

        evt.xdata = 0
        evt.ydata = 0
        extras = Extras(modifiers=Qt.ControlModifier)

        self.assertEqual(self.model.ROI, [])
        
        self.slide.mouseDown(evt)
        self.assertFalse(self.slide.mDown)
        self.slide.mouseDown(evt, extras)
        self.assertTrue(self.slide.mDown)

        evt.xdata = 50
        evt.ydata = 50
        self.slide.mouseMove(evt)
        self.assertTrue(self.slide.mDown)

        evt.xdata = 100
        evt.ydata = 100
        self.slide.mouseUp(evt)

        self.assertEqual(self.model.ROI[0][0], 0)
        self.assertEqual(self.model.ROI[0][1], 0)
        self.assertEqual(self.model.ROI[1][0], 100)
        self.assertEqual(self.model.ROI[1][1], 100)
        self.assertFalse(self.slide.mDown)

        #again at a zoomed out level
        self.model.slide.zoomOut()
        self.model.slide.pos = [600, 600]#recenter

        evt.xdata = 0
        evt.ydata = 0

        self.slide.mouseDown(evt, extras)
        self.assertTrue(self.slide.mDown)

        evt.xdata = 50
        evt.ydata = 50
        self.slide.mouseMove(evt)
        self.assertTrue(self.slide.mDown)

        evt.xdata = 100
        evt.ydata = 100
        self.slide.mouseUp(evt)

        self.assertEqual(self.model.ROI[0][0], 0)
        self.assertEqual(self.model.ROI[0][1], 0)
        self.assertEqual(self.model.ROI[1][0], 200)
        self.assertEqual(self.model.ROI[1][1], 200)
        self.assertFalse(self.slide.mDown)

        
    def test_drawCell(self):
        self.model.currentBlobs = 1
        evt = mpl.backend_bases.MouseEvent('button_press_event', self.slide, 0, 0)
        evt.button = 1

        evt.xdata = 0
        evt.ydata = 0
        extras = Extras(modifiers=Qt.ShiftModifier)
        
        self.assertEqual(self.model.currentBlobLength(), 0)

        self.slide.mouseDown(evt, extras)
        self.assertTrue(self.slide.mDownCirc)

        evt.xdata = 25
        evt.ydata = 25
        self.slide.mouseMove(evt)
        self.assertTrue(self.slide.mDownCirc)

        evt.xdata = 0
        evt.ydata = 50
        self.slide.mouseUp(evt, extras)

        self.assertEqual(self.model.currentBlobLength(), 1)
        self.assertAlmostEqual(self.model.blobCollection[1][0].radius, 50, 0)
        self.assertAlmostEqual(self.model.blobCollection[1][0].X, 0, 0)
        self.assertAlmostEqual(self.model.blobCollection[1][0].Y, 50, 0)
        self.assertFalse(self.slide.mDownCirc)

        #remove with mouse drag
        evt.xdata = 0
        evt.ydata = 0

        self.slide.mouseDown(evt, extras)
        self.assertTrue(self.slide.mDownCirc)

        evt.xdata = 20
        evt.ydata = 20
        self.slide.mouseMove(evt)
        self.assertTrue(self.slide.mDownCirc)

        evt.xdata = 25
        evt.ydata = 25
        self.slide.mouseUp(evt, extras)

        self.assertEqual(self.model.currentBlobLength(), 0)
        self.assertFalse(self.slide.mDownCirc)

        #add with small radius
        evt.xdata = 0
        evt.ydata = 0

        self.slide.mouseDown(evt, extras)
        self.assertTrue(self.slide.mDownCirc)

        evt.xdata = 1
        evt.ydata = 1
        self.slide.mouseMove(evt)
        self.assertTrue(self.slide.mDownCirc)

        evt.xdata = 2
        evt.ydata = 2
        self.slide.mouseUp(evt, extras)
        
        self.assertEqual(self.model.currentBlobLength(), 1)
        self.assertAlmostEqual(self.model.blobCollection[1][0].radius, 
                               GUIConstants.DEFAULT_BLOB_RADIUS, 0)
        self.assertAlmostEqual(self.model.blobCollection[1][0].X, 2, 0)
        self.assertAlmostEqual(self.model.blobCollection[1][0].Y, 2, 0)
        self.assertFalse(self.slide.mDownCirc)

    def test_drawMirrored(self):
        self.model.mirrorImage = True
        self.test_drawCell()
        self.test_drawROI()

    def test_mouseZoom(self):
        evt = mpl.backend_bases.MouseEvent('scroll_event', self.slide, 10, 0, 'up')
        evt.xdata = None

        self.slide.mouseZoom(evt)

        evt.xdata = 100
        evt.ydata = 100
        self.assertEqual(self.model.slide.lvl, 0)
        self.slide.mouseZoom(evt)
        self.assertEqual(self.model.slide.lvl, 0)
        
        evt.button = 'down'
        self.slide.mouseZoom(evt)
        self.assertEqual(self.model.slide.lvl, 1)
        self.slide.mouseZoom(evt)
        self.assertEqual(self.model.slide.lvl, 2)

        evt.button = 'up'
        self.slide.mouseZoom(evt)
        self.assertEqual(self.model.slide.lvl, 1)
        self.slide.mouseZoom(evt)
        self.assertEqual(self.model.slide.lvl, 0)

class test_microMSWindow(unittest.TestCase):
    #this will end up many canvas and model functions
    @classmethod
    def setUpClass(cls):
        cls.tiffImg1 = constants.tiffImg1
        cls.tiffImg2 = constants.tiffImg2
        cls.ndpiImg1 = constants.ndpiImg1
        cls.ndpiImg2 = constants.ndpiImg2
        cls.smallTif = constants.smallTif
        
    def test_init(self):
        GUI = MicroMSQTWindow()
        self.assertFalse(GUI.showHist)

    def test_setup(self):
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.ndpiImg1)

    def test_mapperChanged(self):
        GUI = MicroMSQTWindow()
        #without opening
        self.assertTrue(GUI.instruments.actions()[0].isChecked())
        self.assertFalse(GUI.instruments.actions()[1].isChecked())
        inst = GUI.instruments.actions()[1].trigger()
        self.assertTrue(GUI.instruments.actions()[1].isChecked())
        self.assertFalse(GUI.instruments.actions()[0].isChecked())

        #with an image
        GUI.setupCanvas(self.tiffImg1)
        inst = GUI.instruments.actions()[2].trigger()
        self.assertTrue(GUI.instruments.actions()[2].isChecked())
        self.assertFalse(GUI.instruments.actions()[1].isChecked())
        self.assertFalse(GUI.instruments.actions()[0].isChecked())

    def test_histShow(self):
        GUI = MicroMSQTWindow()
        self.assertFalse(GUI.showHist)
        GUI.showHistWindow()
        self.assertTrue(GUI.showHist)
        GUI.showHistWindow()
        self.assertFalse(GUI.showHist)

    def test_keyPresses(self):
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)
        #wasd
        QTest.keyClick(GUI, 'a')
        QTest.keyClick(GUI, 'w')
        QTest.keyClick(GUI, 'd')
        QTest.keyClick(GUI, 's')

        #zoom in and out
        QTest.keyClick(GUI, 'q')
        self.assertEqual(GUI.model.slide.lvl, 1)
        QTest.keyClick(GUI, 'e')
        self.assertEqual(GUI.model.slide.lvl, 0)

        #reset
        QTest.keyClick(GUI, 'a')
        QTest.keyClick(GUI, 'w')
        QTest.keyClick(GUI, 'q')
        QTest.keyClick(GUI, 'q')
        self.assertEqual(GUI.model.slide.lvl, 2)

        QTest.keyClick(GUI, 'r')
        self.assertEqual(GUI.model.slide.lvl, 0)

        #togggle view
        self.assertTrue(GUI.model.showPatches)
        QTest.keyClick(GUI, 'o')
        self.assertFalse(GUI.model.showPatches)

        self.assertFalse(GUI.model.drawAllBlobs)
        QTest.keyClick(GUI, Qt.Key_O, Qt.ShiftModifier)
        self.assertTrue(GUI.model.drawAllBlobs)

        #these will just be key presses without many assertions
        QTest.keyClick(GUI, Qt.Key_Z, Qt.ControlModifier)
        QTest.keyClick(GUI, Qt.Key_Z)
        QTest.keyClick(GUI, Qt.Key_T)
        QTest.keyClick(GUI, Qt.Key_P)
        QTest.keyClick(GUI, Qt.Key_M)
        QTest.keyClick(GUI, Qt.Key_B)
        QTest.keyClick(GUI, Qt.Key_B, Qt.ShiftModifier)
        QTest.keyClick(GUI, Qt.Key_C)
        QTest.keyClick(GUI, Qt.Key_C, Qt.ShiftModifier)
        QTest.keyClick(GUI, Qt.Key_1)
        QTest.keyClick(GUI, Qt.Key_2, Qt.ControlModifier)
        QTest.keyClick(GUI, Qt.Key_2, Qt.AltModifier)

    def test_keysWInstrument(self):
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)
        supportedCoordSystems.supportedMappers[4] = zaberMapper.zaberMapper()
        GUI.model.setCoordinateMapper(supportedCoordSystems.supportedMappers[4])
        ports = GUI.model.coordinateMapper.connectedInstrument.findPorts()
        goodPort = 'COM3' #expected port to find instrument

        if goodPort in ports:
            GUI.model.coordinateMapper.connectedInstrument.initialize(goodPort)
            self.assertTrue(GUI.model.coordinateMapper.connectedInstrument.connected)
            self.assertTrue(GUI.model.coordinateMapper.isConnectedToInstrument)
            GUI.model.coordinateMapper.connectedInstrument.moveToPositionXY((100000, 100000))
            QTest.keyClick(GUI, Qt.Key_I, Qt.ShiftModifier)
            QTest.keyClick(GUI, Qt.Key_J, Qt.ShiftModifier)
            QTest.keyClick(GUI, Qt.Key_K, Qt.ShiftModifier)
            QTest.keyClick(GUI, Qt.Key_L, Qt.ShiftModifier)
            
            QTest.keyClick(GUI, Qt.Key_Minus)
            QTest.keyClick(GUI, Qt.Key_Equal)
            QTest.keyClick(GUI, Qt.Key_Underscore)
            QTest.keyClick(GUI, Qt.Key_Plus)
            QTest.keyClick(GUI, Qt.Key_Underscore)
            QTest.keyClick(GUI, Qt.Key_Underscore)
            QTest.keyClick(GUI, Qt.Key_V, Qt.ShiftModifier)
            QTest.keyClick(GUI, Qt.Key_V)
            QTest.keyClick(GUI, Qt.Key_X)
            QTest.keyClick(GUI, Qt.Key_H)

            GUI.fileQuit()

    def test_debugLoad(self):
        GUI = MicroMSQTWindow()
        QTest.keyClick(GUI, Qt.Key_D, Qt.ControlModifier)
        GUI.debugLoad()
        GUI.model.slide._zoom(10)
        GUI.slideCanvas.draw()
        QTest.keyClick(GUI, Qt.Key_F, Qt.ControlModifier)
        QTest.keyClick(GUI, Qt.Key_2, Qt.AltModifier)
        GUI.slideCanvas.draw()

    def test_reportFromModel(self):
        GUI = MicroMSQTWindow()
        GUI.showHistWindow()
        GUI.reportFromModel("", True, True)
        
    #a lot of the remaining functions are difficult to test as they spawn blocking GUI message blocks.
    #overloading the connected functions to take an additional argument with data to stop popups

    def test_fileOpen(self):
        GUI = MicroMSQTWindow()
        extras = Extras(fileName=self.tiffImg1)

        GUI.fileOpen(extras)
        self.assertEqual(GUI.fileName, os.path.splitext(os.path.basename(extras.fileName))[0])

    def test_decimate(self):
        GUI = MicroMSQTWindow()
        extras = Extras(fileName=self.smallTif)

        GUI.decimateImageGroup(extras)
        self.assertEqual(GUI.fileName, os.path.splitext(os.path.basename(extras.fileName))[0])

    def test_saveImg(self):
        GUI = MicroMSQTWindow()
        tdir = tempfile.TemporaryDirectory()
        extras = Extras(fileName=os.path.join(tdir.name, 'test.png'))

        GUI.setupCanvas(self.tiffImg1)
        GUI.saveImg(extras)
    
    def test_saveWholeImg(self):
        GUI = MicroMSQTWindow()
        tdir = tempfile.TemporaryDirectory()
        extras = Extras(fileName=os.path.join(tdir.name, 'test.png'))

        GUI.setupCanvas(self.tiffImg1)
        GUI.model.slide._zoom(5)
        GUI.saveWholeImg(extras)

    def test_saveAll(self):
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)
        tdir = tempfile.TemporaryDirectory()
        GUI.directory = tdir.name
        extras = Extras(ok=False, text='test')
        #do nothing
        GUI.saveAll(extras)

        extras = Extras(ok=True, text='test')
        #do nothing, no blobs or coordinates
        GUI.saveAll(extras)

        #add blobs
        GUI.model.blobCollection[0].append(blob(0,0))
        GUI.model.blobCollection[0].append(blob(0,2))
        #save just blobs
        GUI.saveAll(extras)

        GUI.model.coordinateMapper.addPoints((0,0), (0,0))
        #save both
        GUI.saveAll(extras)

    def test_saveReg(self):
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)
        tdir = tempfile.TemporaryDirectory()
        extras = Extras(fileName=os.path.join(tdir.name, 'test.msreg'))
        #do nothing
        GUI.saveReg(extras)
        
        GUI.model.coordinateMapper.addPoints((0,0), (0,0))
        #save
        GUI.saveReg(extras)

    def test_saveCurrentFind(self):
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)

        tdir = tempfile.TemporaryDirectory()
        extras = Extras(fileName=os.path.join(tdir.name, 'test.txt'))

        GUI.saveCurrentFind(extras)

    def test_saveHistogramBlobs(self):
        GUI = MicroMSQTWindow()
        GUI.debugLoad()
        GUI.showHistWindow()

        GUI.model.slide._zoom(5)
        
        GUI.histCanvas.lowIntens = 600
        GUI.histCanvas.highIntens = 150
        GUI.histCanvas.update_figure()
        GUI.limitDraw.setChecked(True)
        GUI.slideCanvas.draw()
        GUI.histCanvas.lowIntens = 60
        
        tdir = tempfile.TemporaryDirectory()
        extras = Extras(fileName=os.path.join(tdir.name, 'test.txt'))

        GUI.saveHistogramBlobs(extras)

        b = GUI.model.histogramBlobs[0][0][0] #gross
        evt = mpl.backend_bases.MouseEvent('button_release_event', GUI.slideCanvas, 0, 0)
        evt.button = 2
        GUI.model.slide.pos = [b.X, b.Y]
        GUI.model.slide.lvl = 0
        p = GUI.model.slide.getLocalPoint((b.X,b.Y))
        evt.xdata = p[0]
        evt.ydata = p[1]
        GUI.slideCanvas.mouseUp(evt)

        evt.xdata = -1
        evt.ydata = b.Y
        GUI.slideCanvas.mouseUp(evt)

    def test_saveAllBlobs(self):
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)

        for i in range(100):
            GUI.model.blobCollection[0].append(blob(random.uniform(0,100)))
            GUI.model.blobCollection[1].append(blob(random.uniform(0,100)))
            GUI.model.blobCollection[2].append(blob(random.uniform(0,100)))

        tdir = tempfile.TemporaryDirectory()
        extras = Extras(fileName=os.path.join(tdir.name, 'test.txt'))

        GUI.saveAllBlobs(extras)

    def test_saveInstrumentPositions(self):
        GUI = MicroMSQTWindow()
        GUI.debugLoad()

        tdir = tempfile.TemporaryDirectory()
        extras = Extras(fileName=os.path.join(tdir.name, 'test.xeo'),
                        ok=True,
                        text = 100)

        GUI.saveInstrumentPositions(extras)

        GUI.model.currentBlobs = 1
        GUI.model.blobCollection[1].append(blob())
        GUI.model.blobCollection[1].append(blob(1))
        GUI.model.blobCollection[1].append(blob(2))

        extras = Extras(fileName=os.path.join(tdir.name, 'test.xeo'),
                        ok=True,
                        text = '')
        GUI.saveInstrumentPositions(extras)

        extras = Extras(fileName=os.path.join(tdir.name, 'test.xeo'),
                        ok=False,
                        text = '')
        GUI.saveInstrumentPositions(extras)

    def test_saveFiducialPositions(self):
        GUI = MicroMSQTWindow()
        GUI.debugLoad()

        tdir = tempfile.TemporaryDirectory()
        extras = Extras(fileName=os.path.join(tdir.name, 'test.xeo'))

        GUI.saveFiducialPositions(extras)

    def test_globalCell(self):
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)
        
        extras = Extras(ok = True,
                        text = 'test')
        GUI.globalCell(extras)

        GUI.model.ROI.append((0,0))
        GUI.model.ROI.append((120,340))
        GUI.globalCell(extras)

    def test_instrumentConnections(self):
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)
        supportedCoordSystems.supportedMappers[4] = zaberMapper.zaberMapper()
        GUI.model.setCoordinateMapper(supportedCoordSystems.supportedMappers[4])
        ports = GUI.model.coordinateMapper.connectedInstrument.findPorts()
        goodPort = 'COM3' #expected port to find instrument

        if goodPort in ports:
            extras = Extras(ok = True,
                            text = 'COM4')
            GUI.initializeInstrument(extras)

            extras = Extras(ok = True,
                            text = goodPort)
            GUI.initializeInstrument(extras)

            extras = Extras(ok = True,
                            text = 'asdf')
            GUI.setDwell(extras)

            extras = Extras(ok = True,
                            text = '1.5')
            GUI.setDwell(extras)

            GUI.analyzeAll()

            GUI.model.coordinateMapper.addPoints((0,0), (0,0))
            GUI.model.coordinateMapper.addPoints((100,0), (10000,0))
            GUI.model.coordinateMapper.addPoints((0,100), (0,10000))

            GUI.model.blobCollection[0].append(blob(50, 50))
            GUI.model.blobCollection[0].append(blob(50, 100))

            GUI.analyzeAll()

    def test_close(self):
        GUI = MicroMSQTWindow()
        GUI.fileQuit()

        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)
        GUI.fileQuit()

    def test_histSelect(self):
        GUI = MicroMSQTWindow()
        GUI.debugLoad()
        GUI.showHistWindow()

        GUI.histSelect(Extras(text=50, ok = True))

        GUI.histFilter()
        GUI.histCanvas.highIntens = None
        GUI.histFilter()

    def test_distanceFilter(self):
        GUI = MicroMSQTWindow()
        GUI.debugLoad()
        GUI.distanceFilter(Extras(ok = True, text = '100'))
        GUI.showHistWindow()
        GUI.distanceFilter(Extras(ok = True, text = '50'))

    def test_packing(self):
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)

        GUI.model.blobCollection[0].append(blob(10, 10, 100))
        GUI.model.blobCollection[0].append(blob(50, 50, 10))
        GUI.model.blobCollection[0].append(blob(25, 50, 8))

        GUI.rectPack(Extras(sep = 50, layers = 1, dynamicLayering = False))
        GUI.model.restoreSavedBlobs()
        GUI.hexPack(Extras(sep = 50, layers = 1, dynamicLayering = False))
        GUI.model.currentBlobs = 1
        GUI.model.restoreSavedBlobs()
        GUI.model.drawAllBlobs = True
        GUI.circPack(Extras(sep = 50, shots = 10, offset = 5))


    def test_loading(self):
        GUI = MicroMSQTWindow()
        GUI.setupCanvas(self.tiffImg1)

        GUI.model.coordinateMapper.addPoints((0,0), (0,0))
        GUI.model.coordinateMapper.addPoints((100,0), (100,0))
        GUI.model.coordinateMapper.addPoints((0,100), (0,-100))

        tempDir, f = os.path.split(__file__)
        fname = os.path.join(tempDir, 'test.msreg')

        GUI.saveReg(Extras(fileName = fname))
        GUI.loadReg(Extras(fileName = fname))

        for i in range(500):
            GUI.model.blobCollection[0].append(blob(random.uniform(0,1000),2))
        
        fname = os.path.join(tempDir, 'test.txt')
        GUI.saveCurrentFind(Extras(fileName = fname))
        GUI.loadCellFind(Extras(fileName = fname))
        
        fname = os.path.join(tempDir, 'test.xeo')
        GUI.tspOpt.setChecked(False)
        GUI.saveInstrumentPositions(Extras(fileName = fname, ok = True, text = ''))
        GUI.loadInstrumentPositions(Extras(fileName = fname))

if __name__ == '__main__':
    unittest.main()
