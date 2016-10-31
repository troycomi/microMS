import abc

class ConnectedInstrument(object, metaclass=abc.ABCMeta):
    """
    A abstract base class of a connected instrument which
    specifies the most basic set of functions to support for microMS
    to interface with the instrument
    """
    def __init__(self):
        '''
        Create a new connected instrument, with some important constants
        '''
        self.dwellTime = 1#seconds
        self.postAcqusitionWait = 0#seconds
        self.connected = False#has a connection been established
        super().__init__()

    @abc.abstractmethod
    def getPositionXY(self):
        '''
        Returns the current XY position of the connected instrument
        returns a tuple of (x,y)
        '''

    @abc.abstractmethod
    def moveToPositionXY(self, xypos):
        '''
        Move the stage to the specified (x,y) coordinate.
        xypos: (x,y) tuple in the instrument coordinate space
        '''
    
    @abc.abstractmethod
    def move(self, direction, stepSize):
        '''
        Move the stage in the specified direction.  The direction the stage moves 
        should match the probe movement.
        direction: a enumModule.Direction enum
        stepSize: enumModule.StepSize specifying if the step should be large
        '''
    
    @abc.abstractmethod
    def moveProbe(self, direction, stepSize):
        '''
        Move the probe in the specified direction.  This may not be general 
        but is necessary for 3-axis collection
        direction: a enumModule.Direction enum
        stepSize: enumModule.StepSize specifying if the step should be large
        '''

    @abc.abstractmethod
    def setProbePosition(self):
        '''
        Signal the instrument that the probe is in the optimized position
        '''

    @abc.abstractmethod
    def getProbePosition(self):
        '''
        Get the current position of the probe for queries on probe position
        '''

    @abc.abstractmethod
    def collect(self):
        '''
        Perform a single collection at the current position for self.dwellTime (in seconds)
        '''
    
    @abc.abstractmethod
    def collectAll(self, positions):
        '''
        Perform sequential collections at each point specified.
        After collection, the probe should return to self.finalPosition() for
        self.postAcqusitionWait seconds. if postAcqusitionWait == -1 stay at finalPosition.
        positions: list of (x,y) tuples
        '''
        
    @abc.abstractmethod
    def initialize(self, portname):
        '''
        Begin connection with an instrument.
        portname: port to connect two
        '''

    @abc.abstractmethod
    def finalPosition(self):
        '''
        Move the probe to the final "resting" position
        '''