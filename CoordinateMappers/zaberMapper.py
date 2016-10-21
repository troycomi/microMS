from CoordinateMappers import coordinateMapper
from CoordinateMappers import zaber3axis

from ImageUtilities import blob

class zaberMapper(coordinateMapper.CoordinateMapper):
    '''
    A coordinate mapper of the zaber XYZ stage.
    Has a connected instrument, but otherwise the coordinate
    mapping is fairly simple.
    '''

    def __init__(self):
        '''
        Set up a new instance of zaberMapper
        '''
        super().__init__()
        #note there is a connected instrument
        self.isConnectedToInstrument = True
        self.instrumentExtension = '.txt'
        self.instrumentName = 'Zaber LMJ'
        self.reflectCoordinates = False
        #set up the instrument as a 3axis zaber stage
        self.connectedInstrument = zaber3axis.Zaber3Axis()

    def isValidEntry(self, inStr):
        '''
        Validate the possible coordinate
        inStr: the string to test, expects two floats separated by a space
        returns true if extract point will successfully parse
        '''
        if " " in inStr:
            toks = inStr.split(" ")
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
            or None if string is not valid
        '''
        if not self.isValidEntry(inStr):
            return None
        toks = inStr.split(" ")
        return( (float(toks[0]), float(toks[1])) )

    def predictName(self, pixelPoint):
        '''
        Predicts the physical location from the pixel position.
        When the instrument is connected, reads in the actual physical point
        pixelPoint: (x,y) tuple in global coordinate space
        '''
        #read position if instrument is initialized
        if self.connectedInstrument.connected:
            xy = self.connectedInstrument.getPositionXY()
            return '{} {}'.format(xy[0], xy[1])
        #else return blank string
        return ''

    def predictLabel(self, physPoint):
        '''
        Predict the label of a registration point based on the physical location.
        Since there are no set, named points for the stage this always returns a blank string
        physPoint: (x,y) tuple in physical coordinate space
        '''
        return ''
    
    def predictedPoints(self):
        '''
        Returns a list of predicted points, set points in the pixel coordinate space.
        In this particular implementation, only returns the current position 
        of the probe when the instrument is connected and enough training points 
        are provided.
        '''
        if len(self.physPoints) < 2 or not self.connectedInstrument.connected:
            return []
        else:
            phys = self.connectedInstrument.getPositionXY()
            return [self.invert(phys)]

    def loadInstrumentFile(self, filename):
        '''
        Loads a zaberMapper instrument file and returs a list of blobs
        with the target locations.
        filename: the file to load
        returns a list of blob objects
        '''
        result = []
        reader = open(filename, 'r')

        for l in reader.readlines():
            toks = l.split('\t')
            if len(toks) == 3:
                #group is encoded
                result.append(blob.blob(float(toks[0]), float(toks[1]), group = int(toks[2])))
            else:
                #no group
                result.append(blob.blob(float(toks[0]), float(toks[1])))

        return result

    def saveInstrumentFile(self, filename, blobs):
        '''
        Save the list of target locations as an instrument file
        filename: the file to save
        blobs: the list of target blob locations
        '''
        if blobs is None or len(blobs) == 0:
            return
        output = open(filename, 'w')
        for p in blobs:
            if p.group is not None:
                output.write('{0:.0f}\t{1:.0f}\t{2}\n'.format(p.X, p.Y, p.group))
            else:
                output.write('{0:.0f}\t{1:.0f}\n'.format(p.X, p.Y))
        output.close()
    
    def getIntermediateMap(self):
        '''
        This is ignored as no intermeidate map is required
        '''
        return [('Not in use', 0, 0)]

    def setIntermediateMap(self, points):
        '''
        This is ignored as no intermediate map is required
        '''
        pass