
####colors and sizes of GUI components in slideCanvas
#default and boarder color of the slide image
IMAGE_BACKGROUND        =   'black'
#color of temporary or test blob find
TEMP_BLOB_FIND          =   'turquoise'
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
#ROI minimum distance 
ROI_DIST                =   10 #pixels
#colors of blob list
MULTI_BLOB              =   ['lime', 'salmon', 'skyBlue', 'orangeRed', 
                             'plum', 'hotPink', 'aqua', 'yellow', 'olive',
                             'green']
#text display of grouped targets from expanding blobs
EXPANDED_TEXT          =   'purple'
#default blob radius in pixels
DEFAULT_RADIUS          =   8#363
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
#color of line to indicate a single blob position
SINGLE_BLOB             =   'red'

###constants for blob shapes
DEFAULT_BLOB_RADIUS     =   DEFAULT_RADIUS
DEFAULT_PATTERN_RADIUS  =   DEFAULT_RADIUS

###standard test files for the debug load
#directory to check for prior to trying to load
DEBUG_DIR               =   r'T:\Cerebellum One Left Stitched _'
#image file
DEBUG_IMG_FILE          =   r'T:\Cerebellum One Left Stitched _\Cerebellum One Left Stitched __c1.tif'
#blob find file
DEBUG_BLOB_FIND         =   r'T:\Cerebellum One Left Stitched _\sol_find.txt'
#registration file
DEBUG_REG_FILE          =   r'T:\Cerebellum One Left Stitched _\sol.msreg'

###help message text
IMAGE_HOTKEYS           =   ("w,s,a,d\t\tMove\n"
        "W,S,A,D\tMove Farther\n"
        "q,e\t\tZoom out/in\n"
        "r\t\tReset view\n"
        "t\t\tSwitch views\n"
        "b\t\tTest blob find\n"
        "B\t\tSwitch to threshold view\n"
        "m\t\tMirror x axis\n"
        "p\t\tToggle predicted location\n"
        "o\t\tToggle drawn shapes\n"
        "O\t\tToggle drawing all blob lists\n"
        "Ctrl + C\tClear all found blobs\n"
        "C\t\tClear current blob list\n"
        "c\t\tClear ROI\n\n"
        "#\t\tToggle channel\n"
        "Ctrl+#\t\tSet channel\n"
        "Alt+#\t\tSet manual blob list\n\n"
        "LMB\t\tMove to center\n"
        "LMB+Shift\tAdd/remove points\n"
        "LMB+Ctrl\tDraw ROI\n"
        "MMB\t\tGet pixel values\n"
        "RMB\t\tAdd slide coordinate\n"
        "RMB+Shift\tRemove slide coordinate\n"
        "Scroll\t\tZoom in/out"
        )

INSTRUMENT_HOTKEYS      =   ("i,k,j,l\t\tMove\n"
        "Ctrl + I,K,J,L\tMove Far\n"
        "I,K,J,L\t\tMove Farther\n"
        "+,-\t\tMove probe up/down\n"
        "V\t\tSet probe position\n"
        "v\t\tToggle probe position\n"
        "h\t\tHome stage\n"
        "H\t\tFinal position\n"
        "x\t\tSingle analysis\n\n"
        "LMB+Alt\tMove to spot\n"
        "RMB\t\tAdd coordinate\n"
        "RMB+Shift\tRemove coordinate\n"
        )

HISTOGRAM_HOTKEYS       =   ("LMB\t\tSet lower threshold\n"
        "LMB+Shift\tSet lower cutoff\n"
        "MMB\t\tSet single bar\n"
        "RMB\t\tSet upper threshold\n"
        "RMB+Shift\tSet upper cutoff\n"
        "Scroll\t\tZoom in/out")

