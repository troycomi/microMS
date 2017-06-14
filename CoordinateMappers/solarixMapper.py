from CoordinateMappers import brukerMapper
import xlsxwriter
from PyQt5 import QtCore, QtGui, QtWidgets
import os

class solarixMapper(brukerMapper.brukerMapper):
    """
    coordinate mapper for the solarix
    noticeable changes include encoding of motor coordinates, 
    requirement of xls for auto acquisition, and limiting number of blobs/acquisition
    """

    def __init__(self):
        '''
        initialize a new solarix mapper with some specified constants
        '''
        d, f = os.path.split(__file__)
        self.motorCoordFilename = os.path.join(d, 'solarixMapperCoords.txt')
        self.instrumentExtension = '.xeo'
        self.instrumentName = 'solariX'
        super().__init__()
        self.reflectCoordinates = True
        
        self.header = ('<!-- $Revision: 1.5 $-->\n'
        '<PlateType>\n'
        '\t<GlobalParameters PlateTypeName="MTP Slide Adapter II" ProbeType="MTP"\n'
        '\t                  RowsNumber="0" ChipNumber="1" ChipsInRow="1"\n'#overwrite the "RowsNumber" from ultraflex/bruker mapper
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

    def isValidMotorCoord(self,instr):
        '''
        Checks if the supplied string is a valid motor coordinate.
        Solarix motor coordinates are delimited by a '/'
        instr: the string to test
        returns true if the string can be successfully parsed
        '''
        if instr is None:
            return False
        if "/" in instr:
            toks = instr.split("/")
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
        Parse the suppled string to generate a motor point
        inStr: the string to parse
        returns an (x,y) tuple of the motor coordinate
        '''
        if not self.isValidMotorCoord(inStr):
            return None
        toks = inStr.split("/")
        return( (int(toks[0]), int(toks[1])) )

    def loadInstrumentFile(self, filename):
        '''
        Load target locations of a given XEO
        filename: the file to load
        returns a list of blobs of the targets in the file
        '''
        return self.loadXEO(filename)

    def saveInstrumentFile(self, filename, blobs):
        '''
        saves an instrument file of the provided list of blobs
        filename: the file to write to
            if more than 400 points, uses filename as a base name
        blobs: list of target positions
        '''
        if blobs is None or len(blobs) == 0:
            return
        maxPoints = 400
        if len(blobs) > maxPoints:
            fn = filename[:-4]
            for i in range(len(blobs) // maxPoints):
                self.writeXEO(fn + '_' + str(i) + '.xeo', blobs[i*maxPoints:(i+1)*maxPoints])
                self.writeAutoXlsx(fn + '_' + str(i) + '.xlsx', blobs[i*maxPoints:(i+1)*maxPoints])
            #get the remainder
            self.writeXEO(fn + '_' + str(len(blobs)//maxPoints) + '.xeo', blobs[-(len(blobs) % maxPoints):])
            self.writeAutoXlsx(fn + '_' + str(len(blobs)//maxPoints) + '.xlsx', blobs[-(len(blobs) % maxPoints):])
            
        else:#write a single xeo
            self.writeXEO(filename,blobs)
            filename = filename[:-3] + 'xlsx'
            self.writeAutoXlsx(filename, blobs)

    def writeAutoXlsx(self, filename, blobs):
        '''
        Write the xlsx file required for autoexecute
        filename: the xlsx name
        blobs: list of blobs to save
        '''
        workbook =  xlsxwriter.Workbook(filename)
        ws = workbook.add_worksheet()
        
        header = ['Spot Number', 'Chip Number', 'Data Directory', 'Data File Name', 'Method Name', 'Sample Name', 'Comment']
        for i,h in enumerate(header):
            ws.write(0, i, h)
            
        for i,p in enumerate(blobs):
            ws.write(i+1, 0, "x_{0:.0f}y_{1:.0f}".format(p.X, p.Y))
            ws.write(i+1, 1, "0")
            ws.write(i+1, 5, "x_{0:.0f}y_{1:.0f}".format(p.X, p.Y))
            
        workbook.close()

    def predictName(self, pixelPoint):
        '''
        predict the motor coordinate or name from the provided pixel point.
        Tries to read the coordinate from the clipboard of a QT GUI
        pixelPoint: (x,y) tuple of global pixel space
        returns the predicted string
        '''
        clipboard = QtWidgets.QApplication.clipboard()
        if clipboard is not None and \
            clipboard.text() is not None and \
            clipboard.text() != '':
            return clipboard.text()
        return super().predictName(pixelPoint)
