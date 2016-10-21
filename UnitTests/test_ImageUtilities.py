import unittest
import random
import tempfile
import os
import numpy as np

import PIL
from PIL import ImageDraw, Image
import openslide

from ImageUtilities import blob
from ImageUtilities import blobUtilities
from ImageUtilities import blobFinder
from ImageUtilities import slideWrapper
from ImageUtilities import TSPutil
from ImageUtilities.enumModule import Direction, StepSize

from GUICanvases import GUIConstants

from UnitTests import constants

SKIP_SLOW = constants.skipSlow

class test_blob(unittest.TestCase):
    def test_blobCreation(self):
        #simple case
        blb = blob.blob(1, 2, 8, 0.8, 5)
        self.assertEqual(blb.X, 1)
        self.assertEqual(blb.Y, 2)
        self.assertEqual(blb.radius, 8)
        self.assertEqual(blb.circularity, 0.8)
        self.assertEqual(blb.group, 5)

        #default values
        blb = blob.blob()
        self.assertEqual(blb.X, 0)
        self.assertEqual(blb.Y, 0)
        self.assertEqual(blb.radius, GUIConstants.DEFAULT_BLOB_RADIUS)
        self.assertEqual(blb.circularity, 1)
        self.assertEqual(blb.group, None)

        #low circularity
        blb = blob.blob(circularity = -1)
        self.assertEqual(blb.circularity, 0)
        
        #high circularity
        blb = blob.blob(circularity = 1.1)
        self.assertEqual(blb.circularity, 1)

    def test_shiftCoord(self):
        blb = blob.blob(10, 20)
        self.assertEqual((blb.X, blb.Y), (10, 20))
        blb.shiftCoord(10, 20)
        self.assertEqual((blb.X, blb.Y), (20, 40))
        blb.shiftCoord(5.1, -10)
        self.assertEqual((blb.X, blb.Y), (25.1, 30))

    def test_inBounds(self):
        blb1 = blob.blob(10, 20)
        blb2 = blob.blob(100, 220)
        blb3 = blob.blob(510, 250)
        
        testPoint = (200, 200)
        self.assertTrue(blb1.inBounds(testPoint))
        self.assertFalse(blb2.inBounds(testPoint))
        self.assertFalse(blb3.inBounds(testPoint))
        
        testPoint = (300, 300)
        self.assertTrue(blb1.inBounds(testPoint))
        self.assertTrue(blb2.inBounds(testPoint))
        self.assertFalse(blb3.inBounds(testPoint))
        
        testPoint = (600, 300)
        self.assertTrue(blb1.inBounds(testPoint))
        self.assertTrue(blb2.inBounds(testPoint))
        self.assertTrue(blb3.inBounds(testPoint))

        self.assertFalse(blb3.inBounds(None))

    def test_getXYList(self):
        blbs = []
        result = []
        for i in range(100):
            blbs.append(blob.blob(i, i*2.2, i/2))
            result.append((i, i*2.2))

        self.assertEqual(blob.blob.getXYList(blbs), result)
        
        blbs = []
        result = []

        self.assertEqual(blob.blob.getXYList(blbs), result)
        
        self.assertEqual(blob.blob.getXYList(None), None)

    def test_blobFromSplitString(self):
        instring = "1.0\t2.0\t8.7\n"
        blb = blob.blob.blobFromSplitString(instring.split('\t'))
        self.assertEqual((blb.X, blb.Y, blb.radius, blb.circularity), (1, 2, 8.7, 1))
        
        instring = "1.0\t2.0\t8.7\t.8\n"
        blb = blob.blob.blobFromSplitString(instring.split('\t'))
        self.assertEqual((blb.X, blb.Y, blb.radius, blb.circularity), (1, 2, 8.7, .8))
        
        instring = "\n"
        blb = blob.blob.blobFromSplitString(instring.split('\t'))
        self.assertEqual((blb.X, blb.Y, blb.radius, blb.circularity), (0, 0, GUIConstants.DEFAULT_BLOB_RADIUS, 1))
        
        instring = ""
        blb = blob.blob.blobFromSplitString(instring.split('\t'))
        self.assertEqual((blb.X, blb.Y, blb.radius, blb.circularity), (0, 0, GUIConstants.DEFAULT_BLOB_RADIUS, 1))
        
        blb = blob.blob.blobFromSplitString(None)
        self.assertEqual((blb.X, blb.Y, blb.radius, blb.circularity), (0, 0, GUIConstants.DEFAULT_BLOB_RADIUS, 1))

    def test_toString(self):
        blb = blob.blob()
        self.assertEqual(blb.toString(), "{0:.3f}\t{1:.3f}\t{2:.3f}\t{3:.3f}".format(blb.X, blb.Y, 
                                                           blb.radius, blb.circularity))

        
        for i in range(100):
            blb = blob.blob(i, i*2.2, i/2)
            self.assertEqual(blb.toString(), "{0:.3f}\t{1:.3f}\t{2:.3f}\t{3:.3f}".format(blb.X, blb.Y, 
                                                           blb.radius, blb.circularity))

