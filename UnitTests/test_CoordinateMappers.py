import unittest
import random
import os
import numpy as np
import sys

from CoordinateMappers import supportedCoordSystems
from CoordinateMappers import coordinateMapper, brukerMapper, solarixMapper, \
        flexImagingSolarix, ultraflexMapper, oMaldiMapper, zaberMapper, zaber3axis
from ImageUtilities import blob
import itertools
from PyQt4 import QtGui

from UnitTests import constants

app = QtGui.QApplication(sys.argv)

class test_supportedCoordSystems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for m in supportedCoordSystems.supportedMappers:
            m.clearPoints()

    def test_addPoints(self):
        pixels = [(0,0),
                  (100,0),
                  (0,100),
                  (100,100),
                  ]
        random.seed(1)
        for i in range(10):
            s = random.uniform(1, 100)
            theta = random.uniform(0.0, 3.1)
            R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
            t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
            for m in supportedCoordSystems.supportedMappers:
                for p in pixels:
                    if m.reflectCoordinates:    
                        phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                    else:
                        phys = s * R * np.matrix([[p[0]],[p[1]]]) + t
                    m.addPoints(p, (phys[0,0], phys[1,0]))
                self.assertEqual(len(m.physPoints), len(pixels))
                self.assertEqual(m.pixelPoints, pixels)
                m.addPoints(None, phys)
                m.addPoints((0,0), None)
                m.addPoints([0,0], (0,0))
                m.addPoints((0,0), [0,0])
                m.addPoints((0,0), (0))
                m.addPoints((0), (0,0))
                self.assertEqual(len(m.physPoints), len(pixels))
                self.assertEqual(m.pixelPoints, pixels)

                m.clearPoints()
                self.assertEqual(len(m.physPoints), 0)
                self.assertEqual(m.pixelPoints, [])

    def test_PBSR(self):
        pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100),
                    ]
        random.seed(1)
        for i in range(10):
            s = random.uniform(1, 100)
            theta = random.uniform(0.0, 3.1)
            R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
            t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
            for m in supportedCoordSystems.supportedMappers:
                for p in pixels:
                    if m.reflectCoordinates:    
                        phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                    else:
                        phys = s * R * np.matrix([[p[0]],[p[1]]]) + t
                    m.addPoints(p, (phys[0,0], phys[1,0]))
                
                m.PBSR()
                self.assertAlmostEqual(s, m.s, 2)
                self.assertAlmostEqual(t[0,0], m.t[0,0], 2)
                self.assertAlmostEqual(t[1,0], m.t[1,0], 2)
                self.assertAlmostEqual(R[0,0], m.R[0,0], 2)
                self.assertAlmostEqual(R[0,1], m.R[0,1], 2)
                self.assertAlmostEqual(R[1,0], m.R[1,0], 2)
                self.assertAlmostEqual(R[1,1], m.R[1,1], 2)

                m.clearPoints()
                self.assertEqual(len(m.physPoints), 0)
                self.assertEqual(m.pixelPoints, [])

    def test_translateInvert(self):
        pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100),
                    ]
        random.seed(1)
        for i in range(10):
            testPoints = [(random.uniform(0,100),random.uniform(0,100)),
                          (random.uniform(0,100),random.uniform(0,100)),
                          (random.uniform(0,100),random.uniform(0,100))]
            s = random.uniform(1, 100)
            theta = random.uniform(0.0, 3.1)
            R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
            t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
            for m in supportedCoordSystems.supportedMappers:
                with self.assertRaises(KeyError):
                    m.translate(testPoints[0])
                with self.assertRaises(KeyError): 
                    m.invert(testPoints[0])
                for p in pixels:
                    if m.reflectCoordinates:    
                        phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                    else:
                        phys = s * R * np.matrix([[p[0]],[p[1]]]) + t
                    m.addPoints(p, (phys[0,0], phys[1,0]))
                
                for p in testPoints:
                    if m.reflectCoordinates:    
                        phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                    else:
                        phys = s * R * np.matrix([[p[0]],[p[1]]]) + t
                    phys = (phys[0,0], phys[1,0])
                    self.assertAlmostEqual(m.translate(p)[0], phys[0])
                    self.assertAlmostEqual(m.translate(p)[1], phys[1])
                    m.update = True
                    self.assertAlmostEqual(m.invert(phys)[0], p[0])
                    self.assertAlmostEqual(m.invert(phys)[1], p[1])

                m.clearPoints()
                self.assertEqual(len(m.physPoints), 0)
                self.assertEqual(m.pixelPoints, [])

    def test_removeClosest(self):
        pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100),
                    ]
        random.seed(1)
        for i in range(10):
            s = random.uniform(1, 100)
            theta = random.uniform(0.0, 3.1)
            R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
            t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
            for m in supportedCoordSystems.supportedMappers:
                for p in pixels:
                    if m.reflectCoordinates:    
                        phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                    else:
                        phys = s * R * np.matrix([[p[0]],[p[1]]]) + t
                    m.addPoints(p, (phys[0,0], phys[1,0]))
                
                self.assertEqual(len(m.physPoints), len(pixels))
                self.assertEqual(len(m.pixelPoints), len(pixels))
                self.assertTrue(pixels[2] in m.pixelPoints)

                m.removeClosest(pixels[2])
                self.assertEqual(len(m.physPoints), len(pixels)-1)
                self.assertEqual(len(m.pixelPoints), len(pixels)-1)
                self.assertFalse(pixels[2] in m.pixelPoints)
                
                m.clearPoints()
                self.assertEqual(len(m.physPoints), 0)
                self.assertEqual(m.pixelPoints, [])

    def test_highestDeviation(self):
        pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100),
                    (50,50)
                    ]
        random.seed(1)
        for i in range(10):
            s = random.uniform(1, 100)
            theta = random.uniform(0.0, 3.1)
            R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
            t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
            for m in supportedCoordSystems.supportedMappers:
                with self.assertRaises(KeyError):
                    m.highestDeviation()
                for j, p in enumerate(pixels):
                    if m.reflectCoordinates:    
                        phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                    else:
                        phys = s * R * np.matrix([[p[0]],[p[1]]]) + t

                    if j == len(pixels) -1:
                        m.addPoints(p, (phys[0,0]+20, phys[1,0]-10))

                    elif j == len(pixels) -2:
                        m.addPoints(p, (phys[0,0]+5, phys[1,0]-2))
                    else:
                        m.addPoints(p, (phys[0,0], phys[1,0]))

                
                self.assertEqual(m.highestDeviation(), len(pixels)-1)
                m.removeClosest(pixels[0])
                self.assertEqual(m.highestDeviation(), len(pixels)-2)
                
                m.clearPoints()
                self.assertEqual(len(m.physPoints), 0)
                self.assertEqual(m.pixelPoints, [])

    def test_saveLoadRegistration(self):
        pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100)
                    ]
        random.seed(1)

        tempDir, f = os.path.split(__file__)
        fn = os.path.join(tempDir, 'mapper.txt')

        for i in range(10):
            s = random.uniform(1, 100)
            theta = random.uniform(0.0, 3.1)
            R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
            t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
            for m in supportedCoordSystems.supportedMappers:
                for j, p in enumerate(pixels):
                    if m.reflectCoordinates:    
                        phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                    else:
                        phys = s * R * np.matrix([[p[0]],[p[1]]]) + t

                    m.addPoints(p, (phys[0,0], phys[1,0]))
                
                m.PBSR()
                self.assertAlmostEqual(s, m.s, 2)
                self.assertAlmostEqual(t[0,0], m.t[0,0], 2)
                self.assertAlmostEqual(t[1,0], m.t[1,0], 2)
                self.assertAlmostEqual(R[0,0], m.R[0,0], 2)
                self.assertAlmostEqual(R[0,1], m.R[0,1], 2)
                self.assertAlmostEqual(R[1,0], m.R[1,0], 2)
                self.assertAlmostEqual(R[1,1], m.R[1,1], 2)

                m.saveRegistration(fn)

                m.clearPoints()
                self.assertEqual(len(m.physPoints), 0)
                self.assertEqual(m.pixelPoints, [])

                m.loadRegistration(fn)
                self.assertAlmostEqual(s, m.s, 2)
                self.assertAlmostEqual(t[0,0], m.t[0,0], 2)
                self.assertAlmostEqual(t[1,0], m.t[1,0], 2)
                self.assertAlmostEqual(R[0,0], m.R[0,0], 2)
                self.assertAlmostEqual(R[0,1], m.R[0,1], 2)
                self.assertAlmostEqual(R[1,0], m.R[1,0], 2)
                self.assertAlmostEqual(R[1,1], m.R[1,1], 2)

                m.clearPoints()

        os.remove(fn)

    #many of these will only catch runtime errors, does not check for correctness
    def test_saveInstrumentFiles(self):
        pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100)
                    ]

        random.seed(1)
        blobs = []
        for i in range(100):
            blobs.append(blob.blob(random.uniform(0,1000), random.uniform(0,1000)))

        tempDir, f = os.path.split(__file__)
        
        for m in supportedCoordSystems.supportedMappers:
            fn = os.path.join(tempDir, 'mapper' + m.instrumentExtension)
            for i in range(10):
                s = random.uniform(1, 100)
                theta = random.uniform(0.0, 3.1)
                R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
                t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
                for j, p in enumerate(pixels):
                    if m.reflectCoordinates:    
                        phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                    else:
                        phys = s * R * np.matrix([[p[0]],[p[1]]]) + t

                    m.addPoints(p, (phys[0,0], phys[1,0]))
                
                m.saveInstrumentRegFile(fn)
                blbs = m.loadInstrumentFile(fn)
                blbs = blob.blob.getXYList(blbs)
                for j in range(len(pixels)):
                    self.assertEqual(pixels[j][0], blbs[j][0])
                    self.assertEqual(pixels[j][1], blbs[j][1])

                m.saveInstrumentFile(fn, blobs)
                blbs = m.loadInstrumentFile(fn)
                blbs = blob.blob.getXYList(blbs)
                bs = blob.blob.getXYList(blobs)
                for j in range(len(blobs)):
                    self.assertAlmostEqual(bs[j][0], blbs[j][0], 0)
                    self.assertAlmostEqual(bs[j][1], blbs[j][1], 0)

                m.saveInstrumentFile(fn, None)
                m.saveInstrumentFile(fn, [])
                    
                m.clearPoints()

            os.remove(fn)

    def test_saveInstrumentFilesWGroups(self):
        pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100)]

        random.seed(1)
        blobs = []
        for i in range(100):
            blobs.append(blob.blob(random.uniform(0,1000), random.uniform(0,1000), group = i//10))

        tempDir, f = os.path.split(__file__)
        
        for m in supportedCoordSystems.supportedMappers:
            fn = os.path.join(tempDir, 'mapper' + m.instrumentExtension)
            for i in range(10):
                s = random.uniform(1, 100)
                theta = random.uniform(0.0, 3.1)
                R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
                t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
                for j, p in enumerate(pixels):
                    if m.reflectCoordinates:    
                        phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                    else:
                        phys = s * R * np.matrix([[p[0]],[p[1]]]) + t

                    m.addPoints(p, (phys[0,0], phys[1,0]))

                m.saveInstrumentFile(fn, blobs)
                blbs = m.loadInstrumentFile(fn)
                xy = blob.blob.getXYList(blbs)
                bs = blob.blob.getXYList(blobs)
                for j in range(len(blobs)):
                    self.assertAlmostEqual(bs[j][0], xy[j][0], 0)
                    self.assertAlmostEqual(bs[j][1], xy[j][1], 0)
                    self.assertEqual(blobs[j].group, blbs[j].group)

                m.saveInstrumentFile(fn, None)
                m.saveInstrumentFile(fn, [])
                    
                m.clearPoints()

            os.remove(fn)

    def test_getSetIntermediateMap(self):
        for m in supportedCoordSystems.supportedMappers:
            intMap = m.getIntermediateMap()
            m.setIntermediateMap(intMap)

    def test_predictedPoints(self):
        pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100)]
        random.seed(1)
        for m in supportedCoordSystems.supportedMappers:
            self.assertEqual(m.predictedPoints(), [])

            s = random.uniform(1, 100)
            theta = random.uniform(0.0, 3.1)
            R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
            t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
            for j, p in enumerate(pixels):
                if m.reflectCoordinates:    
                    phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                else:
                    phys = s * R * np.matrix([[p[0]],[p[1]]]) + t
                m.addPoints(p, (phys[0,0], phys[1,0]))
            m.predictedPoints()
            m.clearPoints()

