# -*- coding: utf-8 -*-
"""
Data format conversion from .dat to SEG-Y format.

@author:     Zhengguang Zhao
@copyright:  Copyright 2016-2019, Zhengguang Zhao.
@license:    MIT
@contact:    zg.zhao@outlook.com


"""

import os

from PyQt5.QtCore import  Qt

from PyQt5.QtWidgets import  QApplication, QAbstractSpinBox, QComboBox, QDesktopWidget, QDialogButtonBox, QDockWidget, QFrame,\
                             QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QMainWindow, \
                             QMessageBox, QPushButton, QSizePolicy, QSpinBox, \
                                  QWidget, QProgressBar

from package.thread.segyconverter import SegyConverterThread
from package.utils.utils import transform_separator
from package.pyqtconfig import ConfigManager

import datetime

import resources_rc


class MainWindow(QMainWindow):  
     
   

    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)


        self.inpath = None
        self.outpath = None 

        self.inFlag = False
        self.outFlag = False

        self.thread = None

    

        # last directory opened
        self.lastDir = 'C:/'         

        self.config = ConfigManager()

        args = {'header_size': 512,
            'initial':4,
            'rcv_field': 'Inline3D',
            'dsf': 'int32',
            'dt': 1000}

        self.config.set_defaults(args)
        
        self.initUI()        
        
        

    def initUI(self):      
        
        self.setWindowTitle('DeepListen SEG-Y Converter')      

        # Adjust screen size
        dw = QDesktopWidget()
        scrCount = dw.screenCount()
        if (scrCount > 1):
            self.iWidth = dw.width()/2
        else:
            self.iWidth = dw.width()
        
        self.iHeight = dw.height()




        self.inButton = QPushButton(u'   Input Directory...', parent=self) 
        self.inLineEdit = QLineEdit(parent=self)

        self.outButton = QPushButton(u'Output Directory...', parent=self) 
        self.outLineEdit = QLineEdit(parent=self) 


        self.headerLabel = QLabel('Header Size [Byte]')
        self.headerSpinBox = QSpinBox()
        self.headerSpinBox.setAccelerated(True)
        self.headerSpinBox.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.headerSpinBox.setMinimum(0)
        self.headerSpinBox.setMaximum(1000000000)
        self.headerSpinBox.setSingleStep(1)
        self.headerSpinBox.setValue(512) 

        self.dsfLabel = QLabel('Sample Format')
        self.dsfComboBox = QComboBox()
        self.dsfComboBox.addItems(['int32'])


        self.dtLabel = QLabel('Sampling Rate [us]')
        self.dtSpinBox = QSpinBox()
        self.dtSpinBox.setAccelerated(True)
        self.dtSpinBox.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.dtSpinBox.setMinimum(1)
        self.dtSpinBox.setMaximum(100000000)
        self.dtSpinBox.setSingleStep(1)
        self.dtSpinBox.setValue(1000) 

        self.rcvLabel = QLabel('Receiver Info.')
        self.rcvComboBox = QComboBox()
        self.rcvComboBox.addItems(['Inline3D'])

        self.numLabel = QLabel('Receiver Numbering')
        self.numSpinBox = QSpinBox()
        self.numSpinBox.setAccelerated(True)
        self.numSpinBox.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.numSpinBox.setMinimum(1)
        self.numSpinBox.setMaximum(100000000)
        self.numSpinBox.setSingleStep(1)
        self.numSpinBox.setValue(4) 

    
        

      
        
        # add line
        line1 = QFrame()
        line1.setFrameShape(QFrame().HLine)
        line1.setFrameShadow(QFrame().Sunken)     



        # add line
        line2 = QFrame()
        line2.setFrameShape(QFrame().HLine)
        line2.setFrameShadow(QFrame().Sunken)   




        self.progressLabel = QLabel('Converting progress') # progerssbar label showing which process is running
        self.progressBar = QProgressBar(self)


        # Create ButtonBox for OK and Cancel
        self.buttonBox = QDialogButtonBox(parent=self)
        self.buttonBox.setOrientation(Qt.Horizontal) # horizontal
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok) 
        self.buttonBox.button(QDialogButtonBox.Ok).setText(self.tr("Convert"))
        self.buttonBox.button(QDialogButtonBox.Cancel).setText(self.tr("Cancel"))
        

        
        grid1 = QGridLayout()
        grid1.addWidget(self.inButton,  0, 0, 1, 1, Qt.AlignRight)
        grid1.addWidget(self.inLineEdit, 0, 1, 1, 3)
        grid1.addWidget(self.outButton,  1, 0, 1, 1, Qt.AlignRight)
        grid1.addWidget(self.outLineEdit, 1, 1, 1, 3)


        grid2 = QGridLayout()
        grid2.addWidget(self.headerLabel,  0, 0, 1, 1, Qt.AlignRight)
        grid2.addWidget(self.headerSpinBox, 0, 1, 1, 2)
        grid2.addWidget(self.dsfLabel,  1, 0, 1, 1, Qt.AlignRight)
        grid2.addWidget(self.dsfComboBox , 1, 1, 1, 2)
        grid2.addWidget(self.dtLabel,  2, 0, 1, 1, Qt.AlignRight)
        grid2.addWidget(self.dtSpinBox  , 2, 1, 1, 2)
        grid2.addWidget(self.rcvLabel ,  3, 0, 1, 1, Qt.AlignRight)
        grid2.addWidget(self.rcvComboBox , 3, 1, 1, 2)
        grid2.addWidget(self.numLabel,  4, 0, 1, 1, Qt.AlignRight)
        grid2.addWidget(self.numSpinBox, 4, 1, 1, 2)

        


        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.progressLabel)
        vbox1.addWidget(self.progressBar)
        
        vbox = QVBoxLayout()
        vbox.addLayout(grid1)
        vbox.addWidget(line1)
        vbox.addLayout(grid2)
        vbox.addWidget(line2)
        vbox.addLayout(vbox1)
        vbox.addWidget(self.buttonBox)


        




        self.main = QWidget()
        self.setCentralWidget(self.main)
        self.main.setLayout(vbox)  


        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()

        self.resize(800, 500)   

        # Connect all necessary signals and slots.
        self._connect_signals_and_slots()
        self._add_handlers_for_config()
         


    def _connect_signals_and_slots(self):

        self.inButton.clicked.connect(self.onInput)
        self.outButton.clicked.connect(self.onOutput)

        
        self.buttonBox.accepted.connect(self.convert) # OK
        self.buttonBox.rejected.connect(self.cancelConversion) # Cancel

    def _add_handlers_for_config(self):

        self.config.add_handler('header_size', self.headerSpinBox)
        self.config.add_handler('initial', self.numSpinBox)
        self.config.add_handler('rcv_field', self.rcvComboBox)
        self.config.add_handler('dsf', self.dsfComboBox)
        self.config.add_handler('dt', self.dtSpinBox)
        
    def createActions(self):
        pass


    def createMenus(self):

        pass

    def createToolBars(self):
        pass
        
    def createStatusBar(self):
        pass


    


    def onInput(self):

        folderPath = QFileDialog.getExistingDirectory(self,"Select Directory Containing .DAT Files", self.lastDir)
        
        if folderPath:
            self.inLineEdit.setText(folderPath)
            self.inpath = transform_separator(folderPath)
            self.lastDir = self.inpath

            self.inFlag = True



    def onOutput(self):

        folderPath = QFileDialog.getExistingDirectory(self,"Select Directory to Save SEG-Y Files", self.lastDir)
        
        if folderPath:
            self.outLineEdit.setText(folderPath)
            self.outpath = transform_separator(folderPath)
            self.lastDir = self.outpath

            self.outFlag = True


    def closeEvent(self, event):
        
        """
        redefined closeEvent method
        :param event: close() triggered event
        :return: None
        """

        if self.thread != None:
    
            self.thread.stop()

        event.accept()
        
    def setProgressLabel(self, text):
    
        self.progressLabel.setText(text)
    
    def updateLabel(self, str):

        self.setProgressLabel(str)

    def updateProgress(self, i, imax):   

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(imax)
        self.progressBar.setValue(i)        
              

    def finishProgress(self, completion, str):   
        #self.completion = self.getCompletionStatus(completion)
        self.setProgressLabel(str)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)


    def cancelConversion(self):
        
        reply = QMessageBox.critical(self,"Abortion Request", "Are you sure to abort this conversion process?",  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:

            if self.thread != None:

                if self.thread.isRunning():
                    self.thread.stop()
                    
                    self.setAbortStatus()
        else:

            return          
            
    def setAbortStatus(self):

        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        self.setProgressLabel ("Conversion stopped. Click 'Convert' to restart the conversion process.")

    
    def killThread(self):
        
        self.thread.stop() # terminate thread


    def showError(self, msg):
        
        self.killThread()
        
        QMessageBox.critical(self,"Error", msg,
                    QMessageBox.Ok)
        
    def convert(self):

        if self.inFlag and self.outFlag:

            args = self.config.as_dict()


            self.thread = SegyConverterThread(self.inpath, self.outpath, args)
                        
            
            
            self.thread.labelSignal_.connect(self.updateLabel)        
            self.thread.progressSignal_.connect(self.updateProgress)
            self.thread.finishSignal_.connect(self.finishProgress)
            self.thread.sendError_.connect(self.showError)
            self.thread.start()
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    


    def datParser(self, root):

    
        file_list_z = []
        map_dict_z = {} # key = folder name; value = full folder path
        
        time_list = []
        rcv_list = []
        size_list = []

        file_list_x = []
        map_dict_x = {}

        file_list_y = []
        map_dict_y = {}

        for root, dirs, files in os.walk(root):            

            for file_name in files:     

                suffix =  os.path.splitext(file_name)[1]     

                if suffix == '.dat' and 'ch01' in file_name:    

                    ss = file_name.split('_')  
                    rname = float(ss[0])
                    rcv_list.append(rname)
                    dates = ss[2]                    
                    times = ss[3]

                    time_list.append(datetime.datetime(int(dates[0:4]), int(dates[4:6]), int(dates[6:8]),
                                                    int(times[0:2]), int(times[2:4]), int(times[4:6])))

                    file_list_z.append(file_name)

                    file = transform_separator(os.path.join(root, file_name))

                    size = os.path.getsize(file)
                    size_list.append(size)

                    map_dict_z[file_name] = file 

                elif suffix == '.dat' and 'ch02' in file_name:      

                    file_list_x.append(file_name)

                    file = transform_separator(os.path.join(root, file_name))

                    map_dict_x[file_name] = file 

                elif suffix == '.dat' and 'ch03' in file_name:      

                    file_list_y.append(file_name)

                    file = transform_separator(os.path.join(root, file_name))

                    map_dict_y[file_name] = file 

        

        return file_list_z, file_list_x, file_list_y, map_dict_z, map_dict_x, map_dict_y, rcv_list, time_list, size_list   

         

  