class test_TSPutil(unittest.TestCase):
    @unittest.skipIf(SKIP_SLOW, "TSP skipped to save time")
    def test_TSPRoute(self):
        self.assertIsNone(TSPutil.TSPRoute(None))

        points = []
        ans = []
        for i in range(100):
            points.append((i,i*2))
            ans.append(i)

        route = TSPutil.TSPRoute(points)
        #the order can be reversed by chance
        self.assertTrue(route == ans or route == list(reversed(ans)))

        import urllib
        input = urllib.request.urlopen('http://www.math.uwaterloo.ca/tsp/vlsi/xqf131.tsp')
        points = []
        for t in input.readlines()[8:]:
            t = t.decode('utf-8')
            t2 = t.split(' ')
            if len(t2) == 3:
                points.append((float(t2[1]), float(t2[2])))
        
        ans = [130,
                126,
                125,
                124,
                123,
                112,
                106,
                105,
                101,
                100,
                99,
                104,
                113,
                117,
                120,
                129,
                122,
                111,
                97,
                92,
                88,
                73,
                52,
                44,
                24,
                17,
                12,
                4,
                11,
                13,
                14,
                15,
                16,
                5,
                0,
                6,
                7,
                1,
                2,
                8,
                9,
                3,
                10,
                23,
                22,
                21,
                20,
                19,
                18,
                25,
                26,
                27,
                28,
                29,
                30,
                31,
                32,
                33,
                34,
                35,
                36,
                37,
                38,
                39,
                40,
                41,
                42,
                43,
                60,
                59,
                58,
                72,
                71,
                79,
                85,
                84,
                83,
                82,
                78,
                68,
                64,
                61,
                65,
                69,
                75,
                70,
                66,
                62,
                57,
                56,
                55,
                51,
                50,
                49,
                48,
                47,
                46,
                54,
                45,
                53,
                63,
                67,
                74,
                76,
                77,
                80,
                81,
                86,
                87,
                91,
                93,
                98,
                107,
                108,
                114,
                118,
                127,
                128,
                121,
                116,
                119,
                115,
                109,
                110,
                102,
                103,
                96,
                95,
                94,
                89,
                90,]

        route = TSPutil.TSPRoute(points)
        self.assertEqual(route, ans)

