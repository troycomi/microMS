import abc
import numpy as np

from ImageUtilities import blob

class CoordinateMapper(object, metaclass=abc.ABCMeta):
    """
    An abstract interface of a coordinate mapper object.
    Used to translate between coordinate systems for each supported instrument
    """

    def __init__(self):
        self.physPoints = []
        self.pixelPoints = []
        self.update = False

        self.isConnectedToInstrument = False
        self.connectedInstrument = None
        self.reflectCoordinates = False

        '''
        also need to define the strings
        self.instrumentExtension: extension of file used by instrument for target positions
        self.instrumentName:Name of instrument for display and logic.  Should be unique

        finally supportedCoordSystems needs to be updated with the import and supportedMappers
        '''

    @abc.abstractmethod
    def isValidEntry(self, inStr):
        '''
        checks if the user-entered coordinate is valid
        inStr: the user entry
        returns a bool, true if the entry was valid
        '''

    @abc.abstractmethod
    def extractPoint(self, inStr):
        '''
        converts the entered point to a physical coordinate
        in simplest case can just parse the input, could require other conversions
        inStr: user entry, should be validated prior to passing in
        returns a tuple in pysical coordinates
        '''
    
    @abc.abstractmethod
    def predictName(self, pixelPoint):
        '''
        used to predict the user entry, which is frequently overwritten when
        setting a registration point. Can be a "named" coordinate to match instrumentation
        or just the predicted physical coordinate
        pixelPoint: a tuple of the x,y pixel position
        returns a string with the predicted input
        '''
    
    @abc.abstractmethod
    def predictLabel(self, physPoint):
        '''
        given a phyisical position of a registration point, the label to draw on the image
        can be a 'named' coordinate or a short position
        '''

    @abc.abstractmethod
    def predictedPoints(self):
        '''
        returns a list of pixel points of predicted 'named' positions
        used to show the predicted grid if the instrument has preset positions
        Returns [] if not implemented or not enough training points are set
        '''
        
    @abc.abstractmethod
    def loadInstrumentFile(self, filename):
        '''
        read in an instrument file produced by saveInstrumentFile
        filename: the name of the instrument file
        should return a list of blobs used in blob finding, 
        radius and circularity can be hard coded as GUIConstants.DEFAULT_BLOB_RADIUS and 1 for display purposes
        '''

    @abc.abstractmethod
    def saveInstrumentFile(self, filename, blobs):
        '''
        write the file used by the instrument to profile each position
        typically requires special formatting.  It is also possible to 
        write meta data in a separate file to simplify loading later
        filename: output file name
        blobs: list of blobs
        '''
    
    def saveInstrumentRegFile(self, filename):
        '''
        Similar to saveInstrumentFile, but saves the positions of the 
        pixelPoints used for registration
        '''
        regBlobs = [blob.blob(p[0], p[1]) for p in self.pixelPoints]
        self.saveInstrumentFile(filename, regBlobs)

    @abc.abstractmethod
    def getIntermediateMap(self):
        '''
        return the coordinates needed to construct the intermediate map, where necessary
        the intermediate map is used to convert from physical positions to a coordinate system
        used by the instrument.  These are typically set points on the instrument which could change.
        the output should be a list of tuples which are used to populate a table in the GUI.
        Subclasses should save and load these points as needed, preferably to a txt file with the class name
        '''

    @abc.abstractmethod
    def setIntermediateMap(self, points):
        '''
        Update the intermediate map based on the points supplied.  The user will likely update some of the points
        so format should be similar to the structure returned by getIntermediate map
        points: a list of tuples
        '''
    
    def PBSR(self):
        '''
        calculates R, t and s for point based registration from pixels (x) to 
        physical positions (y)
        '''
        (self.R, self.s, self.t) = self._PBSR(self.pixelPoints, self.physPoints, self.reflectCoordinates)

    def translate(self, pixelPoint):
        '''
        Translate a provided pixel point to physical coordinate
        pixelPoint: a x,y tuple in pixel space
        '''
        return self._translate(pixelPoint, self.reflectCoordinates)
        
    def invert(self, physPoint):
        '''
        Translate a provided physical point to pixel coordinate
        physPoint: a x,y tuple in physical space
        '''
        return self._invert(physPoint, self.reflectCoordinates)

    def addPoints(self, pixelPoint, physPoint):
        '''
        Adds the provided x,y tuples to the appropriate lists
        Does some type checking and signals the need for a pbsr update
        pixelPoint: (x,y) tuple in global pixel space
        physPoint: (x,y) tuple of physical coordinate
        '''
        #check if tuples of list two
        if isinstance(pixelPoint, tuple) and \
                isinstance(physPoint, tuple) and \
                len(pixelPoint) == 2 and \
                len(physPoint) == 2:

            self.physPoints.append(physPoint)
            self.pixelPoints.append(pixelPoint)
            self.update = True

    def clearPoints(self):
        '''
        Resets all physical and pixel points
        '''
        self.physPoints = []
        self.pixelPoints = []
        self.update = True

    def _translate(self, pixelPoint, reflected):
        '''
        a helper method of translate that has the extra variable for reflection
        pixelPoint: (x,y) tuple in global pixel space
        reflected: boolean to signal if the two coordinate spaces are reflected
        returns an (x,y) tuple in physical space
        '''
        #can't perform transformation
        if len(self.physPoints) < 2:
            raise KeyError('Not enough training points')
            
        #update if needed
        if self.update == True:
            self.PBSR()
            self.update = False

        #if reflecting, negate the y axis
        if reflected:    
            result = self.s * self.R * np.matrix([[pixelPoint[0]],[-pixelPoint[1]]]) + self.t
        else:
            result = self.s * self.R * np.matrix([[pixelPoint[0]],[pixelPoint[1]]]) + self.t
        
        return (result[0,0], result[1,0])

    def _invert(self, physPoint, reflected):
        '''
        helper method for inverting a physical point to a pixel position
        physPoint: (x,y) coordinate of physical position
        reflected: boolean toggle to indicate if the coordinate spaces are relfections
        return (x,y) in pixel positions
        '''
        #not enough training points
        if len(self.physPoints) < 2:
            raise KeyError('Not enough training points')
            
        #update transformation as needed
        if self.update == True:
            self.PBSR()
            self.update = False
            
        #calculate inverse transformation
        result = np.linalg.inv(self.R)*\
            (np.matrix([[physPoint[0]],[physPoint[1]]]) - self.t)/self.s
        
        #negate y axis if reflected
        if reflected:
            return (result[0,0], -result[1,0])
        else:
            return (result[0,0], result[1,0])
                
    def _PBSR(self, X, Y, reflected = False):
        '''
        calculate R, t and s for point based registration from pixel (x) to 
        physical (y)
        X: list of tuples of pixel coordinates
        Y: list of tuples of physical coordinates
        reflected: boolean switch to indicate if the coordinates are related by a reflection
        returns (R, s, t)
        y ~ s*R*x+t
        '''
        flip = -1 if reflected else 1        
        
        xbar = [0,0]
        ybar = [0,0]
        n = len(X)
        for i in range(n):
            xbar[0] += X[i][0]
            xbar[1] += flip*X[i][1]
            ybar[0] += Y[i][0]
            ybar[1] += Y[i][1]
        xbar[0] /= n
        xbar[1] /= n
        ybar[0] /= n
        ybar[1] /= n
        
        xtilde = list(map(lambda x: (x[0]-xbar[0], (flip*x[1])-xbar[1]), X))
        ytilde = list(map(lambda x: (x[0]-ybar[0], x[1]-ybar[1]), Y))

        H = np.matrix('0 0; 0 0')
        
        for s,p in zip(xtilde, ytilde):
            H = H + np.outer(s,p)
            
        U,s,V = np.linalg.svd(H)
     
        R = np.dot(
                np.dot(V, 
                       np.matrix([[1,0],[0,np.linalg.det(np.dot(V,U))]])),
                np.transpose(U))
                
        sTop = 0
        sBot = 0
        for s,p in zip(xtilde, ytilde):
            sTop += np.dot(np.dot(R,s), p)
            sBot += np.dot(s,s)
        s = sTop/sBot
        s = s[0,0]

        if s < 0:
            s = -s
            R = -R
        
        sbar = np.matrix([[xbar[0]],[xbar[1]]])
        pbar = np.matrix([[ybar[0]],[ybar[1]]])
        t = pbar-s*R*sbar 
        return (R,s,t)
                
    def removeClosest(self, pixelPoint):
        '''
        remove the closest fiducial pair to the provided pixel point
        pixelPoint: (x,y) tuple to remove
        '''
        closestI = 0
        if self.pixelPoints:
            #start with distance to fist point
            closestDist = (self.pixelPoints[0][0]-pixelPoint[0])**2+(self.pixelPoints[0][1]-pixelPoint[1])**2
            for i,p in enumerate(self.pixelPoints):
                #update if p is closer
                if (p[0]-pixelPoint[0])**2+(p[1]-pixelPoint[1])**2 < closestDist:
                    closestDist = (p[0]-pixelPoint[0])**2+(p[1]-pixelPoint[1])**2
                    closestI = i
            #remove points and signal the need to update
            self.pixelPoints.pop(closestI)
            self.physPoints.pop(closestI)
            self.update = True

            
    def highestDeviation(self):
        '''
        returns the index of pixelPoints with the highest deviation
        in target registration error
        '''
        if len(self.physPoints) < 2:
            raise KeyError('Not enough training points')
            
        #update as needed
        if self.update == True:
            self.PBSR()
            self.update = False
            
        #get all predicted pixel positions
        predPixPoints = list(map(lambda x: self.invert(x), self.physPoints))
        dists = []
        #calculate deviations (dist squared)
        for i in range(len(predPixPoints)):
            dists.append((self.pixelPoints[i][0] - predPixPoints[i][0])**2 + 
                         (self.pixelPoints[i][1] - predPixPoints[i][1])**2)
        #return max deviation
        return np.argmax(dists)
         
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
            l = infile.readline()
        #update pbsr if possible
        if len(self.physPoints) > 2:
            self.PBSR()

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
        output.write("image x\timage y\tphysical coordinate\n")
        for i,s in enumerate(self.pixelPoints):
            output.write("{}\t{}\t{}\t{}\n".format(s[0], s[1], 
                         self.physPoints[i][0],self.physPoints[i][1]))
                         
        output.close()
