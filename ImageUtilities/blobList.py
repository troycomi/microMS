import numpy as np
import scipy
from scipy.spatial.distance import pdist
from GUICanvases import GUIConstants
from ImageUtilities import blob

class blobList(object):
    """
    A collection of blob objects.
    Underlying data is the list self.blobs and supplies several
    utilities for filtering, drawing and expanding blobs.
    """

    def __init__(self):
        self.blobs = []

    #add in blob utilities
    #add in patches and text draw
    #add in xy list (iff needed)
    #need to generalize enough to support hist blobs

    #have to rewrite a lot of tests to replace lists of blobs with this!
