from CoordinateMappers.solarixMapper import solarixMapper
from ImageUtilities.blob import blob
import os

class flexImagingSolarix(solarixMapper):
    '''
    This is another implementation for the solarix which uses
    flexImaging to perform profiling, instead of autoexecute.
    Most functions are directly inherited from the solarix mapper
    '''

    def __init__(self):
        '''
        Create a new solarix mapper
        Only overwriting is the instrument extension and name
        '''
        super().__init__()
        self.instrumentExtension = '.txt'
        self.instrumentName = 'flexImagingSolarix'

    def saveInstrumentFile(self, filename, blobs):
        '''
        Save the instrument file of the provided list of blobs
        filename: the file to write to
        blobs: list of blob targets to save
        file format is a space deliniated x, y, name, region
        '''
        if blobs is None or len(blobs) == 0:
            return
        output = open(filename, 'w')
        output.write('# X-pos Y-pos spot-name region\n')
        #write out the fiducial locations for registration
        for i in range(len(self.physPoints)):
            phys = self.physPoints[i]
            pix = self.pixelPoints[i]
            output.write('{0:.0f} {1:.0f} fiducial{2} 01\n'
                            .format(phys[0], -phys[1], i))

        for b in blobs:
            phys = self.translate((b.X, b.Y))
            if b.group is not None:
                output.write('{0:.0f} {1:.0f} s{4}_x{2:.0f}_y{3:.0f} 01\n'
                             .format(phys[0], -phys[1], b.X, b.Y, b.group))
            else:
                output.write('{0:.0f} {1:.0f} x{2:.0f}_y{3:.0f} 01\n'.format(phys[0], -phys[1], b.X, b.Y))

        output.close()

    def saveInstrumentRegFile(self, filename):
        if self.pixelPoints is None or len(self.pixelPoints) == 0:
            return
        output = open(filename, 'w')
        output.write('# X-pos Y-pos spot-name region\n')

        for p in self.pixelPoints:
            phys = self.translate((p[0], p[1]))
            output.write('{0:.0f} {1:.0f} x{2:.0f}_y{3:.0f} 01\n'.format(phys[0], -phys[1], p[0], p[1]))


    def loadInstrumentFile(self, filename):
        '''
        Loads target locations from a target file
        filename: the file to read
        returns a list of blobs
        '''
        input = open(filename, 'r')
        result = []
        for l in input.readlines()[1:]:
            toks = l.split(' ')
            toks = toks[2].split('_')
            if len(toks) == 3:
                result.append(blob(int(toks[1][1:]), int(toks[2][1:]), group = int(toks[0][1:])))
            elif len(toks) == 2:
                result.append(blob(int(toks[0][1:]), int(toks[1][1:])))
        return result