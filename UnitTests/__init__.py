'''
nosetests --with-coverage --cover-erase --cover-inclusive --cover-package=ImageUtilities,CoordinateMappers,GUICanvases --cover-html
nosetests --with-coverage --cover-inclusive --cover-package=ImageUtilities,CoordinateMappers,GUICanvases --cover-html

Collection of unit tests for all packages.  Each package has its own test file.
Each module in the package has its own test class, and most functions in the module
have a single test function.

constants.py:               Set of filenames for different types of images and files
test_CoordinateMappers.py:  Test coordinate mappers and stage movement
test_GUICanvases.py:        Test GUI function and underlying models
test_ImageUtilities.py:     Test image support functions and utilities
'''