class test_brukerMapper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brukerMappers = [
                solarixMapper.solarixMapper(),
                flexImagingSolarix.flexImagingSolarix(),
                ultraflexMapper.ultraflexMapper()
            ]

        cls.pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100)
                    ]

    def test_ValidMotor(self):
        allPoints = list(map(lambda x: x[1]+x[0],
                            itertools.product(self.brukerMappers[0].MTPMapX.keys(), 
                                           self.brukerMappers[0].MTPMapY.keys())))
        failPoints = ['C3', 'A6', 'CC', None, '', 'C', '1', '14', 'CC4', '6D']
        for m in self.brukerMappers:
            for p in allPoints:
                self.assertTrue(m.isValidEntry(p))
                self.assertTrue(m.isValidMTP(p))
            for p in failPoints:
                self.assertFalse(m.isValidEntry(p))
                self.assertFalse(m.isValidMTP(p))

    def test_extractPoint(self):
        allPoints = list(map(lambda x: x[1]+x[0],
                            itertools.product(self.brukerMappers[0].MTPMapX.keys(), 
                                           self.brukerMappers[0].MTPMapY.keys())))
        allMTP = list(itertools.product(self.brukerMappers[0].MTPMapX.values(), 
                                        self.brukerMappers[0].MTPMapY.values()))
        failPoints = ['C3', 'A6', 'CC', None, '', 'C', '1', '14', 'CC4', '6D']
        for m in self.brukerMappers:
            for i, p in enumerate(allPoints):
                m.extractPoint(p)
                self.assertEqual(m.extractMTPPoint(p, True), allMTP[i])

            for p in failPoints:
                self.assertIsNone(m.extractPoint(p))
                self.assertIsNone(m.extractMTPPoint(p))
                self.assertIsNone(m.extractMTPPoint(p,True))

