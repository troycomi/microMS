from enum import Enum, unique

@unique      
class Direction(Enum):
    '''
    Enum class to encode directions for slide stepping
    '''
    left = 1
    right = 2
    up = 3
    down = 4

@unique      
class StepSize(Enum):
    '''
    Enum class to encode directions for slide stepping
    '''
    small = 1
    medium = 2
    large = 3
    giant = 4