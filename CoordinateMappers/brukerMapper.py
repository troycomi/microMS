from CoordinateMappers import coordinateMapper
from GUICanvases import GUIConstants
from ImageUtilities import blob
import abc
import numpy as np
import itertools

class brukerMapper(coordinateMapper.CoordinateMapper, metaclass=abc.ABCMeta):
    """
    A generic bruker mapper with constants for the slide II adaptor and xeo headers
    all physical points are stored as motor coordinates so if a user enters C5 that has
    to be converted.  Upon saving, the motor coordinates are finally converted in one step.
    """

    '''
    also need to define:
    self.motorCoordinateFilename: filename for intermediate mapping positions.  Should be unique
    '''

    def __init__(self):
        super().__init__()
        self.MTPMapY = {
            'C':0.478261,
            'D':0.391304,
            'E':0.304348,
            'F':0.217391,
            'G':0.130435,
            'J':-0.130435,
            'K':-0.217391,
            'L':-0.304348,
            'M':-0.391304,
            'N':-0.478261,
        }
        
        self.MTPMapX = {
            '5':-0.652174,
            '6':-0.565217,
            '7':-0.478261,
            '8':-0.391304,
            '9':-0.304348,
            '10':-0.217391,
            '11':-0.130435,
            '12':-0.043478,
            '13':0.043478,
            '14':0.130435,
            '15':0.217391,
            '16':0.304348,
            '17':0.391304,
            '18':0.478261,
            '19':0.565217,
            '20':0.652174,
        }
        
        self.header = ('<!-- $Revision: 1.5 $-->\n'
        '<PlateType>\n'
        '\t<GlobalParameters PlateTypeName="MTP Slide Adapter II" ProbeType="MTP"\n'
        '\t                  RowsNumber="100" ChipNumber="1" ChipsInRow="1"\n'
        '\t                  X_ChipOffsetSize="0" Y_ChipOffsetSize="0"\n'
        '\t                  HasDirectLabels="false" HasColRowLabels="true"\n'
        '\t                  HasNearNeighbourCalibrants="false"\n'
        '\t                  ProbeDiameterX="103.5" SampleDiameter="2"\n'
        '\t                  SamplePixelRadius="5" ZoomFactor="1"\n'
        '\t                  FirstCalibrant="TPX1" SecondCalibrant="TPX2" ThirdCalibrant="TPX3"\n'
        '\t                  />\n'
        '\t<MappingParameters mox="56.239998" moy="42.635009" sinphi="0.000000" cosphi="1.000000" '
         'alpha="51.750000" beta="51.750000" tansigma="0.000000"/>\n')
         
        self.footer = """\t</PlateSpots>
    	<AutoTeachSpots>
    		<PlateSpot PositionIndex="0" PositionName="TPX1" UnitCoord_X="-0.729469" UnitCoord_Y="0.550725"/>
    		<PlateSpot PositionIndex="1" PositionName="TPX2" UnitCoord_X="0.729469" UnitCoord_Y="0.550725"/>
    		<PlateSpot PositionIndex="2" PositionName="TPX3" UnitCoord_X="0.729469" UnitCoord_Y="0.057971"/>
    		<PlateSpot PositionIndex="3" PositionName="TPX4" UnitCoord_X="-0.729469" UnitCoord_Y="0.057971"/>
    		<PlateSpot PositionIndex="4" PositionName="TPY1" UnitCoord_X="-0.729469" UnitCoord_Y="-0.057971"/>
    		<PlateSpot PositionIndex="5" PositionName="TPY2" UnitCoord_X="0.729469" UnitCoord_Y="-0.057971"/>
    		<PlateSpot PositionIndex="6" PositionName="TPY3" UnitCoord_X="-0.729469" UnitCoord_Y="-0.550725"/>
    		<PlateSpot PositionIndex="7" PositionName="TPY4" UnitCoord_X="0.729469" UnitCoord_Y="-0.550725"/>
    	</AutoTeachSpots>
    </PlateType>"""        

        #list of all MTP points, used for drawing predicted points
        self.allPoints = list(itertools.product(self.MTPMapX.values(), self.MTPMapY.values()))
        #a tuple of (R,s,t) for PBSR of motor coordinates to MTP coordinate
        self.motor2MTP = None
        #list of motor training coordinates
        self.motor = []
        #list of mtp training points
        self.mtp = []
        
        #load the stored training coordinates
        self.loadStagePoints()

    @abc.abstractmethod
    def loadStagePoints(self):
        '''
        read in or hard code the map from motor coordinates to MTP points 
        should populate the self.motor2MTP = (R,s,t)
        '''

    @abc.abstractmethod
    def isValidMotorCoord(self, inStr):
        '''
        tests if the user-entered string is a valid motor coordinate
        inStr: the string to test if it follows motor coordinate format
        returns true if inStr can be successfully parsed by extractMotorPoint
        '''

    def isValidEntry(self, inStr):
        '''
        Test if the string is a valid entry for a physical coordinate.  
        Can be a motor coordinate or MTP string
        inStr: string to test
        returns true if inStr can be successfully parsed by extractPoint
        '''
        if inStr is None or len(inStr) < 2:
            return False 
        return self.isValidMTP(inStr) or self.isValidMotorCoord(inStr)

    def isValidMTP(self, inStr):
        '''
        Test if the provided string is a valid MTP named coordinate
        inStr: String to test
        returns true if the point is encoded
        '''
        if inStr is None or len(inStr) < 2:
            return False 
        Y = inStr[0].upper()
        X = inStr[1:]
        return X in self.MTPMapX and Y in self.MTPMapY

    def extractPoint(self, inStr):
        '''
        Extract motor coordinate of the supplied point.
        inStr: string to parse
        returns the motor coordinate or None if the string is not valid
        '''
        if self.isValidMTP(inStr):
            return self.extractMTPPoint(inStr)
        elif self.isValidMotorCoord(inStr):
            return self.extractMotorPoint(inStr)
        else:
            return None

    def extractMTPPoint(self, inStr, needMTP = False):
        '''
        From a provided, named MTP point, returns the motor position.
        inStr: the named position to try and parse
        needMTP: optional toggle to get the fractional distance instead of
            translating to a motor coordinate
        returns an (x,y) tuple of motor coordinate, fractional distance (needMTP == True)
            or None if instr is invalid
        '''
        if inStr is None or len(inStr) < 2:
            return None
        Y = inStr[0].upper()
        X = inStr[1:]
    
        if X in self.MTPMapX and Y in self.MTPMapY:
            if needMTP:
                return (self.MTPMapX[X], self.MTPMapY[Y])
            else:
                return self.MTPtoMotor((self.MTPMapX[X], self.MTPMapY[Y]))
        else:
            return None
        
    @abc.abstractmethod
    def extractMotorPoint(self, inStr):
        '''
        given a user-entered motor coordinate, parse out the x and y coordinates
        inStr format could change between instruments if copy/paste is supported
        '''

    def predictName(self, pixelPoint):
        '''
        predict the name of a given pixel position
        By default returns the named mtp coordinate
        '''
        if len(self.physPoints) < 2:
            return ''

        #convert pixel to motor
        motor = self.translate(pixelPoint)
        return self.predictLabel(motor)

    def mtpLabel(self, mtpCoord):
        '''
        From a given mtpCoordinate, returns the named position on an mtp slide II adapter
        mtpCoord: (x,y) tuple in fractional distance coordinates
        '''
        X,Y = mtpCoord

        #return MTP coordinate
        Ymin, Ykey = abs(Y-next(iter(self.MTPMapY.values()))), \
            next(iter(self.MTPMapY.keys()))
        Xmin, Xkey = abs(X-next(iter(self.MTPMapX.values()))), \
            next(iter(self.MTPMapX.keys()))
        for key, val in self.MTPMapY.items():
            if abs(Y-val) < Ymin:
                Ymin, Ykey = abs(Y-val), key
        for key, val in self.MTPMapX.items():
            if abs(X-val) < Xmin:
                Xmin, Xkey = abs(X-val), key
        return Ykey+Xkey

    def predictLabel(self, physPoint):
        '''
        Predicts the label of a registration mark based on the physical position
        physPoint: (x,y) in motor coordinate system
        returns the named, mtp point
        '''
        #motor to MTP
        return self.mtpLabel(self.motorToMTP(physPoint))

    def predictedPoints(self):
        '''
        Gets all the predicted points of the named, mtp positions
        '''
        if len(self.physPoints) < 2:
            return []
        result = []
        for p in self.allPoints:
            result.append(self.invert(self.MTPtoMotor(p)))

        return result

    def motorToMTP(self, motorCoord):
        '''
        Performs translation of the motor coordinate system to fractional distance
        with the self.motor2MTP map.
        motorCoord: (x,y) tuple the motor coordinate
        returns the (xy) tuple in fractional distance
        '''
        (R,s,t) = self.motor2MTP
        mtp = s * R * np.matrix([[motorCoord[0]],[motorCoord[1]]]) + t
        return (mtp[0,0], mtp[1,0])

    def MTPtoMotor(self, MTPcoord):
        '''
        Translates the fractional distance to a motor coordinate.
        MTPcoord: (x,y) tuple a fractional distance
        returns the (x,y) tuple in motor coordinate
        '''
        (R,s,t) = self.motor2MTP
        motor = np.linalg.inv(R)*\
            (np.matrix([[MTPcoord[0]],[MTPcoord[1]]]) - t)/s
        return (motor[0,0], motor[1,0])
    
    def writeXEO(self, filename, blobs):
        '''
        write an xeo file of the provided list of blobs with appropriate header
        and format to use as a Bruker geometry file.
        filename: the xeo file to save
        blobs: list of blobs to save
        '''
        if blobs is None or len(blobs) == 0:
            return
        output = open(filename, 'w')

        output.write(self.header)
        output.write('	<PlateSpots PositionNumber="{}">\n'.format(len(blobs)))
        
        for i,p in enumerate(blobs):
            trans = self.motorToMTP(self.translate((p.X, p.Y)))
            if p.group is None:
                output.write('		<PlateSpot PositionIndex="{0}" PositionName="x_{1:.0f}y_{2:.0f}" UnitCoord_X="{3:.6f}" UnitCoord_Y="{4:.6f}"/>\n'.format(
                i, p.X, p.Y, trans[0], trans[1]))
            else:
                output.write('		<PlateSpot PositionIndex="{0}" PositionName="s_{5:.0f}x_{1:.0f}y_{2:.0f}" UnitCoord_X="{3:.6f}" UnitCoord_Y="{4:.6f}"/>\n'.format(
                i, p.X, p.Y, trans[0], trans[1], p.group))
                    
             
        output.write(self.footer)
        output.close()

    def loadXEO(self,filename):
        '''
        From the provided xeo, parse a list of target positions
        filename: xeo file to parse
        '''
        infile = open(filename, 'r')
        lines = infile.readlines()
        result = []
        #ignore header and footer
        for l in lines[13:-12]:
            toks = l.split('"')
            pos = toks[3].split('_')
            #parse pixel position and group
            if len(pos) == 4:
                offset = 1
                x = int(pos[1+offset][:-1])
                y = int(pos[2+offset])
                s = int(pos[1][:-1])
                result.append(blob.blob(x=x, y=y, group =  s))
            else:
                offset= 0
                x = int(pos[1+offset][:-1])
                y = int(pos[2+offset])
                result.append(blob.blob(x = x, y = y))
            
        return result

    
    def getIntermediateMap(self):
        '''
        populates the intermediate map using the list of motor and mtp points
        '''
        result = []
        for i in range(len(self.motor)):
            result.append( (self.mtpLabel(self.mtp[i]), self.motor[i][0], self.motor[i][1]))

        return result

    
    def loadStagePoints(self):
        '''
        loads in the intermeidate map at self.motorCoordFilename
        '''
        #read in data file
        reader = open(self.motorCoordFilename, 'r')
        for l in reader.readlines():
            toks = l.split('\t')
            self.mtp.append(self.extractMTPPoint(toks[0], needMTP=True));
            self.motor.append((int(toks[1]), int(toks[2])))

        #update map
        self._updateMotor2MTP()
       
    def setIntermediateMap(self, points):
        '''
        From the list of points, generate a new intermediate map
        points: list of (name, x, y) training points
        '''
        #parse returned points
        self.motor = []
        self.mtp = []
        writer = open(self.motorCoordFilename, 'w')
        for t in points:
            self.mtp.append(self.extractMTPPoint(t[0], needMTP=True));
            self.motor.append((int(t[1]), int(t[2])))
            #save new file
            writer.write("{}\t{}\t{}\n".format(t[0], t[1], t[2]))

        writer.close()
        #update motor coordinate
        self._updateMotor2MTP()
    
    def _updateMotor2MTP(self):
        '''
        helper method to perform point based similarity registration
        from the motor coordinate system to the fractional distance
        '''
        self.motor2MTP = self._PBSR(self.motor, self.mtp, False)