class test_ultraflexMapper(unittest.TestCase):
    def test_isValidMotorCoord(self):
        m = ultraflexMapper.ultraflexMapper()
        goodPoints = ["123 456", "-123 +456",  "123 456 ", "123 456 789"]
        badPoints = ["123,456", "123, 456", "q23 456", "123 #56", "10,000 20,000"]
        for p in goodPoints:
            self.assertTrue(m.isValidEntry(p))
            self.assertTrue(m.isValidMotorCoord(p))

        for p in badPoints:
            self.assertFalse(m.isValidEntry(p))
            self.assertFalse(m.isValidMotorCoord(p))

    def test_extractMotorPoint(self):
        m = ultraflexMapper.ultraflexMapper()
        goodPoints = ["123 456", "-123 +456",  "123 456 ", "123 456 789"]
        answers = [(123, 456), (-123, 456), (123, 456), (123, 456)]
        badPoints = ["123,456", "123, 456", "q23 456", "123 #56", "10,000 20,000"]
        for i, p in enumerate(goodPoints):
            self.assertEqual(m.extractPoint(p), answers[i])
            self.assertEqual(m.extractMotorPoint(p), answers[i])

        for p in badPoints:
            self.assertIsNone(m.extractPoint(p))
            self.assertIsNone(m.extractMotorPoint(p))

    def test_predictName(self):
        m = ultraflexMapper.ultraflexMapper()
        pixels = [(0,0),
                    (10000,0),
                    (0,10000),
                    (10000,10000)]
        MTPPoints = ["C5", "C6", "D5", "D6"]
        self.assertEqual(m.predictName((0,0)), "")
        for i in range(len(pixels)):
            #setup a simple transformation
            m.addPoints(pixels[i], m.extractMTPPoint(MTPPoints[i]))
            
        for i in range(len(pixels)):
            self.assertEqual(m.predictName(pixels[i]), MTPPoints[i])
            self.assertEqual(m.predictLabel(m.extractMTPPoint(MTPPoints[i])), MTPPoints[i])

