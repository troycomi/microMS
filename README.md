# microMS
GUI for performing automatic cell finding and point based registration

microMS is written in python 3.4.  In addition to base components, the packages matplotlib, PyQt4, numpy, scipy, openslide, skimage, pyserial are required.  The main class is composed of widgets in the GUICanvas package for displaying a microscope image and population level statistics as a histogram.  Each widget interacts with microMSModel object, representing a microscopy experiment and mass spectrometer system and interacting data.  

A slideWrapper provides an object for interacting with a set of microscopy images representing brightfield and different fluorescence channel images.  The current field of view is maintained to simplify controller interaction with the image. The ImageUtilities package also contains modules for cell finding, patterning target positions, and optimizing travel paths.

The coordinateMapper is an abstract base class providing an interface to the GUI software. At a minimum, the mapper aligns pixel positions with physical coordinates and provides a means to translate target positions on an image to instrument-specific directions. Currently, four concrete implementations are included to demonstrate the versitility of the software. Coordinate systems for a Bruker UltrafleXtreme, a Bruker SolariX, an AB Sciex oMALDI sample stage and a lab-built 3-axis liquid microjunction probe are contained in the CoordianteMappers package.
