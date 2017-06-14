from CoordinateMappers import coordinateMapper
from ImageUtilities import blob

import numpy as np
import scipy.linalg

class srsMapper(coordinateMapper.CoordinateMapper):
    '''
    A simple mapper for a stimulated raman scattering microscope.  
    Motor coordinates require no additional translation, no inversion
    and output is a tab delimited text file of x/y coordinates
    Has a method for performing autofocusing when the x,y,z coordinates are provided
    '''

    def __init__(self):
        '''
        Set up a new instance of srsMapper
        '''
        super().__init__()
        self.instrumentName = "SRSM"
        self.instrumentExtension = ".txt"
        self.reflectCoordinates = False
        self.focusPoints = []
        self.focusPlane = []

    def isValidEntry(self, inStr):
        '''
        Validate the possible coordinate
        inStr: the string to test, expects two floats separated by a space
        returns true if extract point will successfully parse
        '''
        if ' ' in inStr:
            toks = inStr.split(' ')
            try:
                float(toks[0])
                float(toks[1])
                return True
            except:
                return False
        else:
            return False

    def extractPoint(self, inStr):
        '''
        Parse the physical coordinate from the provided string
        inStr: the input string
        returns an (x,y) tuple of the physical coordinate, 
            an (x,y,z) if another value is provided,
            or None if string is not valid
        '''
        if not self.isValidEntry(inStr):
            return None
        toks = inStr.split(' ')
        if len(toks) == 3:
            try:
                #try to get third value if possible
                return (float(toks[0]), float(toks[1]), float(toks[2]))
            except:
                pass

        return (float(toks[0]), float(toks[1]))

    def predictName(self, pixelPoint):
        '''
        Predicts the physical location from the pixel position.
        Returns the predicted physical, motor position
        '''
        if len(self.physPoints) < 2:
            return ''
        phys = self.translate(pixelPoint)
        if self.focusPlane: #is not empty
            return '{0:.0f} {1:.0f} {2:.1f}'.format(phys[0], phys[1], self.predictFocus(phys))
        return '{0:.0f} {1:.0f}'.format(phys[0], phys[1])

    def predictFocus(self, physPoint):
        if self.update == True:
            self.PBSR()
            self.update = False

        if self.focusPlane:
            return physPoint[0]*self.focusPlane[0] + physPoint[1]*self.focusPlane[1] + self.focusPlane[2]

        else:
            return None


    def predictLabel(self, physPoint):
        '''
        Predict the label of a registration point based on the physical location.
        Since there are no set, named points for the stage this always returns a blank string
        physPoint: (x,y) tuple in physical coordinate space
        '''
        for i, p in enumerate(self.physPoints):
            if physPoint[0] == p[0] and physPoint[1] == p[1]:
                if self.focusPoints[i] is not None:
                    return '{0:.0f} {1:.0f} {2:.1f}'.format(physPoint[0], physPoint[1], self.focusPoints[i])
                else:
                    break

        return '{0:.0f} {1:.0f}'.format(physPoint[0], physPoint[1])

    def predictedPoints(self):
        '''
        Returns a list of predicted points, set points in the pixel coordinate space.
        In this particular implementation, always returns nothing
        '''
        return []

    def saveInstrumentFile(self, filename, blobs):
        '''
        Save the list of target locations as an instrument file
        filename: the file to save
        blobs: the list of target blob locations
        '''
        if blobs is None or len(blobs) == 0:
            return
        output = open(filename, 'w')
        if self.focusPlane:
            output.write('Focus = A*X + B*Y + C\n{0:.6f}\t{1:.6f}\t{2:.6f}\n'\
                .format(self.focusPlane[0],self.focusPlane[1],self.focusPlane[2]))
        else:
            output.write('Focus = A*X + B*Y + C\nNone\tNone\tNone\n')

        for p in blobs:
            phys = self.translate((p.X, p.Y))
            if p.group is not None:
                output.write('x_{0:.0f}y_{1:.0f}\t{2:.0f}\t{3:.0f}\t{4}\n'.format(p.X, p.Y, phys[0], phys[1], p.group))
            else:
                output.write('x_{0:.0f}y_{1:.0f}\t{2:.0f}\t{3:.0f}\n'.format(p.X, p.Y, phys[0], phys[1]))
        output.close()

    def loadInstrumentFile(self, filename):
        '''
        Loads a srsMapper instrument file and returns a list of blobs
        with the target locations.
        filename: the file to load
        returns a list of blob objects
        '''
        result = []
        reader = open(filename, 'r')

        for l in reader.readlines()[2:]:#toss focus plane
            toks = l.split('\t')
            pos = toks[0].split('_')
            #parse pixel position and group
            x = int(pos[1][:-1])
            y = int(pos[2])
            if len(toks) == 4:
                s = int(toks[3])
                result.append(blob.blob(x = x, y = y, group = s))
            else:
                result.append(blob.blob(x = x, y = y))

        return result

    def getIntermediateMap(self):
        '''
        This is ignored as no intermediate map is required
        '''
        return [('Not in use', 0, 0)]

    def setIntermediateMap(self, points):
        '''
        This is ignored as no intermediate map is required
        '''
        pass

    def addPoints(self, pixelPoint, physPoint):
        if isinstance(pixelPoint, tuple) and \
            isinstance(physPoint, tuple) and \
            len(pixelPoint) == 2 and \
            len(physPoint) >= 2:

            if len(physPoint) == 3:
                self.focusPoints.append(physPoint[2])
            else:
                self.focusPoints.append(None)

            return super().addPoints(pixelPoint, physPoint[0:2])

    def clearPoints(self):
        self.focusPoints = []
        self.focusPlane = []
        return super().clearPoints()

    def PBSR(self):
        super().PBSR()
        #determine equation of focus plane
        physX = [self.physPoints[i][0] for i in np.where([f is not None for f in self.focusPoints])[0]]
        physY = [self.physPoints[i][1] for i in np.where([f is not None for f in self.focusPoints])[0]]
        foc = [self.focusPoints[i] for i in np.where([f is not None for f in self.focusPoints])[0]]
        if len(foc) < 3:            
            self.focusPlane = []

        else:
            A = np.c_[physX, physY, np.ones(len(physX))]
            self.focusPlane,_,_,_ = scipy.linalg.lstsq(A, foc)
            self.focusPlane = self.focusPlane.tolist()

    def saveRegistration(self, filename):
        '''
        save the registration file
        filename: the msreg file to write
        '''
        #update if needed and enough points
        if self.update == True and len(self.physPoints) > 2:
            self.PBSR()
            self.update = False
        output = open(filename, 'w')
        output.write(self.instrumentName + '\n')
        #write the registration transformation
        if len(self.physPoints) > 2:
            output.write("S:{}\nR:{}\nT:{}\n".format(self.s, self.R, self.t))
        #write the coordinates
        output.write("image x\timage y\tphysical coordinate\tfocus\n")
        for i,s in enumerate(self.pixelPoints):
            output.write("{}\t{}\t{}\t{}\t{}\n".format(s[0], s[1], 
                         self.physPoints[i][0],self.physPoints[i][1],
                         self.focusPoints[i]))
                         
        output.close()

    def loadRegistration(self, filename):
        '''
        load the msreg file by populating the physical and pixel lists
        filename: the msreg file to load
        '''
        #clear list
        self.physPoints = []
        self.pixelPoints = []
        
        infile = open(filename, 'r')
        
        #toss lines until hitting 'image x'
        l = infile.readline()
        while 'image x' not in l:
            l = infile.readline()

        #then get next
        l = infile.readline()

        #read while lines are not none
        while l:
            #parse out the points
            toks = l.rstrip().split('\t')
            self.pixelPoints.append((int(float(toks[0])), int(float(toks[1]))))
            self.physPoints.append((float(toks[2]), float(toks[3])))
            if toks[4] == 'None':
                self.focusPlane.append(None)
            else:
                self.focusPlane.append(float(toks[4]))
            l = infile.readline()
        #update pbsr if possible
        if len(self.physPoints) > 2:
            self.PBSR()

    def removeClosest(self, pixelPoint):
        closestI = super().removeClosest(pixelPoint)
        self.focusPoints.pop(closestI)