class test_solarixMapper(unittest.TestCase):
    def test_isValidMotorCoord(self):
        m = solarixMapper.solarixMapper()
        goodPoints = ["123/456/10", "123/456", "-123/-456"]
        badPoints = ["123\456", "123 456", "q34/456"]
        for p in goodPoints:
            self.assertTrue(m.isValidEntry(p))
            self.assertTrue(m.isValidMotorCoord(p))

        for p in badPoints:
            self.assertFalse(m.isValidEntry(p))
            self.assertFalse(m.isValidMotorCoord(p))

    def test_extractMotorPoint(self):
        m = solarixMapper.solarixMapper()
        goodPoints = ["123/456/10", "123/456", "-123/-456"]
        answers = [(123, 456), (123, 456), (-123, -456)]
        badPoints = ["123|456", "123 456", "q34/456"]
        for i, p in enumerate(goodPoints):
            self.assertEqual(m.extractPoint(p), answers[i])
            self.assertEqual(m.extractMotorPoint(p), answers[i])

        for p in badPoints:
            self.assertIsNone(m.extractPoint(p))
            self.assertIsNone(m.extractMotorPoint(p))

    def test_predictName(self):
        m = solarixMapper.solarixMapper()
        pixels = [(0,0),
                    (10000,0),
                    (0,10000),
                    (10000,10000)]
        MTPPoints = ["C5", "C6", "D5", "D6"]
        goodPoints = ["123/456/10", "123/456", "-123/-456"]
        for i in range(len(pixels)):
            #setup a simple transformation
            m.addPoints(pixels[i], m.extractMTPPoint(MTPPoints[i]))
            
        for i in range(len(pixels)):
            self.assertEqual(m.predictLabel(m.extractMTPPoint(MTPPoints[i])), MTPPoints[i])

        clipboard = QtGui.QApplication.clipboard()
        clipboard.clear()

        for p in goodPoints:
            clipboard.setText(p)
            self.assertEqual(m.predictName((0,0)), p)

        clipboard.clear()

    def test_saveInstrumentFileLarge(self):
        pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100)
                    ]

        random.seed(1)
        blobs = []
        for i in range(1000):
            blobs.append(blob.blob(random.uniform(0,1000), random.uniform(0,1000)))

        tempDir, f = os.path.split(__file__)
        
        m = solarixMapper.solarixMapper()
        fn = os.path.join(tempDir, 'mapper' + m.instrumentExtension)
        for i in range(10):
            s = random.uniform(1, 100)
            theta = random.uniform(0.0, 3.1)
            R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
            t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
            for j, p in enumerate(pixels):
                if m.reflectCoordinates:    
                    phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                else:
                    phys = s * R * np.matrix([[p[0]],[p[1]]]) + t

                m.addPoints(p, (phys[0,0], phys[1,0]))

            m.saveInstrumentFile(fn, blobs)
            blbs = m.loadInstrumentFile(os.path.join(tempDir, 'mapper_0.xeo'))
            blbs = blob.blob.getXYList(blbs)
            bs = blob.blob.getXYList(blobs[0:900])
            for j in range(len(bs)):
                self.assertAlmostEqual(bs[j][0], blbs[j][0], 0)
                self.assertAlmostEqual(bs[j][1], blbs[j][1], 0)
                    
            m.clearPoints()

    def test_saveInstrumentFileLarge2(self):
        pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100)
                    ]

        random.seed(1)
        blobs = []
        for i in range(901):
            blobs.append(blob.blob(random.uniform(0,1000), random.uniform(0,1000)))

        tempDir, f = os.path.split(__file__)
        
        m = solarixMapper.solarixMapper()
        fn = os.path.join(tempDir, 'mapper' + m.instrumentExtension)
        for i in range(10):
            s = random.uniform(1, 100)
            theta = random.uniform(0.0, 3.1)
            R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
            t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
            for j, p in enumerate(pixels):
                if m.reflectCoordinates:    
                    phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                else:
                    phys = s * R * np.matrix([[p[0]],[p[1]]]) + t

                m.addPoints(p, (phys[0,0], phys[1,0]))

            m.saveInstrumentFile(fn, blobs)
            blbs = m.loadInstrumentFile(os.path.join(tempDir, 'mapper_0.xeo'))
            blbs = blob.blob.getXYList(blbs)
            bs = blob.blob.getXYList(blobs[0:900])
            for j in range(len(bs)):
                self.assertAlmostEqual(bs[j][0], blbs[j][0], 0)
                self.assertAlmostEqual(bs[j][1], blbs[j][1], 0)
                    
            m.clearPoints()

