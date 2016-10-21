'''
Contains all the supported coordinate systems and a list of 
instances of each type.
'''

###add new import here
from CoordinateMappers import ultraflexMapper
from CoordinateMappers import solarixMapper
from CoordinateMappers import oMaldiMapper
from CoordinateMappers import zaberMapper
from CoordinateMappers import flexImagingSolarix

###add new mapper instance here
supportedMappers = [ultraflexMapper.ultraflexMapper(),
                    solarixMapper.solarixMapper(),
                    flexImagingSolarix.flexImagingSolarix(),
                    oMaldiMapper.oMaldiMapper(),
                    zaberMapper.zaberMapper()]


#check for defined names here
supportedNames = list(map(lambda x: x.instrumentName, supportedMappers))
list(map(lambda x: x.instrumentExtension, supportedMappers))