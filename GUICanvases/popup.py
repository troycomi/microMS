
"""
a collection of small, custom popup windows used by microMSQT
"""

from PyQt4 import QtGui

class blbPopupWindow(QtGui.QDialog):
    '''
    Window for setting blob finding parameters
    '''
    def __init__(self, blbFinder, parent=None):
        '''
        setup GUI and populate with current values
        blobFinder: the blob finding object
        parent: the parent, calling widget, a MicroMSQTWindow
        '''
        super(blbPopupWindow,self).__init__()

        self.master = parent        
        
        self.setWindowTitle("Blob Find Entry")        
        
        #user input widgets
        self.blobFinder = blbFinder
        self.minText = QtGui.QLineEdit(self)
        self.minText.setText( str(blbFinder.minSize))
        self.maxText = QtGui.QLineEdit(self)
        self.maxText.setText('' if blbFinder.maxSize is None else str(blbFinder.maxSize))
        self.minCirText = QtGui.QLineEdit(self)
        self.minCirText.setText( str(blbFinder.minCircularity))
        self.maxCirText = QtGui.QLineEdit(self)
        self.maxCirText.setText('' if blbFinder.maxCircularity is None 
                                else str(blbFinder.maxCircularity))
        self.intens = QtGui.QLineEdit(self)
        self.intens.setText(str(blbFinder.threshold))
        self.imgInd = QtGui.QLineEdit(self)
        self.imgInd.setText(str(blbFinder.imageIndex+1))
        self.channel = QtGui.QComboBox(self)
        self.channel.addItem("Red")
        self.channel.addItem("Green")
        self.channel.addItem("Blue")
        self.channel.setCurrentIndex(blbFinder.colorChannel)

        #add to vbox layout with labels
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(QtGui.QLabel("Minimum Size",self))
        vbox.addWidget(self.minText)
        vbox.addWidget(QtGui.QLabel("Maximum Size",self)) 
        vbox.addWidget(self.maxText)
        vbox.addWidget(QtGui.QLabel("Minimum Circularity",self))
        vbox.addWidget(self.minCirText)
        vbox.addWidget(QtGui.QLabel("Maximum Circularity",self)) 
        vbox.addWidget(self.maxCirText)
        vbox.addWidget(QtGui.QLabel("Threshold",self)) 
        vbox.addWidget(self.intens)
        vbox.addWidget(QtGui.QLabel("Image Channel",self)) 
        vbox.addWidget(self.imgInd)
        vbox.addWidget(QtGui.QLabel("Color",self)) 
        vbox.addWidget(self.channel)
        self.setButton = QtGui.QPushButton("Set Parameters",self)
        self.setButton.clicked.connect(self.setParams)
        vbox.addWidget(self.setButton)
        
        self.setLayout(vbox)
        
    def setParams(self):
        '''
        sets the parameters for blob finding based on the current GUI values
        Calls on the slideCanvas to perform blob finding on the current image
        '''
        try:
            self.blobFinder.minSize = int(self.minText.text())
        except:
            self.minText.setText(str(self.blobFinder.minSize))

        try:    
            self.blobFinder.maxSize = None if self.maxText.text() is '' else int(self.maxText.text())
        except:
            self.maxText.setText('' if self.blobFinder.maxSize is None else str(self.blobFinder.maxSize))

        try:
            self.blobFinder.minCircularity = float(self.minCirText.text())
        except:
            self.minCirText.setText( str(self.blobFinder.minCircularity))

        try:
            self.blobFinder.maxCircularity = None if self.maxCirText.text() is '' else float(self.maxCirText.text())
        except:
            self.maxCirText.setText('' if self.blobFinder.maxCircularity is None 
                                else str(self.blobFinder.maxCircularity))

        try:
            self.blobFinder.threshold = int(self.intens.text())
        except:
            self.intens.setText(str(self.blobFinder.threshold))

        try:
            self.blobFinder.imageIndex = int(self.imgInd.text())-1
        except:
            self.imgInd.setText(str(self.blobFinder.imageIndex+1))

        self.blobFinder.colorChannel = int(self.channel.currentIndex())
        #blob find
        if self.master is not None:
            self.master.model.testBlobFind()
            self.master.slideCanvas.draw()

