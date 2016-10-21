
####colors and sizes of GUI components in slideCanvas
#default and boarder color of the slide image
IMAGE_BACKGROUND        =   'black'
#color of temporary or test cell find
TEMP_CELL_FIND          =   'turquoise'
#predicted locations from the current mapper
PREDICTED_POINTS        =   'yellow'
#color of circle and text of highest FLE 
FIDUCIAL_WORST          =   'red'
#color fo the rest of the fiducial circles and text
FIDUCIAL                =   'blue'
#background label of fiducial marks
FIDUCIAL_LABEL_BKGRD    =   'white'
#ROI boundary 
ROI                     =   'yellow'
#colors of blob list
MULTI_BLOB              =   ['lime', 'salmon', 'skyBlue', 'orangeRed', 
                             'plum', 'hotPink', 'aqua', 'yellow', 'olive']
#text display of grouped targets from expanding blobs
EXPANDED_TEXT          =   'purple'
#default blob radius in pixels
DEFAULT_RADIUS          =   8
#default fiducial radius in pixels
FIDUCIAL_RADIUS         =   100
#maximum number of blobs to draw when limit is selected
DRAW_LIMIT              =   250
#maximum number of blobs to check prior to deselecting TSP optimization
TSP_LIMIT               =   1000


###colors of GUI components in histCanvas
#colors of  bars in histogram for red, green, blue, size, circularity, and distance
BAR_COLORS              =   ['red', 'green', 'blue', 'gray', 'gray', 'gray']
#color of bars and blobs with values less than the cutoff
LOW_BAR                 =   'cyan'
#color of bars and blobs with values greater than the cutoff
HIGH_BAR                =   'hotpink'
#color of bars and blobs with values in a single bar
SINGLE_BAR              =   'darkorange'
#color of line to indicate a single cell position
SINGLE_CELL             =   'red'

###constants for blob shapes
DEFAULT_BLOB_RADIUS     =   DEFAULT_RADIUS
DEFAULT_PATTERN_RADIUS  =   DEFAULT_RADIUS

###standard test files for the debug load
#directory to check for prior to trying to load
DEBUG_DIR               =   r'T:\Cerebellum One Left Stitched _'
#image file
DEBUG_IMG_FILE          =   r'T:\Cerebellum One Left Stitched _\Cerebellum One Left Stitched __c1.tif'
#cell find file
DEBUG_CELL_FIND         =   r'T:\Cerebellum One Left Stitched _\sol_find.txt'
#registration file
DEBUG_REG_FILE          =   r'T:\Cerebellum One Left Stitched _\sol.msreg'