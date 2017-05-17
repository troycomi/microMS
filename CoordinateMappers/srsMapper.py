from CoordinateMappers import coordinateMapper
from ImageUtilities import blob

class srsMapper(coordinateMapper.CoordinateMapper):
    '''
    A simple mapper for a stimulated raman scattering microscope.  
    Motor coordinates require no additional translation, no inversion
    and output is a tab delimited text file of x/y coordinates
    '''

    def __init__(self):
        '''
        Set up a new instance of srsMapper
        '''
        super().__init__()
        self.instrumentName = "SRSM"
        self.instrumentExtension = ".txt"
        self.reflectCoordinates = False

    def isValidEntry(self, inStr):
        '''
        Validate the possible coordinate
        inStr: the string to test, expects two floats separated by a space
        returns true if extract point will successfully parse
        '''
        if ' ' in inStr:
            toks = instrumentExtentions.split(' ')
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
        toks = inStr.split(' ')

        return (float(toks[0]), float(toks[1]))

    def predictName(self, pixelPoint):
        '''
        Predicts the physical location from the pixel position.
        No set positions so return ''
        '''
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
        for p in blobs:
            if p.group is not None:
                output.write('{0:.0f}\t{1:.0f}\t{2}\n'.format(p.X, p.Y, p.group))
            else:
                output.write('{0:.0f}\t{1:.0f}\n'.format(p.X, p.Y))
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

        for l in reader.readlines():
            toks = l.split('\t')
            if len(toks) == 3:
                #group is encoded
                result.append(blob.blob(float(toks[0]), float(toks[1]), group = int(toks[2])))
            else:
                #no group
                result.append(blob.blob(float(toks[0]), float(toks[1])))

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