class test_slideWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tiffImg1 = constants.tiffImg1
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
        #tiff images
        img = slideWrapper.SlideWrapper(self.tiffImg1, [256, 256], 0)
        self.assertEqual(len(img.slides), 2)
        self.assertEqual(len(img.slides[0]), 3)
        self.assertEqual(img.filetype, '.tif')
        self.assertEqual(img.slides[0][0].level_count, img.level_count)
        self.assertEqual(img.slides[0][0].dimensions, img.dimensions)
        self.assertEqual([True]*len(img.slides), img.displaySlides)
        self.assertEqual(img.brightInd, 0)
        self.assertEqual(img.size, [256, 256])
        self.assertEqual(img.lvl, 0)
        self.assertEqual(img.pos, [img.size[0]*2**(img.lvl-1), img.size[1]*2**(img.lvl-1)])

        img = slideWrapper.SlideWrapper(self.tiffImg2, [512, 512])
        self.assertEqual(len(img.slides), 2)
        self.assertEqual(len(img.slides[0]), 3)
        self.assertEqual(img.filetype, '.tif')
        self.assertEqual(img.slides[0][0].level_count, img.level_count)
        self.assertEqual(img.slides[0][0].dimensions, img.dimensions)
        self.assertEqual([True]*len(img.slides), img.displaySlides)
        self.assertEqual(img.brightInd, 0)
        self.assertEqual(img.size, [512, 512])
        self.assertEqual(img.lvl, 0)
        self.assertEqual(img.pos, [img.size[0]*2**(img.lvl-1), img.size[1]*2**(img.lvl-1)])

        img = slideWrapper.SlideWrapper(self.ndpiImg1)
        self.assertEqual(len(img.slides), 2)
        self.assertEqual(len(img.slides[0]), 1)
        self.assertEqual(img.filetype, '.ndpi')
        self.assertEqual(img.slides[0][0].level_count, img.level_count)
        self.assertEqual(img.slides[0][0].dimensions, img.dimensions)
        self.assertEqual([True]*len(img.slides), img.displaySlides)
        self.assertEqual(img.brightInd, 0)
        self.assertEqual(img.size, [1024,1024])
        self.assertEqual(img.lvl, 0)
        self.assertEqual(img.pos, [img.size[0]*2**(img.lvl-1), img.size[1]*2**(img.lvl-1)])

        img = slideWrapper.SlideWrapper(self.ndpiImg2)
        self.assertEqual(len(img.slides), 2)
        self.assertEqual(len(img.slides[0]), 1)
        self.assertEqual(img.filetype, '.ndpi')
        self.assertEqual(img.slides[0][0].level_count, img.level_count)
        self.assertEqual(img.slides[0][0].dimensions, img.dimensions)
        self.assertEqual([True]*len(img.slides), img.displaySlides)
        self.assertEqual(img.brightInd, 0)
        self.assertEqual(img.size, [1024,1024])
        self.assertEqual(img.lvl, 0)
        self.assertEqual(img.pos, [img.size[0]*2**(img.lvl-1), img.size[1]*2**(img.lvl-1)])

        img = slideWrapper.SlideWrapper(self.noDecTif)
        self.assertEqual(len(img.slides), 2)
        self.assertEqual(len(img.slides[0]), 1)
        self.assertEqual(img.filetype, '.tif')
        self.assertEqual(img.slides[0][0].level_count, img.level_count)
        self.assertEqual(img.slides[0][0].dimensions, img.dimensions)
        self.assertEqual([True]*len(img.slides), img.displaySlides)
        self.assertEqual(img.brightInd, 0)
        self.assertEqual(img.size, [1024,1024])
        self.assertEqual(img.lvl, 0)
        self.assertEqual(img.pos, [img.size[0]*2**(img.lvl-1), img.size[1]*2**(img.lvl-1)])

        img = slideWrapper.SlideWrapper(self.multiTif)
        self.assertEqual(len(img.slides), 3)
        self.assertEqual(len(img.slides[0]), 3)
        self.assertEqual(img.filetype, '.tif')
        self.assertEqual(img.slides[0][0].level_count, img.level_count)
        self.assertEqual(img.slides[0][0].dimensions, img.dimensions)
        self.assertEqual([True]*len(img.slides), img.displaySlides)
        self.assertEqual(img.brightInd, 0)
        self.assertEqual(img.size, [1024,1024])
        self.assertEqual(img.lvl, 0)
        self.assertEqual(img.pos, [img.size[0]*2**(img.lvl-1), img.size[1]*2**(img.lvl-1)])

        img = slideWrapper.SlideWrapper(self.singleNdpi)
        self.assertEqual(len(img.slides), 1)
        self.assertEqual(len(img.slides[0]), 1)
        self.assertEqual([True]*len(img.slides), img.displaySlides)

        img = slideWrapper.SlideWrapper(self.tiffMissC1)
        self.assertEqual(len(img.slides), 2)
        self.assertEqual(len(img.slides[1]), 3)
        self.assertEqual([True]*len(img.slides), img.displaySlides)

        img = slideWrapper.SlideWrapper(self.noCTif)
        self.assertEqual(len(img.slides),1)
        self.assertEqual(len(img.slides[0]), 3)

        try:
            img = slideWrapper.SlideWrapper(self.failImg)
            self.fail()
        except ValueError:
            pass

    def test_getImg(self):
        #this test will only catch exceptions, does not check for equality
        imgTif = slideWrapper.SlideWrapper(self.tiffImg1, [256, 256], 0)
        imgNdpi = slideWrapper.SlideWrapper(self.ndpiImg1, [256, 256], 0)
        imgMulti = slideWrapper.SlideWrapper(self.multiTif, [256, 256], 0)
        imgMissing = slideWrapper.SlideWrapper(self.tiffMissC1, [256, 256], 0)

        imgTif.getImg()
        imgNdpi.getImg()
        imgMulti.getImg()
        imgMissing.getImg()

        imgTif.toggleChannel(1)
        imgNdpi.toggleChannel(0)
        imgMissing.toggleChannel(1)
        
        imgTif.getImg()
        imgNdpi.getImg()
        imgMissing.getImg()
        
        imgTif.toggleChannel(0)
        imgNdpi.toggleChannel(1)

        imgTif.getImg()
        imgNdpi.getImg()

        imgMulti.toggleChannel(2)
        imgMulti.getImg()

    def test_getImgHelper(self):
        #this test will only catch exceptions, does not check for equality
        imgTif = slideWrapper.SlideWrapper(self.tiffImg1, [256, 256], 0)
        imgNdpi = slideWrapper.SlideWrapper(self.ndpiImg1, [256, 256], 0)
        imgMulti = slideWrapper.SlideWrapper(self.multiTif, [256, 256], 0)
        imgNoDec = slideWrapper.SlideWrapper(self.noDecTif, [256, 256], 0)

        for img in [ imgTif, imgNdpi, imgMulti, imgNoDec]:
            img.zoomOut()
            img.getImg()
            img.zoomOut()
            img.zoomOut()
            img.zoomOut()
            img.getImg()
            img.zoomOut()
            img.zoomOut()
            img.zoomOut()
            img.getImg()

    def test_getMaxZoomImages(self):
        outDir = tempfile.TemporaryDirectory()
        imgTif = slideWrapper.SlideWrapper(self.tiffImg1, [256, 256], 0)
        imgTif.getMaxZoomImages(outDir.name, [(1000, 1000), (2000, 2000)], imgInd = 0)
        imgTif.getMaxZoomImages(outDir.name, [(1000, 1000), (2000, 2000)], imgInd = 0, invert=True)

    def test_getMaxZoomImg(self):
        imgTif = slideWrapper.SlideWrapper(self.tiffImg1, [256, 256], 0)
        imgTif.getMaxZoomImage()
        imgTif.getMaxZoomImage(position= (200, 200))
        imgTif.getMaxZoomImage(size = (200, 200))
        imgTif.getMaxZoomImage(size = (200, 200), position = (400,400))

    def test_step(self):
        img = slideWrapper.SlideWrapper(self.tiffImg1, [256, 256])
        img.pos = [0,0]

        img.step(Direction.down, StepSize.large)
        self.assertEqual(img.pos, [0, 256])
        img.zoomOut()
        img.zoomOut()
        img.step(Direction.right, StepSize.large)
        self.assertEqual(img.pos, [256*4, 256])

        img = slideWrapper.SlideWrapper(self.ndpiImg1, [200, 200])
        img.pos = [0,0]

        img.zoomOut()
        img.zoomOut()
        img.step(Direction.down, StepSize.large)
        img.step(Direction.right, StepSize.large)
        self.assertEqual(img.pos, [800, 800])
        img.zoomIn()
        img.zoomIn()
        img.step(Direction.up, StepSize.small)
        self.assertEqual(img.pos, [800, 780])
        img.step(Direction.up, StepSize.small)
        self.assertEqual(img.pos, [800, 760])
        img.zoomOut()
        img.step(Direction.left, StepSize.medium)
        self.assertEqual(img.pos, [600, 760])

    def test_zoom(self):
        img = slideWrapper.SlideWrapper(self.tiffImg1, startLvl = -1)
        self.assertEqual(img.lvl, 0)
        img.zoomIn()
        self.assertEqual(img.lvl, 0)
        img.zoomOut()
        self.assertEqual(img.lvl, 1)
        img.zoomIn()
        self.assertEqual(img.lvl, 0)
        img._zoom(5)
        self.assertEqual(img.lvl, 5)
        img._zoom(5)
        self.assertEqual(img.lvl, 8)
        img._zoom(-15)
        self.assertEqual(img.lvl, 0)
        
        img = slideWrapper.SlideWrapper(self.noDecTif, startLvl = -1)
        self.assertEqual(img.lvl, 0)
        img.zoomIn()
        self.assertEqual(img.lvl, 0)
        img.zoomOut()
        self.assertEqual(img.lvl, 1)
        img.zoomIn()
        self.assertEqual(img.lvl, 0)
        img._zoom(5)
        self.assertEqual(img.lvl, 2)
        img._zoom(5)
        self.assertEqual(img.lvl, 2)
        img.resetView()
        self.assertEqual(img.lvl, 0)

        img = slideWrapper.SlideWrapper(self.tiffMissC1, startLvl = -1)
        self.assertEqual(img.lvl, 0)
        img.zoomIn()
        self.assertEqual(img.lvl, 0)
        img.zoomOut()
        self.assertEqual(img.lvl, 1)
        img.zoomIn()
        self.assertEqual(img.lvl, 0)
        img._zoom(5)
        self.assertEqual(img.lvl, 5)
        img._zoom(5)
        self.assertEqual(img.lvl, 8)
        img._zoom(-15)
        self.assertEqual(img.lvl, 0)

        img = slideWrapper.SlideWrapper(self.noCTif, startLvl = -1)
        self.assertEqual(img.lvl, 0)
        img.zoomIn()
        self.assertEqual(img.lvl, 0)
        img.zoomOut()
        self.assertEqual(img.lvl, 1)
        img.zoomIn()
        self.assertEqual(img.lvl, 0)
        img._zoom(5)
        self.assertEqual(img.lvl, 5)
        img._zoom(5)
        self.assertEqual(img.lvl, 8)
        img._zoom(-15)
        self.assertEqual(img.lvl, 0)

    def test_switchType(self):
        img = slideWrapper.SlideWrapper(self.multiTif)
        self.assertEqual(img.displaySlides, [True, True, True])
        img.switchType()
        self.assertEqual(img.displaySlides, [False, True, False])
        img.switchToChannel(0)
        self.assertEqual(img.displaySlides, [True, False, False])
        img.switchType()
        self.assertEqual(img.displaySlides, [False, True, False])
        img.switchType()
        self.assertEqual(img.displaySlides, [False, False, True])
        img.switchType()
        self.assertEqual(img.displaySlides, [True, False, False])
        img.toggleChannel(0)
        self.assertEqual(img.displaySlides, [False, False, False])
        img.switchType()
        self.assertEqual(img.displaySlides, [True, False, False])

    def test_toggleBrightfield(self):
        img = slideWrapper.SlideWrapper(self.multiTif)
        self.assertEqual(img.brightInd, 0)
        img.setBrightfield(0)
        self.assertEqual(img.brightInd, -1)
        img.setBrightfield(0)
        self.assertEqual(img.brightInd, 0)
        img.setBrightfield(2)
        self.assertEqual(img.brightInd, 2)

    def test_moveCenter(self):
        img = slideWrapper.SlideWrapper(self.multiTif, [200, 200])
        img.pos = [0, 0]
        self.assertEqual(img.pos, [0, 0])
        img.moveCenter((100, 100))
        self.assertEqual(img.pos, [0, 0])
        img.moveCenter((150, 100))
        self.assertEqual(img.pos, [50, 0])
        img.moveCenter((100, 150))
        self.assertEqual(img.pos, [50, 50])
        img.moveCenter((150, 150))
        self.assertEqual(img.pos, [100, 100])
        img.moveCenter((50, 50))
        self.assertEqual(img.pos, [50, 50])

        img.zoomOut()
        img.zoomOut()
        img.moveCenter((150, 150))
        self.assertEqual(img.pos, [250, 250])
        img.moveCenter((50, 150))
        self.assertEqual(img.pos, [50, 450])

    def test_getGlobalPoint(self):
        img = slideWrapper.SlideWrapper(self.multiTif, [200, 200])
        img.pos = [0, 0]
        self.assertEqual(img.getGlobalPoint((100,100)), (0,0))
        self.assertEqual(img.getGlobalPoint((150,100)), (50,0))
        self.assertEqual(img.getGlobalPoint((100,150)), (0,50))
        img.zoomOut()
        img.zoomOut()
        self.assertEqual(img.getGlobalPoint((100,150)), (0,200))
        self.assertEqual(img.getGlobalPoint((150,100)), (200,0))
        img.pos = [200, 200]
        self.assertEqual(img.getGlobalPoint((100,150)), (200,400))
        self.assertEqual(img.getGlobalPoint((150,100)), (400,200))
        self.assertEqual(img.getGlobalPoint((100,50)), (200,0))
        self.assertEqual(img.getGlobalPoint((50,100)), (0,200))

    def test_getLocalPoint(self):
        img = slideWrapper.SlideWrapper(self.multiTif, [200, 200])
        img.pos = [0, 0]
        self.assertEqual(img.getLocalPoint((100,100)), [200,200])
        self.assertEqual(img.getLocalPoint((0,100)), [100,200])
        img.zoomOut()
        img.zoomOut()
        self.assertEqual(img.getLocalPoint((100,100)), [125,125])
        self.assertEqual(img.getLocalPoint((0,100)), [100,125])
        img.pos = [200, 200]
        self.assertEqual(img.getLocalPoint((100,200)), [75,100])
        self.assertEqual(img.getLocalPoint((200,100)), [100,75])
        self.assertEqual(img.getLocalPoint((100,40)), [75,60])
        self.assertEqual(img.getLocalPoint((40,100)), [60,75])

    def test_getPointsInBounds(self):
        img = slideWrapper.SlideWrapper(self.multiTif, [200, 200])
        testPoints = [(5,25),(100,150),(200,215),(0,0),(200,200),(500,500),(-20,-56)]
        results, ind = img.getPointsInBounds(testPoints)
        self.assertEqual(ind, [0, 1, 3, 4])
        img.pos = [500, 500]
        results, ind = img.getPointsInBounds(testPoints)
        self.assertEqual(ind, [5])
        img._zoom(5)
        results, ind = img.getPointsInBounds(testPoints)
        self.assertEqual(ind, [0,1,2,3,4,5,6])

    def test_getSize(self):
        img = slideWrapper.SlideWrapper(self.multiTif)
        self.assertEqual(img.getSize(), img.dimensions)
        img = slideWrapper.SlideWrapper(self.ndpiImg1)
        self.assertEqual(img.getSize(), img.dimensions)

    def test_getFluorInt(self):
        img = slideWrapper.SlideWrapper(self.tiffImg1)
        blobs = [blob.blob(10, 10, 10),
                 blob.blob(90, 90, 10),
                 blob.blob(250, 210, 10),
                 blob.blob(500, 240, 10)]
        result = img.getFluorInt(blobs, 2, 1)
        ans = [0, 0.56, 1.485, 5.3525]
        for i in range(len(ans)):
            self.assertAlmostEqual(result[i], ans[i], 2)
        result = img.getFluorInt(blobs, 2, 1,reduceMax=True)
        ans = [0, 1, 3, 8]
        for i in range(len(ans)):
            self.assertAlmostEqual(result[i], ans[i], 2)

        blobs = []
        for i in range(15):
            for j in range(15):
                blobs.append(blob.blob(i*15, j*15))
        img.getFluorInt(blobs, 2, 1)

    @unittest.skipIf(SKIP_SLOW, "Skipping decimation to save time")
    def test_decimateImages(self):
        slideWrapper.SlideWrapper.generateDecimatedImgs(self.smallTif)
        slideWrapper.SlideWrapper.generateDecimatedImgs(self.noCTif)
        slideWrapper.SlideWrapper.generateDecimatedImgs(self.tiffMissC1)

