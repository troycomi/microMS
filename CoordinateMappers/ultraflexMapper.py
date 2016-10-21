from CoordinateMappers import brukerMapper
import os

class ultraflexMapper(brukerMapper.brukerMapper):
    """
    coordinate mapper for the ultrafleXtreme
    """
    
    def __init__(self):
       '''
       set up a new ultraflex mapper and set some constants
       '''
       #the intermediate map coordinates
       d, f = os.path.split(__file__)
       self.motorCoordFilename = os.path.join(d, 'ultraflexMapperCoords.txt')
       self.instrumentExtension = '.xeo'
       self.instrumentName = 'ultrafleXtreme'
       super().__init__()
       self.reflectCoordinates = True

        
    def isValidMotorCoord(self, instr):
        '''
        Test if the supplied string is a valid coordinate.  
        Valid strings are separated by a space and contain two ints
        instr: string to test
        returns true if the string is able to be parsed
        '''
        if instr is None:
            return False
        if " " in instr:
            toks = instr.split(" ")
            try:
                int(toks[0])
                int(toks[1])
                return True
            except:
                return False
        else:
            return False

    def extractMotorPoint(self,inStr):
        '''
        Parses the string to generate a motor coordinate
        inStr: the string to parse
        returns an (x,y) tuple if the string successfully parses
        '''
        if not self.isValidMotorCoord(inStr):
            return None
        toks = inStr.split(" ")
        return( (int(toks[0]), int(toks[1])) )

    def loadInstrumentFile(self, filename):
        '''
        Loads an xeo file and returns a list of blobs.
        filename: the xeo file to read
        returns a list of blobs representing the target coordinates
        '''
        return self.loadXEO(filename)

    def saveInstrumentFile(self, filename, blobs):
        '''
        Save the provided list of blobs as an xeo file
        filename: the file to write to
        blobs: list of target blobs
        '''
        self.writeXEO(filename, blobs)
        