class gridPopupWindow(QtGui.QDialog):
    '''
    displays a table with the current intermediate map of the mapper for the user to edit
    '''
    def __init__(self, model):
        '''
        populate the GUI with previous points
        previousPoints: list of triples of the set coordinate and its x and y physical position
        parent: the microMSQT window calling the popup
        '''
        super(gridPopupWindow,self).__init__()

        self.model = model
        previousPoints = model.coordinateMapper.getIntermediateMap()
        
        self.setWindowTitle("Stage Locations")

        vbox = QtGui.QVBoxLayout()
        self.table = QtGui.QTableWidget(self)
        
        self.table.setRowCount(len(previousPoints))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Coord","X","Y"])
        self.table.update()
        vbox.addWidget(self.table)
        for i,m in enumerate(previousPoints):
            for j,el in enumerate(m):
                self.table.setItem(i,j,QtGui.QTableWidgetItem(str(el)))
        self.setLayout(vbox)

    def closeEvent(self,evnt):
        '''
        parse the information in the table and return it to the current mapper
        '''
        result = []
        for i in range(self.table.rowCount()):
            coord = self.table.item(i,0).text()
            x = self.table.item(i,1).text()
            y = self.table.item(i,2).text()
            result.append((coord, x, y))

        self.model.coordinateMapper.setIntermediateMap(result)
        #close
        super(gridPopupWindow, self).closeEvent(evnt)

class histPopupWindow(QtGui.QDialog):
    '''
    a popup window to adjust histogram options such as display image and metric
    '''
    def __init__(self, histCanvas, parent=None):
        '''
        setup GUI and initialize it with the current settings
        histCanvas: a histCanvas widget contained within parent
        parent: a microMSQT window
        '''
        super(histPopupWindow,self).__init__()

        self.master = parent        
        self.hist = histCanvas
        
        self.setWindowTitle("Histogram Options")        
        
        #generate user io widgets
        self.imgInd = QtGui.QLineEdit(self)
        self.imgInd.setText(str(self.hist.imgInd+1))
        self.channel = QtGui.QComboBox(self)
        for m in self.hist.metrics:
            self.channel.addItem(m)

        self.channel.setCurrentIndex(self.hist.populationMetric)
        self.offset = QtGui.QLineEdit(self)
        self.offset.setText(str(self.hist.offset))
        self.max = QtGui.QRadioButton(self)
        self.max.setText('Max Intensity')
        self.mean = QtGui.QRadioButton(self)
        self.mean.setText('Average Intensity')
        self.mean.setChecked(not self.hist.reduceMax)
        self.max.setChecked(self.hist.reduceMax)

        #add to vbox layout with labels
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(QtGui.QLabel("Image Channel",self)) 
        vbox.addWidget(self.imgInd)
        vbox.addWidget(QtGui.QLabel("Color or Morphology",self)) 
        vbox.addWidget(self.channel)
        vbox.addWidget(QtGui.QLabel("Offset (pixels)",self)) 
        vbox.addWidget(self.offset)
        vbox.addWidget(self.max)
        vbox.addWidget(self.mean)

        btn = QtGui.QPushButton("Set Parameters",self)
        btn.clicked.connect(self.setParams)
        vbox.addWidget(btn)
        
        self.setLayout(vbox)
        
    def setParams(self):
        '''
        trigger to set the new histogram parameters and redraw the histogram
        '''
        try:
            self.hist.imgInd = int(self.imgInd.text())-1
        except:
            self.imgInd.setText(str(self.hist.imgInd+1))
            
        try:
            self.hist.offset = int(self.offset.text())
        except: 
            self.offset.setText(str(self.hist.offset))

        self.hist.populationMetric = int(self.channel.currentIndex())
        self.hist.reduceMax = self.max.isChecked()
        self.hist.calculateHist()