class test_blobUtilities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.noBlbs = []
        cls.blobFinder = blobFinder.blobFinder(None)
        random.seed(1)

        cls.smallBlbList = []
        for i in range(10):
            cls.smallBlbList.append(
                blob.blob(random.randint(0, 1000), random.randint(0,1000), random.normalvariate(8, 1)))
            
        cls.bigBlbList = []
        for i in range(1000):
            cls.bigBlbList.append(
                blob.blob(random.randint(0, 10000), random.randint(0,10000), random.normalvariate(8, 1)))
            
    def test_distanceFilter(self):
        #run on random lists to check everything will run
        self.assertIsNone(
            blobUtilities.blobUtilities.distanceFilter(self.noBlbs, 100)
            )
        self.assertIsNone(
            blobUtilities.blobUtilities.distanceFilter(None, 100)
            )
        blobUtilities.blobUtilities.distanceFilter(self.smallBlbList, 100, 3, True)
        blobUtilities.blobUtilities.distanceFilter(self.bigBlbList, 100)

        #setup small list of blobs with known distances
        blbs = [
            blob.blob(0, 0, 8),
            blob.blob(10, 0, 8),
            blob.blob(10, 10, 8),
            blob.blob(0, 10, 8),
            blob.blob(10, 500, 8),
            blob.blob(100, 500, 8)
            ]
        result = blobUtilities.blobUtilities.distanceFilter(blbs, 50, verbose=True)
        self.assertTrue(result[0])
        self.assertTrue(result[1])
        self.assertTrue(result[2])
        self.assertTrue(result[3])
        self.assertFalse(result[4])
        self.assertFalse(result[5])

    def test_minimumDistances(self):
        #run on random lists to check everything will run
        self.assertIsNone(
            blobUtilities.blobUtilities.minimumDistances(self.noBlbs)
            )
        self.assertIsNone(
            blobUtilities.blobUtilities.minimumDistances(None)
            )
        blobUtilities.blobUtilities.minimumDistances(self.smallBlbList, 3)
        blobUtilities.blobUtilities.minimumDistances(self.bigBlbList)

        #setup small list of blobs with known distances
        blbs = [
            blob.blob(0, 0, 8),
            blob.blob(10, 0, 8),
            blob.blob(10, 10, 8),
            blob.blob(0, 10, 8),
            blob.blob(10, 500, 8),
            blob.blob(100, 500, 8)
            ]
        result = blobUtilities.blobUtilities.minimumDistances(blbs)
        self.assertEqual(result[0], 10)
        self.assertEqual(result[1], 10)
        self.assertEqual(result[2], 10)
        self.assertEqual(result[3], 10)
        self.assertEqual(result[4], 90)
        self.assertEqual(result[5], 90)

        #generate a larger list of blobs, with one very far away to trigger a 
        blbs = []
        for i in range(100):
            blbs.append(blob.blob(random.uniform(0,100), random.uniform(0,100)))

        blbs.append(blob.blob(1e6, 1e6))

        result = blobUtilities.blobUtilities.minimumDistances(blbs, 2, overlap = 1000)
        self.assertEqual(result[-1], 1000)

    def test_saveBlobs(self):
        tempDir = tempfile.TemporaryDirectory()
        blobUtilities.blobUtilities.saveBlobs(os.path.join(tempDir.name, 'small.txt'), 
                                              self.smallBlbList, self.blobFinder)
        blobUtilities.blobUtilities.saveBlobs(os.path.join(tempDir.name, 'small.txt'), 
                                              self.noBlbs, self.blobFinder)
        blobUtilities.blobUtilities.saveBlobs(os.path.join(tempDir.name, 'small.txt'), 
                                              None, self.blobFinder)
        blobUtilities.blobUtilities.saveBlobs(os.path.join(tempDir.name, 'small.txt'), 
                                              self.smallBlbList, self.blobFinder, ['test1', 'test2', 'test3'])

    def test_loadBlobs(self):
        tempDir, f = os.path.split(__file__)
        bigList = os.path.join(tempDir, 'big.txt')
        smallList = os.path.join(tempDir, 'small.txt')
        blobUtilities.blobUtilities.saveBlobs(smallList, 
                                              self.smallBlbList, self.blobFinder)
        self.blobFinder.minCircularity = 0.4
        blobUtilities.blobUtilities.saveBlobs(bigList, 
                                              self.bigBlbList, self.blobFinder)
        blbFind = blobFinder.blobFinder(None)
        outBlbs, outFind = blobUtilities.blobUtilities.loadBlobs(bigList, blbFind)
        self.assertEqual(blbFind.minCircularity, outFind.minCircularity)

        os.remove(bigList)
        os.remove(smallList)

    def test_circularPackPoints(self):
        blobs = [blob.blob(radius = 5),
                 blob.blob(radius = 15),
                 blob.blob(radius = 50),
                 ]

        circ = blobUtilities.blobUtilities.circularPackPoints(blobs, 20, 10, 5)
        totals = [0, 0, 0]
        for b in circ:
            totals[b.group] += 1

        self.assertEqual(totals[0], 4)#min, small R
        self.assertEqual(totals[1], 6)#between 
        self.assertEqual(totals[2], 10)#max, large R

    def test_rectangularlyPackPoints(self):
        blobs = [blob.blob(0,0, 10),
                 blob.blob(100,100,25),
                 blob.blob(1000,1000,50)]

        result = blobUtilities.blobUtilities.rectangularlyPackPoints(blobs, 10, 1, dynamicLayering=False)
        totals = [0, 0, 0]
        for b in result:
            totals[b.group] += 1

        for t in totals:
            self.assertEqual(t, 9)

        for d in blobUtilities.blobUtilities.minimumDistances(result):
            self.assertEqual(d, 10)

        result = blobUtilities.blobUtilities.rectangularlyPackPoints(blobs, 10, 3, dynamicLayering=False)
        totals = [0, 0, 0]
        for b in result:
            totals[b.group] += 1

        for t in totals:
            self.assertEqual(t, 49)

        for d in blobUtilities.blobUtilities.minimumDistances(result):
            self.assertEqual(d, 10)

        result = blobUtilities.blobUtilities.rectangularlyPackPoints(blobs, 10, 0, dynamicLayering=True)
        totals = [0, 0, 0]
        answer = [9, 49, 121]
        for b in result:
            totals[b.group] += 1

        for i in range(len(answer)):
            self.assertEqual(totals[i], answer[i])

        for d in blobUtilities.blobUtilities.minimumDistances(result):
            self.assertEqual(d, 10)

    def test_hexagonallyPackPoints(self):
        blobs = [blob.blob(0,0, 10),
                 blob.blob(100,100,20),
                 blob.blob(1000,1000,30)]

        result = blobUtilities.blobUtilities.hexagonallyClosePackPoints(blobs, 10, 1)
        totals = [0, 0, 0]
        for b in result:
            totals[b.group] += 1

        for t in totals:
            self.assertEqual(t, 7)

        for d in blobUtilities.blobUtilities.minimumDistances(result):
            self.assertAlmostEqual(d, 10,1)

        result = blobUtilities.blobUtilities.hexagonallyClosePackPoints(blobs, 10, 3)
        totals = [0, 0, 0]
        for b in result:
            totals[b.group] += 1

        for t in totals:
            self.assertEqual(t, 37)

        for d in blobUtilities.blobUtilities.minimumDistances(result):
            self.assertAlmostEqual(d, 10,1)

        result = blobUtilities.blobUtilities.hexagonallyClosePackPoints(blobs, 10, 0, dynamicLayering=True)
        totals = [0, 0, 0]
        answer = [7, 19, 37]
        for b in result:
            totals[b.group] += 1

        for i in range(len(answer)):
            self.assertEqual(totals[i], answer[i])

        for d in blobUtilities.blobUtilities.minimumDistances(result):
            self.assertAlmostEqual(d, 10,1)