class test_oMaldiMapper(unittest.TestCase):
    def test_isValidMotorCoord(self):
        m = oMaldiMapper.oMaldiMapper()
        goodPoints = ["123 456", "-123 +456",  "123 456 ", "123 456 789"]
        badPoints = ["123,456", "123, 456", "q23 456", "123 #56", "10,000 20,000"]
        for p in goodPoints:
            self.assertTrue(m.isValidEntry(p))

        for p in badPoints:
            self.assertFalse(m.isValidEntry(p))

    def test_extractMotorPoint(self):
        m = oMaldiMapper.oMaldiMapper()
        goodPoints = ["123 456", "-123 +456",  "123 456 ", "123 456 789"]
        answers = [(123, 456), (-123, 456), (123, 456), (123, 456)]
        badPoints = ["123,456", "123, 456", "q23 456", "123 #56", "10,000 20,000"]
        for i, p in enumerate(goodPoints):
            self.assertEqual(m.extractPoint(p), answers[i])

        for p in badPoints:
            self.assertIsNone(m.extractPoint(p))

    def test_predict(self):
        m = oMaldiMapper.oMaldiMapper()
        self.assertEqual(m.predictName((0,0)), "")
        
        pixels = [(0,0),
                    (10000,0),
                    (0,10000),
                    (10000,10000)]

        self.assertEqual(m.predictLabel((1600, 30400)), 1)
        self.assertEqual(m.predictLabel((1600, 27000)), 11)
        self.assertEqual(m.predictLabel((27200, 27000)), 19)
        self.assertEqual(m.predictLabel((27200, 14000)), 59)

    def test_saveCornerCases(self):
        m = oMaldiMapper.oMaldiMapper()
        pixels = [(0,0),
                    (100,0),
                    (0,100),
                    (100,100)
                    ]

        random.seed(1)
        blobs = []
        for i in range(100):
            blobs.append(blob.blob(random.uniform(0,1000), random.uniform(0,1000)))

        tempDir, f = os.path.split(__file__)

        fn = os.path.join(tempDir, 'mapper' + m.instrumentExtension)
        for i in range(10):
            s = random.uniform(1, 100)
            theta = random.uniform(0.0, 3.1)
            R = np.matrix([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
            t = np.matrix([[random.uniform(-100,100)],[random.uniform(-100,100)]])
            for j, p in enumerate(pixels):
                if m.reflectCoordinates:    
                    phys = s * R * np.matrix([[p[0]],[-p[1]]]) + t
                else:
                    phys = s * R * np.matrix([[p[0]],[p[1]]]) + t

                m.addPoints(p, (phys[0,0], phys[1,0]))

            m.saveInstrumentFile(fn, blobs)
            #test removal of txt file prior to reading instrument points
            os.remove(os.path.join(tempDir, "mapper.txt"))
            blbs = m.loadInstrumentFile(fn)
            self.assertEqual(blbs, [])
                    
            m.clearPoints()

        os.remove(fn)

    def test_slopCorrection(self):
        m = oMaldiMapper.oMaldiMapper()
        

        #test slop in a particular order
        points = [(5,5),#start in center
                  (4,6),#continue movement
                  (3,5),#change in y direction +-
                  (4,4),#change in x direction -+
                  (5,5),#change in y direction -+
                  (4,6),#change in x direction +-
                  (4,7),#only in y ++
                  (5,7),#only in x -+
                  (5,8),#only in y ++
                  (4,8),#only in x +-
                  (4,7),#only in y +-
                  (5,7),#only in x -+
                  (5,8),#only in y -+
                  (6,9),
                  (5,8),#both +-
                  (4,7),
                  (5,8)#both -+
                  ]

        answer = [(5,5),
                  (4,6),
                  (3,4.8),
                  (4.1,3.8),
                  (5.1,5),
                  (4,6),
                  (4,7),
                  (5.1,7),
                  (5.1,8),
                  (4,8),
                  (4,6.8),
                  (5.1,6.8),
                  (5.1,8),
                  (6.1,9),
                  (5,7.8),
                  (4,6.8),
                  (5.1,8)
                  ]

        output = m.SlopCorrection(points, 0.1, 0.2)
        for i in range(len(points)):
            self.assertEqual(output[i], answer[i])

class test_zaberMapper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapper = zaberMapper.zaberMapper()
        cls.goodPort = 'COM3' #expected port to find instrument
        cls.ports = zaberMapper.zaberMapper().connectedInstrument.findPorts()

    def setUp(self):
        self.mapper = zaberMapper.zaberMapper()

    def tearDown(self):
        del self.mapper
        
    def test_isValid(self):
        goodPoints = ["123 456", "-23 -456", "23.1 12.3"]
        badPoints = ["asdf asdf", "123,456", "123, 456", "123/456"]

        for p in goodPoints:
            self.assertTrue(self.mapper.isValidEntry(p))

        for p in badPoints:
            self.assertFalse(self.mapper.isValidEntry(p))

    def test_extractPoint(self):
        goodPoints = ["123 456", "-23 -456", "23.1 12.3"]
        answers = [(123, 456),(-23, -456),(23.1, 12.3)]
        badPoints = ["asdf asdf", "123,456", "123, 456", "123/456"]

        for i, p in enumerate(goodPoints):
            self.assertEqual(self.mapper.extractPoint(p), answers[i])

        for p in badPoints:
            self.assertIsNone(self.mapper.extractPoint(p))

    def test_predictNameNoConnect(self):
        self.assertEqual(self.mapper.predictName((10,10)), '')
        self.assertEqual(self.mapper.predictName((10,100)), '')

    def test_predictLabel(self):
        self.assertEqual(self.mapper.predictLabel((10,10)), '')
        self.assertEqual(self.mapper.predictLabel((10,100)), '')

    def test_predictedPointsNoConnect(self):
        self.assertEqual(self.mapper.predictedPoints(), [])
        
    def test_predictNameConnect(self):
        if self.goodPort in self.ports:
            self.mapper.connectedInstrument.initialize(self.goodPort)
            self.assertEqual(self.mapper.predictName((10,10)), '100000.0 100000.0')
            self.assertEqual(self.mapper.predictName((10,100)), '100000.0 100000.0')
            self.mapper.connectedInstrument.moveToPositionXY((10000, 12000))
            self.assertEqual(self.mapper.predictName((10,10)), '10000.0 12000.0')
            self.assertEqual(self.mapper.predictName((10,100)), '10000.0 12000.0')

    def test_predictedPointsConnect(self):
        self.assertEqual(self.mapper.predictedPoints(), [])
        if self.goodPort in self.ports:
            self.mapper.connectedInstrument.initialize(self.goodPort)
            #no teaching
            self.assertEqual(self.mapper.predictedPoints(), [])
            for p in [(0,0), (1000,1000), (1500, 1000)]:
                self.mapper.addPoints(p, p)
            self.assertAlmostEqual(self.mapper.predictedPoints()[0][0], 100000, 1)
            self.assertAlmostEqual(self.mapper.predictedPoints()[0][1], 100000, 1)
            self.mapper.connectedInstrument.moveToPositionXY((10000, 12000))
            self.assertAlmostEqual(self.mapper.predictedPoints()[0][0], 10000, 1)
            self.assertAlmostEqual(self.mapper.predictedPoints()[0][1], 12000, 1)

class test_zaber3axis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instrument = zaber3axis.Zaber3Axis()
        cls.ports = cls.instrument.findPorts()
        cls.goodPort = 'COM3' #expected port to find instrument
        cls.badPort = 'COM4' #expected port to find nothing

    def setUp(self):
        self.instrument = zaber3axis.Zaber3Axis()

    def tearDown(self):
        del self.instrument
        
    def test_initialize(self):
        if self.goodPort in self.ports:
            if self.badPort not in self.ports:
                self.instrument.initialize(self.badPort)
                self.assertFalse(self.instrument.connected)

                #these should do nothing
                self.instrument.homeAll()
                self.instrument.checkReplies(3)
                self.assertIsNone(self.instrument.getPositionXY())
                self.instrument.moveToPositionXY((0,10))
                self.instrument.move(Direction.up, True)
                self.instrument.collect()
                self.instrument.collectAll([(0,0)])
                self.instrument.moveProbe(Direction.up, False)
                self.instrument.setProbePosition()
                self.instrument.toggleProbe()

            self.instrument.initialize(self.goodPort)
            self.assertTrue(self.instrument.connected)

    def test_getAndMove(self):
        if self.goodPort in self.ports:
            self.instrument.initialize(self.goodPort)
            self.assertTrue(self.instrument.connected)

            self.assertEqual(self.instrument.getPositionXY(), (100000,100000))
            testPoints = [(1000,2000), (2000,2000), (2000, 1000)]
            for p in testPoints:
                self.instrument.moveToPositionXY(p)
                self.assertEqual(self.instrument.getPositionXY(), p)
                
            self.instrument.homeAll()
            self.assertEqual(self.instrument.getPositionXY(), (0,0))


    def test_move(self):
        if self.goodPort in self.ports:
            self.instrument.initialize(self.goodPort)
            self.assertTrue(self.instrument.connected)

            self.assertEqual(self.instrument.getPositionXY(), (100000, 100000))

            for i in range(3):
                for big in [True, False]:
                    for d in [Direction.up, Direction.left, Direction.down, Direction.right]:
                        self.instrument.move(d, big)

            self.instrument.homeAll()
            self.assertEqual(self.instrument.getPositionXY(), (0,0))

    def test_moveProbe(self):
        if self.goodPort in self.ports:
            self.instrument.initialize(self.goodPort)
            self.assertTrue(self.instrument.connected)

            self.assertEqual(self.instrument.getPositionXY(), (100000, 100000))
            self.instrument._send(self.instrument.zdev, self.instrument.COMMANDS["MOVE_ABS"], 100000)
            self.instrument._receive()

            for i in range(3):
                for big in [True, False]:
                    for d in [Direction.up, Direction.down]:
                        self.instrument.moveProbe(d, big)

            self.instrument.homeAll()
            self.assertEqual(self.instrument.getPositionXY(), (0,0))

    def test_setToggleProbe(self):
        if self.goodPort in self.ports:
            self.instrument.initialize(self.goodPort)
            self.assertTrue(self.instrument.connected)

            self.assertEqual(self.instrument.getPositionXY(), (100000, 100000))
            self.instrument._send(self.instrument.zdev, self.instrument.COMMANDS["MOVE_ABS"], 100000)
            self.instrument._receive()
            
            self.assertEqual(self.instrument.getPosition(self.instrument.zdev), 100000)

            self.instrument.toggleProbe()#does nothing
            self.assertEqual(self.instrument.getPosition(self.instrument.zdev), 100000)

            self.instrument.setProbePosition()
            self.assertEqual(self.instrument.bottomPosition, 100000)
            self.assertEqual(self.instrument.getPosition(self.instrument.zdev), 
                             100000 - self.instrument.largeZstep*5)
            self.assertFalse(self.instrument.atBottom)
            
            #move to bottom
            self.instrument.toggleProbe()
            self.assertEqual(self.instrument.getPosition(self.instrument.zdev), 
                             100000)
            self.assertTrue(self.instrument.atBottom)
            
            #raise
            self.instrument.toggleProbe()
            self.assertEqual(self.instrument.getPosition(self.instrument.zdev), 
                             100000 - self.instrument.largeZstep*5)
            self.assertFalse(self.instrument.atBottom)
            
            #again
            self.instrument.toggleProbe()
            self.assertEqual(self.instrument.getPosition(self.instrument.zdev), 
                             100000)
            self.assertTrue(self.instrument.atBottom)

            #should reset at bottom
            self.instrument.moveProbe(Direction.up, False)
            self.assertFalse(self.instrument.atBottom)
            self.instrument.toggleProbe()
            self.assertTrue(self.instrument.atBottom)
            self.instrument.moveProbe(Direction.down, False)
            self.assertFalse(self.instrument.atBottom)
            self.instrument.toggleProbe()
            self.assertTrue(self.instrument.atBottom)

            #moving should toggle up
            self.instrument.move(Direction.left, True)
            self.assertFalse(self.instrument.atBottom)
            self.instrument.toggleProbe()
            self.assertTrue(self.instrument.atBottom)
            self.instrument.moveToPositionXY((100000, 100000))
            self.assertFalse(self.instrument.atBottom)
            self.instrument.toggleProbe()
            self.assertTrue(self.instrument.atBottom)

            #and after home
            self.instrument.homeAll()
            self.assertFalse(self.instrument.atBottom)

            self.assertEqual(self.instrument.getPositionXY(), (0,0))


    def test_collect(self):
        if self.goodPort in self.ports:
            #return 
            self.assertFalse(self.instrument.connected)
            self.instrument._collect((0,0))
            self.instrument.initialize(self.goodPort)
            self.assertTrue(self.instrument.connected)

            self.assertEqual(self.instrument.getPositionXY(), (100000, 100000))
            self.instrument._send(self.instrument.zdev, self.instrument.COMMANDS["MOVE_ABS"], 100000)
            self.instrument._receive()

            self.instrument.setProbePosition()
            self.assertEqual(self.instrument.bottomPosition, 100000)
            self.assertEqual(self.instrument.getPosition(self.instrument.zdev), 
                             100000 - self.instrument.largeZstep*5)
            self.assertFalse(self.instrument.atBottom)

            self.instrument.collect() #collect while raise
            self.assertFalse(self.instrument.atBottom)
            self.instrument.toggleProbe()
            self.assertTrue(self.instrument.atBottom)
            self.instrument.collect() #collect while lowered
            self.assertFalse(self.instrument.atBottom)

            testPoints = [(100000,110000), (110000,110000), (110000, 100000)]
            for p in testPoints:
                self.instrument.moveToPositionXY(p)
                self.assertEqual(self.instrument.getPositionXY(), p)
                self.instrument.collect()
                self.assertFalse(self.instrument.atBottom)
                self.assertEqual(self.instrument.getPositionXY(), p)

            self.instrument.homeAll()
            self.assertEqual(self.instrument.getPositionXY(), (0,0))

    def test_collectAll(self):
        if self.goodPort in self.ports:
            self.instrument.initialize(self.goodPort)
            self.assertTrue(self.instrument.connected)

            self.assertEqual(self.instrument.getPositionXY(), (100000, 100000))
            self.instrument._send(self.instrument.zdev, self.instrument.COMMANDS["MOVE_ABS"], 100000)
            self.instrument._receive()

            self.instrument.setProbePosition()
            self.assertEqual(self.instrument.bottomPosition, 100000)
            self.assertEqual(self.instrument.getPosition(self.instrument.zdev), 
                             100000 - self.instrument.largeZstep*5)
            self.assertFalse(self.instrument.atBottom)

            testPoints = [(100000,110000), (110000,110000), (110000, 100000), (100000, 100000)]
            self.instrument.collectAll(testPoints)

            #should home after completion
            self.assertEqual(self.instrument.getPositionXY(), (0,0))

    def test_failureConditions(self):
        with self.assertRaises(ValueError):
            self.instrument._send(0,0)
        with self.assertRaises(ValueError):
            self.instrument._receive()

if __name__ == '__main__':
    unittest.main()
