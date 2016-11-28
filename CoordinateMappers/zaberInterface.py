import serial, struct, abc
 
class ZaberInterface(object, metaclass=abc.ABCMeta):
    '''
    An abstract base class for interacting with zaber linear stages
    Encodes methods for basic IO with a stage
    '''
    def __init__(self):
        #the serial object to talk to
        self.stage = None
        
        #standard commands, more at
        #http://www.zaber.com/wiki/Manuals/Binary_Protocol_Manual#Quick_Command_Reference
        self.COMMANDS = {
            'HOME'      :   1,
            'RENUMBER'  :   2,
            'MOVE_ABS'  :   20,
            'MOVE_REL'  :   21,
            'CUR_POS'   :   60
            }
        super().__init__()

    '''
    home and renumber don't recieve
    as they don't know the number of connected devices
    '''
    def home(self, device = 0):
        '''
        home the specified device or all
        device: the device to home
        '''
        self._send(device, self.COMMANDS['HOME'])

    def renumber(self):
        '''
        renumber all devices
        '''
        self._send(0, self.COMMANDS['RENUMBER'])

    def getPosition(self, device):
        '''
        provides the current location of the reqested device
        device: the device to query
        '''
        self._send(device, self.COMMANDS['CUR_POS'])
        (deviceOut, command, data) = self._receive()
        #some times the recieves can get misaligned, hopefully this catches it!
        if device == deviceOut:
            return data
        else:
            return -1
        
    def _openPort(self, portName, timeout=None):
        '''
        begin communication with a serial stage
        portName: the name of the port to communicate with
        timeout: the time to wait for a reply.  Set to None for blocking calls
        '''
        try:
            self.stage = serial.Serial(portName, 9600, 8, 'N', 1, timeout=timeout) 
        except Exception as ext:
            print(ext)
            print("Error initializing {}!".format(portName))
            raise ValueError("stage not initialized!")

    def _send(self, device, command, data=0):
        '''
        send a packet using the specified device number, command number, and data
        The data argument is optional and defaults to zero
        device: the id of the connected device
        command: a command, using the dictionary in init
        data: the optional data to send as well
        '''
        if self.stage == None:
            raise ValueError("stage not initialized!")
        data = int(data)
        packet = struct.pack('<BBl', device, command, data)
        self.stage.write(packet)
 
    def _receive(self):
        '''
        reads the serial port
        there must be 6 bytes to receive (no error checking)
        returns the (device, command, data)
        '''
        if self.stage == None:
            raise ValueError("stage not initialized!")
        r = [0,0,0,0,0,0]
        for i in range (6):
            r[i] = ord(self.stage.read(1))

        data =  (256.0**3.0*r[5]) + (256.0**2.0*r[4]) + (256.0*r[3]) + (r[2])
        if r[5] > 127:
            data -= 256.0**4

        device = r[0]
        command = r[1]

        return (device, command, data)

    def findPorts(self):
        '''
        Querry each COM port for a possible connection.
        Will work for windows only
        '''
        result = []
        for i in range(256):
            try:
                name = 'COM{}'.format(i)
                s = serial.Serial(name)
                result.append(name)
                s.close()
            except serial.SerialException:
                pass
        return result