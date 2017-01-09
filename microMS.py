#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import ctypes
from PyQt5 import QtGui, QtCore, QtWidgets

from GUICanvases.microMSQTWindow import MicroMSQTWindow

def main(): 
    '''
    main method that begins execution of the QApplication
    '''
    qApp = QtWidgets.QApplication(sys.argv) 

    #set up icon
    if sys.platform == 'win32':
        myappid = 'uiuc.sweedlerlab.microms.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    qApp.setWindowIcon(QtGui.QIcon(r'GUICanvases/Icon/icon_sm.png'))
    
    #start application
    aw = MicroMSQTWindow()
    aw.setWindowTitle("MicroMS")
    aw.show()
    sys.exit(qApp.exec_())
    
if __name__ == '__main__':
    main()