'''
Package with all coordinate system mappers and connected instruments
brukerMapper.py:        An abstract base class implementing coordinateMapper specific
                        for bruker type instruments using their fractional distance.
connectedInstrument.py: An abstract base class specifying functions required for
                        interacting with a connected instrument
coordinateMapper.py:    An abstract base class with some standard methods for mapping
                        pixel positions to physical locations in an instrument.
flexImagingSolarix.py:  An extension of solarixMapper which generates files suitable
                        for acquisition with flexImaging.
oMaldiMapper.py:        Implementation of coordinate mapper for acquisition with the
                        AB Sciex oMaldi server.  Contains methods for slop correction
solarixMapper.py:       Implementation of brukerMapper for the solarix FT-ICR 
                        that generates xeo and xls files for autoacquisition
supportedCoordSystems.py: A collection of coordinatemappers.  Only mappers included here
                        will be accessible to the GUI
ultraflexMapper.py:     An implementation of brukerMapper for the ultraflextreme tof/tof
                        that generates xeo files for autoexecute
zaber3axis.py           Concrete implementation of a connected instrument for an XYZ stage
                        for liquid microjunction extraction.
zaberInterface.py:      An abstract base class with methods for interacting with zaber
                        linear actuators.
zaberMapper.py:         An implementation of coordinateMapper with a connected zaber3axis
                        used for the liquid microjunction extraction.
'''