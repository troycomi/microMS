from CoordinateMappers import zaberInterface
from CoordinateMappers import connectedInstrument
from ImageUtilities.enumModule import Direction, StepSize
import time

class Zaber3Axis(zaberInterface.ZaberInterface, 
                 connectedInstrument.ConnectedInstrument):
    '''
    A connected zaber linear stage with XYZ axes.
    Note the multiple inheritance
    '''

    def __init__(self):
        '''
        Setup, but not connect the stage
        Initializes a few constants that may need changing and some instance variables
        '''
        super().__init__()
        self.xdev = 2
        self.ydev = 1
        self.zdev = 3

        self.smallStep = 500 #microsteps

        self.smallZstep = 50 #microsteps
        
        self.mediumFactor = 10
        self.largeFactor = 100
        self.giantFactor = 1000

        #the position of the z axis when the probe is at the surface
        self.bottomPosition = 0;
        #true if the probe is at the surface, else false
        self.atBottom = False

        
    def initialize(self, portName, timeout = None):
        '''
        Attempt to connect to the specified port and initialize stage
        portName: the port to connect to
        timeout: how long to listen to the port, None for blocking calls
        '''
        try:
            self._openPort(portName,timeout)
        except:
            self.connected = False
            return
        #set the conncetion to true
        self.connected = True
        #renumber to make sure all ids are unique and as expected
        self.renumber()
        #clear replies from renumber
        self.checkReplies(3)
        #home all stages
        self.homeAll()
        #move xyz to 100,000 to engage each stage and get rid of dead zone
        self.moveToPositionXY((100000, 100000))
        self._send(self.zdev, self.COMMANDS['MOVE_ABS'], 100000)
        self._receive()

    def homeAll(self):
        '''
        home all stages and clear replies.
        Homes the z axis first to help protect the probe
        '''
        if not self.connected:
            return
        self.home(3)
        self._receive()
        self.home(2)
        self.home(1)
        self._receive()
        self._receive()
        self.atBottom = False

    def checkReplies(self, numreads):
        '''
        Performs multiple receive calls and checks for rejections
        numreads: the number of reads to perform
        returns true if no errors or rejections occured
        '''
        if not self.connected:
            return
        result = True
        for i in range(numreads):
            (device, command, data) = self._receive()
            if command == 255:
                print('Rejected command')
                result = False

        return result

    def getPositionXY(self):
        '''
        get the current x,y position
        returns (x,y) in stage coordinates
        '''
        if not self.connected:
            return None
        x = self.getPosition(self.xdev)
        y = self.getPosition(self.ydev)
        return (x,y)
    
    def moveToPositionXY(self,  xypos):
        '''
        Move the stage to the specified xy position.  A blocking call.
        Will also retract the probe if it is at the sample surface.
        xypos: (x,y) tuple to move to
        '''
        if not self.connected:
            return
        if self.atBottom:
            self.toggleProbe()
        x,y = xypos
        self._send(self.xdev, self.COMMANDS['MOVE_ABS'], x)
        self._send(self.ydev, self.COMMANDS['MOVE_ABS'], y)
        self._receive()
        self._receive()

    def move(self, direction, stepSize):
        '''
        performs a relative move in the specified direction
        direction: a enumModule.Direction enum
        stepSize: enumModule.StepSize specifying if the step should be large
        '''
        #if not connected, do nothing
        if not self.connected:
            return
        #retract probe if it's at the surface
        if self.atBottom:
            self.toggleProbe()

        #calculate the steps to perform
        step = self.smallStep
        if stepSize == StepSize.large:
            step *= self.largeFactor
        elif stepSize == StepSize.medium:
            step *= self.mediumFactor

        #change device for each direction
        if direction == Direction.left or \
            direction == Direction.right:
            dev = self.xdev
        elif direction == Direction.down or \
            direction == Direction.up:
            dev = self.ydev
        else:
            raise ValueError('Invalid direction')
        #this is inverted relative to the stage, but correct relative to the probe
        #retract for these directions
        if direction == Direction.down or \
            direction == Direction.right:
            step = -1 * step

        #blocking call
        self._send(dev, self.COMMANDS['MOVE_REL'], step)
        self._receive()

    def _collect(self, position):
        '''
        Perform a single collection at the specified position
        position: (x,y) of stage coordinate to sample
        '''
        #do nothing if not connected
        if not self.connected:
            return

        #move the probe into place (is blocking)
        self.moveToPositionXY(position)
        #collect at the current position
        self.collect(finish = False)

    def collect(self, finish = True):
        '''
        Collect at the current position for self.dwellTime
		finish: call self.finishCollection at end of collection
        '''
        #do nothing if not connected
        if not self.connected:
            return
        #if probe is not at the bottom
        if not self.atBottom:
            self.toggleProbe()#lower, otherwise do nothing
        #wait for dwellTime
        time.sleep(self.dwellTime)
        self.toggleProbe()#raise
        if finish == True:
            self.finishCollection(forceHome = False)

    def collectAll(self, positions):
        '''
        Collect from each position specified
        positions: a list of (x,y) coordinates in motor positions
        '''
        #do nothing if not connected
        if not self.connected or self.bottomPosition == 0:
            return
        #start by homing all
        self.homeAll()
        #collected from each position
        for i, p in enumerate(positions):
            print("Collecting from sample {}".format(i+1))
            self._collect(p)
        print("Finished collection")
        self.finishCollection(forceHome = True)

    def finishCollection(self, forceHome):
        #if self.postAcqusitionWait is not 0, have to move to final position
        if self.postAcqusitionWait != 0:
            self.finalPosition()
            if self.postAcqusitionWait != -1:
                time.sleep(self.postAcqusitionWait)
                self.homeAll()
        elif forceHome == True:
            #finish homing all
            self.homeAll()

    def moveProbe(self, direction, stepSize):
        '''
        Move the probe relative to the current position
        direction: a valid connectedInstrument.Direction
        isBigStep: toggle for having a larget step size
        '''
        #do nothing without a connection
        if not self.connected:
            return
        #find step size
        step = self.smallZstep
        if stepSize == StepSize.medium:
            step *= self.mediumFactor
        elif stepSize == StepSize.large:
            step *= self.largeFactor
        elif stepSize == StepSize.giant:
            step *= self.giantFactor
        if direction == Direction.up:
            step = -step
        self._send(self.zdev, self.COMMANDS['MOVE_REL'], step)
        self._receive()
        #regardless of position, the probe is no longer at the bottom
        self.atBottom = False

    def setProbePosition(self):
        '''
        set the probe position as at the surface
        '''
        if not self.connected:
            return
        #store the current position
        self.bottomPosition = self.getPosition(self.zdev)
        #probe is now at the bottom
        self.atBottom = True
        #automatically retract
        self.toggleProbe()

    def getProbePosition(self):
        if not self.connected:
            return None
        return self.getPosition(self.zdev)

    def toggleProbe(self):
        '''
        toggle the current probe position.  If at bottom, raise, else lower
        '''
        if self.bottomPosition == 0 or not self.connected:
            return
        if self.atBottom:
            pos = self.bottomPosition - self.smallZstep * self.largeFactor*5
            pos = 0 if pos < 0 else pos
        else:
            pos = self.bottomPosition

        self._send(self.zdev, self.COMMANDS['MOVE_ABS'], pos)
        self._receive()
        self.atBottom = not self.atBottom
        
    def finalPosition(self):
        '''
        Move the probe to the washing position, which is 10000 above the slide position
        '''
        if self.bottomPosition == 0 or not self.connected:
            return
        self.homeAll()
        pos = self.bottomPosition - 10000#NOTE CONSTANT VALUE
        
        self._send(self.zdev, self.COMMANDS['MOVE_ABS'], pos)
        self._receive()