class test_blobFinding(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.slide = slideWrapper.SlideWrapper(constants.noCTif)
        img = Image.new("RGB", (5000,2500), "black")#blank image
        draw = ImageDraw.Draw(img)
        for x in range (100, 5000, 250):
            for y in range(100, 2500, 250):
                #radius between 10 and 55
                #size 314 and 9498
                rad = 8 + (5*y) // 250
                #color intens between 5 and 247
                intens = int(255*(x/5000))
                col = (intens, intens, intens)
                draw.ellipse((x-rad, y-rad, x+rad, y+rad),col)
        cls.slide.slides[0][0] = openslide.ImageSlide(img)#first image, full zoom
        cls.slide.dimensions = cls.slide.slides[0][0].dimensions

    def test_init(self):
        blbfind = blobFinder.blobFinder(self.slide)

    def test_getSetParams(self):
        blbfind = blobFinder.blobFinder(self.slide, minSize = 50, maxSize = None,
                                        minCircularity = 0.6, maxCircularity = None,
                                        colorChannel = 2, threshold = 75, imageIndex = 0)

        params = blbfind.getParameters()
        self.assertEqual(params['minSize'], 50)
        self.assertEqual(params['maxSize'], None)
        self.assertEqual(params['minCir'], 0.6)
        self.assertEqual(params['maxCir'], None)
        self.assertEqual(params['channel'], 2)
        self.assertEqual(params['thresh'], 75)
        self.assertEqual(params['ImageInd'], 0)

        #should do nothing
        blbfind.setParameterFromSplitString([])
        blbfind.setParameterFromSplitString(None)
        blbfind.setParameterFromSplitString(['NOT ENCODED', 21])
        #should change things
        blbfind.setParameterFromSplitString(['minSize', 21])
        blbfind.setParameterFromSplitString(['maxSize', 100])
        blbfind.setParameterFromSplitString(['minCir', 0.5])
        blbfind.setParameterFromSplitString(['maxCir', 0.9])
        blbfind.setParameterFromSplitString(['channel', 1])
        blbfind.setParameterFromSplitString(['thresh', 200])
        blbfind.setParameterFromSplitString(['ImageInd', 1])
        
        params = blbfind.getParameters()
        self.assertEqual(params['minSize'], 21)
        self.assertEqual(params['maxSize'], 100)
        self.assertEqual(params['minCir'], 0.5)
        self.assertEqual(params['maxCir'], 0.9)
        self.assertEqual(params['channel'], 1)
        self.assertEqual(params['thresh'], 200)
        self.assertEqual(params['ImageInd'], 1)
        
        #None should only change max size and circ
        with self.assertRaises(ValueError):
            blbfind.setParameterFromSplitString(['minSize', 'None\n'])
        blbfind.setParameterFromSplitString(['maxSize', 'None\n'])
        with self.assertRaises(ValueError):
            blbfind.setParameterFromSplitString(['minCir', 'None\n'])
        blbfind.setParameterFromSplitString(['maxCir', 'None\n'])
        with self.assertRaises(ValueError):
            blbfind.setParameterFromSplitString(['channel', 'None\n'])
        with self.assertRaises(ValueError):
            blbfind.setParameterFromSplitString(['thresh', 'None\n'])
        with self.assertRaises(ValueError):
            blbfind.setParameterFromSplitString(['ImageInd', 'None\n'])

        params = blbfind.getParameters()
        self.assertEqual(params['minSize'], 21)
        self.assertEqual(params['maxSize'], None)
        self.assertEqual(params['minCir'], 0.5)
        self.assertEqual(params['maxCir'], None)
        self.assertEqual(params['channel'], 1)
        self.assertEqual(params['thresh'], 200)
        self.assertEqual(params['ImageInd'], 1)

    def test_getBlobChar(self):
        blbfind = blobFinder.blobFinder(self.slide, minSize = 50, maxSize = None,
                                        minCircularity = 0.6, maxCircularity = None,
                                        colorChannel = 2, threshold = 75, imageIndex = 0)
        #no blb
        self.assertEqual(blbfind.getBlobCharacteristics((0,0)), (0,0))
        self.slide.size = [500, 500]
        #all blobs
        for x in range (100, 5000, 250):
            for y in range(100, 2500, 250):
                self.slide.pos = [x, y]
                rad = 8 + (5*y) // 250
                intens = int(255*(x/5000))
                if intens < 75:
                    self.assertEqual(blbfind.getBlobCharacteristics((250,250)), (0,0))
                else:
                    self.assertAlmostEqual((blbfind.getBlobCharacteristics((250,250))[0] -\
                                            (np.pi*rad*rad + np.pi*rad)) / (np.pi*rad*rad + np.pi*rad),#add half of circumference for pixel cutoffs
                                            0, 1)#+/- 10%
                    self.assertAlmostEqual(blbfind.getBlobCharacteristics((250,250))[1],
                                           1.0, 0)

    def test_blobSlide(self):
        for intensity in [50, 100, 200, 300]:
            blbfind = blobFinder.blobFinder(self.slide, imageIndex = 0, threshold=intensity)
            blobs = blbfind.blobSlide()
            for x in range (100, 5000, 250):
                for y in range(100, 2500, 250):
                    #radius between 10 and 55
                    rad = 8 + (5*y) // 250
                    #color intens between 5 and 247
                    intens = int(255*(x/5000))
                    if intens >= intensity:
                        #blob should be in list, have to find and test parameters
                        ind = -1
                        for i,b in enumerate(blobs):
                            dist = (b.X-x)**2 + (b.Y-y)**2
                            if ind == -1 or dist < minDist:
                                minDist = dist
                                ind = i
                        #must be found
                        self.assertNotEqual(ind, -1)
                        self.assertTrue(minDist < 100)#less than 10 pixels away
                        #check x, y, and radius
                        self.assertAlmostEqual(x, blobs[ind].X, 1)
                        self.assertAlmostEqual(y, blobs[ind].Y, 1)
                        self.assertAlmostEqual(0,(rad-blobs[ind].radius)/rad, 0)#relative error should be 0
                        self.assertAlmostEqual(1, blobs[ind].circularity, 0)
                    else:
                        #blob should not be in list
                        ind = -1
                        for i,b in enumerate(blobs):
                            dist = (b.X-x)**2 + (b.Y-y)**2
                            if ind == -1 or dist < minDist:
                                minDist = dist
                                ind = i
                        self.assertTrue(ind == -1 or minDist > 100)

            if intensity == 300:
                self.assertTrue(len(blobs) == 0)


if __name__ == '__main__':
    unittest.main()
