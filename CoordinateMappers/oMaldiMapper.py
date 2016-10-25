from CoordinateMappers import coordinateMapper
import os
import numpy as np
import itertools

from ImageUtilities import blob

class oMaldiMapper(coordinateMapper.CoordinateMapper):
    '''
    coordinate mapper of an ab sciex oMaldi server.
    Tries to account for slide slop in generation of instrument files
    '''

    def __init__(self):
        '''
        creates a new oMaldiMapper and sets some constant values
        '''
        super().__init__()

        self.instrumentExtension = '.ptn'
        self.instrumentName = 'oMALDI'
        self.reflectCoordinates = True

        #these are rough estimates, but shouldn't be used beyond predicting labels
        self.SIMSMapY = {
            0:30400,
            10:27200,
            20:24000,
            30:20800,
            40:17600,
            50:14400,
            60:11200,
            70:8000,
            80:4800,
            90:1600
        }
        
        self.SIMSMapX = {
            10:30400,
            9:27200,
            8:24000,
            7:20800,
            6:17600,
            5:14400,
            4:11200,
            3:8000,
            2:4800,
            1:1600
        }
        
        self.allPoints = list(itertools.product(self.SIMSMapX.values(), self.SIMSMapY.values()))

    def isValidEntry(self, inStr):
        '''
        Tests if the string is a valid motor entry.
        Sample entry is two ints separated by a space
        inStr: string to test
        returns true if the string can be successfully parsed
        '''
        if " " in inStr:
            toks = inStr.split(" ")
            try:
                int(toks[0])
                int(toks[1])
                return True
            except:
                return False
        else:
            return False

    def extractPoint(self, inStr):
        '''
        Extracts a motor coordinate from the provided string.
        inStr: the string to parse
        returns an (x,y) tuple in physical coordinate space
        '''
        if not self.isValidEntry(inStr):
            return None
        toks = inStr.split(" ")
        return( (int(toks[0]), int(toks[1])) )

    def predictName(self, pixelPoint):
        '''
        Predicts the motor coordinate from a pixel position.
        pixelPoint: (x,y) tuple
        returns a blank string
        '''
        return ""

    def predictLabel(self, physicalPoint):
        '''
        Predict the label of a physical point.
        physicalPoint: (x,y) tuple of the position to predict
        returns a string of the position of a standard 100 spot plate
        '''
        Y = physicalPoint[1]
        X = physicalPoint[0]
        Ymin, Ykey = abs(Y-next(iter(self.SIMSMapY.values()))), \
            next(iter(self.SIMSMapY.keys()))
        Xmin, Xkey = abs(X-next(iter(self.SIMSMapX.values()))), \
            next(iter(self.SIMSMapX.keys()))
        #find closest position
        for key, val in self.SIMSMapY.items():
            if abs(Y-val) < Ymin:
                Ymin, Ykey = abs(Y-val), key
        for key, val in self.SIMSMapX.items():
            if abs(X-val) < Xmin:
                Xmin, Xkey = abs(X-val), key
        return Ykey+Xkey

    def predictedPoints(self):
        '''
        Returns a list of predicted points of the standard 100 spot plate
        '''
        if len(self.physPoints) < 2:
            return []
        result = []
        for p in self.allPoints:
            result.append(self.invert(p))
        return result

    def loadInstrumentFile(self, filename):
        '''
        Loads all the targets associated with a given instrument file.
        filename: the ptn file to load.  Actually gets information from a partner text file.
        returns a list of blobs of the target locations
        '''
        result = []
        if os.path.exists(filename[0:-4] + '.txt'):
            reader = open(filename[0:-4] + '.txt', 'r')
            for l in reader.readlines():
                toks = l.split('\t')
                if len(toks) == 3:
                    result.append(blob.blob(float(toks[0]), float(toks[1]), group = int(toks[2])))
                else:
                    result.append(blob.blob(float(toks[0]), float(toks[1])))
        else:
            print('{} continaing pixel positions not found!'.format(filename[0:-4] + '.txt'))
        return result

    def saveInstrumentFile(self, filename, blobs):  
        '''
        Save the list of blobs to the provided filename
        filename: the base ptn filename to save
        blobs: list of blobs to save
        '''
        if blobs is None or len(blobs) == 0:
            return
        slop = 0.1
        #assuming start at spot 43:
        scale = 0.0031249999999999984;
        rot = np.matrix([[ -1.00000000e+00,   2.77555756e-16],
        [  2.22044605e-16,  -1.00000000e+00]]);
        transl = np.matrix([[ 30.],
        [-50.]]);

        points = [];                
                
        output = open(filename[0:-4] + '.txt', 'w')
        for b in blobs:
            trans = self.translate((b.X,b.Y))
            result = scale * rot * np.matrix([[trans[0]],[-trans[1]]]) + transl
            points.append((result[0,0], result[1,0]))
            if b.group is not None:
                output.write('{0:.0f}\t{1:.0f}\t{2}\n'.format(b.X, b.Y, b.group))
            else:
                output.write('{0:.0f}\t{1:.0f}\n'.format(b.X, b.Y))
        output.close()

        points = self.SlopCorrection(points, slop, slop)        
        
        output = open(filename, 'w')
        for p in points:
            output.write('{0:.3f}\t{1:.3f}\n'.format(p[0], p[1]))
        output.close()
        
    def SlopCorrection(self, points, xcorr, ycorr):
        '''
        Attempts to correct for linear actuator motor slop in the stage.
        As the stage changes direction from positive to negative direction
        in either axis, a constant value is added or subtracted to make the stage
        move a little further or less depending on slop in drive screw.
        assume start at spot 43, equal x and y slop, apply when changing directions
        pattern value at start is 5,5 coming in direction of 6,4
        points: list of points to visit
        xcorr: x slop correction value
        ycorr: y slop correction value
        returns a new list of points with slop correction
        '''
        path = []
        output = []
        #path contains the last "two points visited" in x and y
        #to determine what kind of slope correction, if any, to apply
        path.append((6,4))
        path.append((5,5))
        xslop = 0
        yslop = 0
        for p in points:
            path.append(p)
            #update xslop
            # +-
            if path[0][0] < path[1][0] and path[1][0] > path[2][0]:
                xslop -= xcorr
            #-+
            elif path[0][0] > path[1][0] and path[1][0] < path[2][0]:
                xslop += xcorr
            #no change, forward point          
            elif path[1][0] == path[2][0]:
                path[1] = (path[0][0], path[1][1])
            #update yslop
            # +-
            if path[0][1] < path[1][1] and path[1][1] > path[2][1]:
                yslop -= ycorr
            #-+
            elif path[0][1] > path[1][1] and path[1][1] < path[2][1]:
                yslop += ycorr
            #no change, forward point          
            elif path[1][1] == path[2][1]:
                path[1] = (path[1][0], path[0][1])
            
            output.append((p[0]+xslop,p[1]+yslop))
            path.pop(0)
        return output
    
    def getIntermediateMap(self):
        '''
        The intermeidate map is hard coded for now
        '''
        return [('Not in use', 0, 0)]

    def setIntermediateMap(self, points):
        '''
        This is unused
        '''
        pass
