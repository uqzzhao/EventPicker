# -*- coding: utf-8 -*-

"""

Mainwindow of EventPicker 

@author:     Zhengguang Zhao
@copyright:  Copyright 2016-2019, Zhengguang Zhao.
@license:    LGPL v2.1
@contact:    zg.zhao@outlook.com


"""

import sys

sys.path.append(".") 
import time

import os
import numpy as np

import csv
import copy
import pandas as pd

from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)

from matplotlib.figure import Figure

from PyQt5 import QtCore
from PyQt5.QtCore import  Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit, \
QMainWindow, QMessageBox, QPushButton, QRadioButton, QSizePolicy, QScrollArea, QSpacerItem, QSpinBox, QTabWidget, QToolBar, QToolButton, QVBoxLayout, QWidget


from package.psmodule import pssegy
from package.utils import signorm
from collections import defaultdict
from matplotlib import pyplot as plt

import resources_rc

DEFAULT_NUMERIC_VALUE = -999.25

class EventPicker(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('EventPicker 2018.1')


        self.nSubPlots = None # number of traces/subplots
        self.nSamples = None # number of samples per trace
        self.dragFrom = None
        self.segy = None # type: Segy class 

        
        # # {'0': {'2500': {'p':[marker1, marker2]}
        # 				 {'s':[maerker1, marker2]}}
        # 
        self.markers = defaultdict(dict)
        self.eventList = []
        self.markerList = []

        self.currentEvent = defaultdict(dict)
        self.event2file = defaultdict(dict)
        self.currentEventId = int(1)
        self.spanMarker = None
        self.modeFlag = 'a'
        self.componentFlag = int(12)
        self.normFlag = int(1) # traces data normalized before display

        self.zTraces = None
        self.xTraces = None
        self.yTraces = None
                      
        self.xcolor = 'b'
        self.ycolor = 'r'
        self.zcolor = 'green'


        self.fileList = []
        self.currentFile = None
        self.inpath = None
        self.outpath = "F:\\datafolder\\eventspicked"


        self.zLines = [] # list container of line curves of Z traces
        self.xLines = []
        self.yLines = []

        self.autoPickerParams = {            
            'stalta_algorithm': 'Recursive',            
            'nsta': '20',
            'nlta': '50',
            'pthreshold': '2.0',
            'sthreshold': '2.2'
        }


        
        self.initUI()  
    
    def initUI(self):
       
        # Trace plot
        self.fig = plt.figure()
        
        self.staticCanvas = FigureCanvas(self.fig)        
        self.staticCanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
               
       
        

       
        self.fig.canvas.mpl_connect('button_press_event', self.onClick)
        self.fig.canvas.mpl_connect('button_release_event', self.onRelease)		
        #self.fig.canvas.mpl_connect('scroll_event', self.onScroll)
        self.fig.canvas.mpl_connect('key_press_event', self.onKey)


        self.p_line_style = dict(color='r', linestyle='-', linewidth=2)        
        self.p_marker_style = dict(marker='o', s=40, facecolors='none', edgecolors='r')
        self.s_line_style = dict(color='b', linestyle='-', linewidth=2)
        self.s_marker_style = dict(marker='o', s=40, facecolors='none', edgecolors='b')


        # Reference trace plot
        self.refFig = plt.figure()
        
        self.refCanvas = FigureCanvas(self.refFig)

        self.refFig.set_size_inches(self.size().width()/self.refFig.get_dpi(),
                self.size().height() * 0.25 /self.refFig.get_dpi())

        self.refCanvas.setSizePolicy(QSizePolicy.Expanding,
                                   QSizePolicy.Fixed)

        self.refCanvas.updateGeometry()

        
        

        self.graphArea = QScrollArea(self)   
        self.graphArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.graphArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)     
        self.graphArea.setWidget(self.staticCanvas)
        self.graphArea.setWidgetResizable(True)

        
        layout = QVBoxLayout() 
         
        layout.addWidget(self.graphArea)
        #layout.addWidget(self.staticCanvas)
        layout.addWidget(self.refCanvas)

        self.main = QWidget()
        self.setCentralWidget(self.main)
        self.main.setLayout(layout)
        

        self.createActions()
        self.createMenus()
        self.createToolBars()


        self.resize(1176, 776)
       



    def createActions(self):

        self.pickSettingAction = QAction(QIcon(':/icons/windows/settings-48.png'), "&AutoPicker Settings",
                self, shortcut= '',
                statusTip="AutoPicker settings", triggered=self.onPickSettingsClicked)
        self.pickSettingAction.setEnabled(False)
        
        self.selectFolderAction = QAction(QIcon(':/icons/windows/add-folder-48.png'), "&Select SEG-Y Folder",
                self, shortcut= '',
                statusTip="Select SEG-Y files folder", triggered=self.onSelectFolder)

        self.exportAction = QAction(QIcon(':/icons/windows/export-one-48.png'), "&Export Current Event",
                self, shortcut= '',
                statusTip="Export current picked event", triggered=self.onExport)
        
        self.exportAllAction = QAction(QIcon(':/icons/windows/export-all-48.png'), "&Export All Events",
                self, shortcut= '',
                statusTip="Export all picked events", triggered=self.onExportAll)

        self.editEventsAction = QAction(QIcon(':/icons/windows/edit-event-48.png'), "&Edit Events",
                self, shortcut= '',
                statusTip="Edit all picked events", triggered=self.onEditEvents)

        
        
        
        
    def createMenus(self):
        
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.selectFolderAction)

        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.editEventsAction)

        self.exportMenu = self.menuBar().addMenu("&Export")
        self.exportMenu.addAction(self.exportAction)
        self.exportMenu.addAction(self.exportAllAction)
        

    def createToolBars(self):

        # Component Toolbar
        self.componentToolBar = QToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.componentToolBar)


        self.zComponentToolButton = QToolButton(self)
        self.zComponentToolButton.setToolTip('Z Component')
        self.zComponentToolButton.setIcon(QIcon(':/icons/windows/z-checked-48.png'))
        self.zComponentToolButton.setCheckable(True)
        self.zComponentToolButton.setChecked(True)
        self.zComponentToolButton.toggled.connect(self.update) 

        self.xComponentToolButton = QToolButton(self)
        self.xComponentToolButton.setToolTip('X Component')
        self.xComponentToolButton.setIcon(QIcon(':/icons/windows/n-48.png'))
        self.xComponentToolButton.setCheckable(True)
        self.xComponentToolButton.toggled.connect(self.update) 

        self.yComponentToolButton = QToolButton(self)
        self.yComponentToolButton.setToolTip('Y Component')
        self.yComponentToolButton.setIcon(QIcon(':/icons/windows/e-48.png'))
        self.yComponentToolButton.setCheckable(True)
        self.yComponentToolButton.toggled.connect(self.update) 

        
        
        self.componentToolBar.addWidget(self.yComponentToolButton)
        self.componentToolBar.addWidget(self.xComponentToolButton)
        self.componentToolBar.addWidget(self.zComponentToolButton)

        # Auto Pick Toolbar
        self.autoPickToolBar = QToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.autoPickToolBar)

        self.autoPickToolButton = QToolButton(self)
        self.autoPickToolButton.setToolTip('Run AutoPicker')
        self.autoPickToolButton.setIcon(QIcon(':/icons/windows/autopick-purple-48.png'))
        self.autoPickToolButton.clicked.connect(self.onAutoPickClicked)
        self.autoPickToolButton.setEnabled(False)
        
        self.autoPickToolBar.addAction(self.pickSettingAction)        
        self.autoPickToolBar.addWidget(self.autoPickToolButton)

        # Manual Pick Toolbar
        self.manualPickToolBar = QToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.manualPickToolBar)

        self.pickPwaveToolButton = QToolButton(self)
        self.pickPwaveToolButton.setToolTip('Pick P-phase Arrival')
        self.pickPwaveToolButton.setIcon(QIcon(':/icons/windows/pickp-48.png'))
        self.pickPwaveToolButton.setCheckable(True)
        self.pickPwaveToolButton.toggled.connect(self.onPickPwaveToggled)

        self.pickSwaveToolButton = QToolButton(self)
        self.pickSwaveToolButton.setToolTip('Pick S-phase Arrival')
        self.pickSwaveToolButton.setIcon(QIcon(':/icons/windows/picks-48.png'))
        self.pickSwaveToolButton.setCheckable(True)
        self.pickSwaveToolButton.toggled.connect(self.onPickSwaveToggled)

        self.manualPickToolBar.addWidget(self.pickPwaveToolButton)
        self.manualPickToolBar.addWidget(self.pickSwaveToolButton)

        
        # Event Toolbar
        self.eventToolBar = QToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.eventToolBar)
        

        self.clearPickToolButton = QToolButton(self)
        self.clearPickToolButton.setToolTip('Clear Current Picks')
        self.clearPickToolButton.setIcon(QIcon(':/icons/windows/clear-picks-48.png'))
        self.clearPickToolButton.clicked.connect(self.onClearPick) 

        self.clearAllPickToolButton = QToolButton(self)
        self.clearAllPickToolButton.setToolTip('Clear All Picks')
        self.clearAllPickToolButton.setIcon(QIcon(':/icons/windows/clear-all-picks-48.png'))
        self.clearAllPickToolButton.clicked.connect(self.onClearAllPick) 
        self.eventIdWidget = EventIDWidget(self) 

        
        self.eventToolBar.addWidget(self.clearPickToolButton)
        self.eventToolBar.addWidget(self.clearAllPickToolButton)
        self.eventToolBar.addWidget(self.eventIdWidget)
        self.eventToolBar.addAction(self.editEventsAction)
        self.eventToolBar.addAction(self.exportAction)
        self.eventToolBar.addAction(self.exportAllAction)
        
        



        # Matplotlib Navigation ToolBar
        self.pltToolBar = NavigationToolbar(self.staticCanvas, self)
        self.addToolBar(self.pltToolBar)

        self.addToolBarBreak()
        # Manual Pick Toolbar
        self.fileToolBar = FileToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.fileToolBar)
        
        
    def onExportAll(self):

        self.updateCurrentEvent2File()
        
        fileName, ok = QFileDialog.getSaveFileName(self,
                                    "Export",
                                    "C:\\",
                                    "All Files (*);;CSV Files (*.csv)")

        if fileName:
            markers = self.markers

            dics = []

            dic = {'event_id':None,
                'file_name': None,
                'receiver_id': None,
                'p_pos': None, 
                's_pos':None}
            

            if len(markers):
                for event_id, item in self.markers.items():                
                    for plot_id, markers in item.items():
                        dic['event_id'] = int(event_id)
                        dic['file_name'] = self.event2file[event_id]
                        dic['receiver_id'] = int(plot_id) + 1
                        if markers['p'] != None:
                            dic['p_pos'] =  markers['p']['pos']
                        else:
                            dic['p_pos'] =  DEFAULT_NUMERIC_VALUE
                        if markers['s'] != None:
                            dic['s_pos'] =  markers['s']['pos']
                        else:
                            dic['s_pos'] =  DEFAULT_NUMERIC_VALUE

                        
                        dics.append(copy.deepcopy(dic))
                        

                
                
                df = pd.DataFrame(dics)
                df.to_csv(fileName)
                
                QMessageBox.information(self,
                                            "Information",  
                                            "All Events have been saved successfully!",  
                                            QMessageBox.Ok) 
            else:
                QMessageBox.warning(self,
                                            "Warning",  
                                            "No P-wave or S-wave arrival time has been picked!\nPlease pick at least one arrival time for exporting.",  
                                            QMessageBox.Ok)

    def onSelectFolder (self):
        
        folderPath = QFileDialog.getExistingDirectory(self,"Select SEG-Y folder","C:\\")
        if folderPath:            
            self.inpath = folderPath
            self.fileList = self.getAllFiles(folderPath)
            self.updateAll(self.fileList[0])
            self.fileToolBar.initWidget(self.fileList)
        
    def getAllFiles(self, path_dir):        
        if os.path.exists(path_dir) and os.path.isdir(path_dir):
            path_dir = os.path.abspath(path_dir)
            for i in os.listdir(path_dir):
                path_i = os.path.join(path_dir, i)
                if os.path.isfile(path_i) and os.path.splitext(os.path.basename(path_i))[1] == '.sgy':
                    self.fileList.append(path_i)
                    #print(path_i)
                else:
                    self.getAllFiles(path_i)
        return self.fileList 
    

    def updateMarkers(self, params):
        '''
        NOT FINISHED YET
        '''
        pass
        # for subPlotNr in range(self.nSubPlots):
        #     if str(subPlotNr) not in self.markers[str(self.currentEventId)]:
        #         self.markers[str(self.currentEventId)][str(subPlotNr)] = []    

        

        # if  'stalta_algorithm' in params.keys():
        #     method =  params['stalta_algorithm']
        #     nsta = int(params['nsta'])
        #     lsta = int(params['nlta'])
        #     pthres = float(params['pthreshold'])
        #     sthres = float(params['sthreshold'])

        
        # pCfs, sCfs = self.segy.calcStaLtaCF(nsta, lsta, method)
        # pPicks, sPicks = self.segy.pickPS(pCfs, sCfs, pthres, sthres)      
        
          

        # for subPlotNr in range(self.nSubPlots):            
            
        #     xP = pPicks[str(subPlotNr)] 
        #     xS = sPicks[str(subPlotNr)]

        #     subPlot = self.selectSubPlot(subPlotNr)

        #     markerList = []
                        

        #     for i in range(len(xP)):
        #         xp = xP[i]           
                
                                 
        #         pMarker1 = subPlot.axvline(xp, 0.1, 0.9, **self.p_line_style)
        #         pMarker2 = subPlot.scatter(xp, 0.0, **self.p_marker_style)	
 
        #         markerList.append({'px': xp, 
        #                         'pmarker': [pMarker1, pMarker2]
        #         })               
                
                
                    
        #     for i in range(len(xS)):
        #         xs = xS[i]
                 
        #         sMarker1 = subPlot.axvline(xs, 0.1, 0.9, **self.s_line_style)
        #         sMarker2 = subPlot.scatter(xs, 0.0, **self.s_marker_style)	
                	
        #         markerList.append({'sx': xs, 
        #                         'smarker': [sMarker1, sMarker2]
        #         })
            
            
        #     self.markers[str(self.currentEventId)][str(subPlotNr)] = markerList
            
        # self.fig.canvas.draw()                          
                    
           
            
        

    def setAutoPicker(self, object):

        self.autoPickerParams.clear()
        self.autoPickerParams = object
        print(self.autoPickerParams)


    def getComponentFlag(self):
	
        if self.xComponentToolButton.isChecked():
            xflag = 14
            self.xComponentToolButton.setIcon(QIcon(':/icons/windows/e-checked-48.png'))
        else:
            xflag = 0
            self.xComponentToolButton.setIcon(QIcon(':/icons/windows/e-48.png'))
        
        if self.yComponentToolButton.isChecked():
            yflag = 13 
            self.yComponentToolButton.setIcon(QIcon(':/icons/windows/n-checked-48.png'))
        else:
            yflag = 0
            self.yComponentToolButton.setIcon(QIcon(':/icons/windows/n-48.png'))
        
        if self.zComponentToolButton.isChecked():
            zflag = 12
            self.zComponentToolButton.setIcon(QIcon(':/icons/windows/z-checked-48.png'))
        else:
            zflag = 0
            self.zComponentToolButton.setIcon(QIcon(':/icons/windows/z-48.png'))
        
        flag = xflag + yflag +zflag

        return flag

    def onPickPwaveToggled(self, checked):
        
        if checked:
            self.modeFlag = 'p'
            self.pickSwaveToolButton.setChecked(False)
        elif self.pickSwaveToolButton.isChecked() == False:
            self.modeFlag = 'a'
        
        
        
    
    def onPickSwaveToggled(self, checked):
        
        if checked:
            self.modeFlag = 's'
            self.pickPwaveToolButton.setChecked(False)
        elif self.pickPwaveToolButton.isChecked() == False:
            self.modeFlag = 'a'
        

    def onAutoPickClicked(self):
                
        self.updateMarkers(self.autoPickerParams)

    def onPickSettingsClicked(self):

        dialog = AutoPickerSettingDialog(self)
        dialog.applySignal.connect(self.updateMarkers)
        dialog.show()
        dialog.exec_()       


    
    def setSegy(self, segy):
        self.segy = segy

    def getSegy(self):
        return self.segy 

    def updateAll(self, file):
               
        self.currentFile = file
        segy = pssegy.Segy(file)
        self.setSegy(segy) 
        self.xComponentToolButton.setChecked(False)
        self.yComponentToolButton.setChecked(False)
        self.zComponentToolButton.setChecked(True)
        self.initPlot()

    def updateEvent2File(self, ind):

        
        if str(ind) not in self.event2file and len(self.markers[str(ind)]):
            self.event2file[str(ind)] = self.currentFile
        
    def updateCurrentEvent2File(self):

        ind = self.currentEventId
        if str(ind) not in self.event2file and len(self.markers[str(ind)]):
            self.event2file[str(ind)] = self.currentFile    

    def initPlot(self):

        

        df = self.segy.df
        
        
        if self.normFlag == 1:
            self.zTraces = signorm(self.segy.zTraces)
            self.xTraces = signorm(self.segy.xTraces)
            self.yTraces = signorm(self.segy.yTraces) # @TODO: add norm flag here
        else:
            self.zTraces = self.segy.zTraces
            self.xTraces = self.segy.xTraces
            self.yTraces = self.segy.yTraces

        ns, ntr = self.zTraces.shape
        self.nSamples = ns
        self.nSubPlots  = ntr

        if self.nSubPlots > 12:
            self.fig.set_size_inches(self.size().width()/self.fig.get_dpi(),
                self.size().height() * self.nSubPlots / 12 /self.fig.get_dpi())
            self.staticCanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.staticCanvas.setMinimumHeight(self.size().height() * self.nSubPlots / 12 )
        
        
        t = np.arange(self.nSamples, dtype=np.float32) / df

        


        # if len(self.fig.axes):
        #     xlim = self.fig.axes[0].get_xlim()
        #     #print(xlim)
        # else:
        #     
        
        self.fig.clear()
        
        xlim = (0, ns)
        nrow = int(ntr)
        ncol = 1
        

        self.zLines = self.plotWaveform(self.zTraces, xlim, nrow, ncol, self.fig, self.zcolor)
        #self.nSubPlots = len(self.fig.axes)       
        

        
        self.plotRefWaveform(self.zTraces, self.nSubPlots, df, self.refFig) 


    def updatePlot(self):

        

        if len(self.fig.axes):
            xlim = self.fig.axes[0].get_xlim()
            #print(xlim)
        else:
            xlim = (0, self.nSamples)

        nrow = int(self.nSubPlots)
        ncol = 1

        if self.zComponentToolButton.isChecked() == False:
        
            self.removeLines(self.zLines)
            self.zLines = []
            
        else:
            if not len(self.zLines):            
                self.zLines = self.plotWaveform(self.zTraces, xlim, nrow, ncol, self.fig, self.zcolor)

        
        if self.xComponentToolButton.isChecked() == False:
            
            self.removeLines(self.xLines)
            self.xLines = []
            
        else: 
            if not len(self.xLines):           
                self.xLines = self.plotWaveform(self.xTraces, xlim, nrow, ncol, self.fig, self.xcolor)


        if self.yComponentToolButton.isChecked() == False:
            
            self.removeLines(self.yLines)
            self.yLines = []
            
        else:  
            if not len(self.yLines):          
                self.yLines = self.plotWaveform(self.yTraces, xlim, nrow, ncol, self.fig, self.ycolor)

        
        
        self.fig.canvas.draw()

        if not len(self.zLines) and not len(self.xLines) and not len(self.yLines):
            self.autoPickToolButton.setEnabled(False)
        else:
            self.autoPickToolButton.setEnabled(True)
            

    
    def removeLines(self, lines):
        if len(lines):
               for subPlotNr in range(self.nSubPlots):
                    
                    subPlot = self.selectSubPlot(subPlotNr)
                    line = lines[subPlotNr]
                    if line in subPlot.lines:
                        #print('line in subplot.lines')
                        subPlot.lines.remove(line)

    def updateToolBar(self):
		
        if self.xComponentToolButton.isChecked():
            
            self.xComponentToolButton.setIcon(QIcon(':/icons/windows/e-checked-48.png'))
        else:
            
            self.xComponentToolButton.setIcon(QIcon(':/icons/windows/e-48.png'))
        
        if self.yComponentToolButton.isChecked():
             
            self.yComponentToolButton.setIcon(QIcon(':/icons/windows/n-checked-48.png'))
        else:
            
            self.yComponentToolButton.setIcon(QIcon(':/icons/windows/n-48.png'))
        
        if self.zComponentToolButton.isChecked():
            
            self.zComponentToolButton.setIcon(QIcon(':/icons/windows/z-checked-48.png'))
        else:
            
            self.zComponentToolButton.setIcon(QIcon(':/icons/windows/z-48.png'))
        
    
    # Declare and register callbacks
    def onXlimsChanged(self, ax):
        
        if len(self.refFig.axes):
            #print ("updated xlims: ", ax.get_xlim())
            xlim = ax.get_xlim()

            self.refFig.axes[0].patches = [] 
            self.refFig.axes[1].patches = []
                
            # if self.spanMarker in self.refFig.axes[0].patches:
            #     #print('spanMarker in subplot.patches')
            #     self.refFig.axes[0].patches.remove(self.spanMarker)                
            #     self.spanMarker = None
                    
            df = self.segy.df
            
            self.spanMarker = self.refFig.axes[0].axvspan(xlim[0]/df, xlim[1]/df, facecolor='#2ca02c', alpha=0.25)
        self.refFig.canvas.draw()



    def onYlimsChanged(self, ax):
        pass
        #print ("updated ylims: ", ax.get_ylim())

      
    
    def update(self):
        self.updateToolBar()
        if self.segy is not None:
            self.updatePlot()   

                
    def plotRefWaveform(self, traces, ind, df, fig):

        fig.clear()
        ns, ntr = traces.shape

        xlim = (0/df, ns/df) 

        nTick = 10
        step = divmod(ns, nTick)[0]


        x_n =  np.linspace(0, ns, ns)
        x_t =  np.arange(ns, dtype=np.float32) / df

        ax1 = fig.add_subplot(1,1,1)

        line = ax1.plot(x_t, traces[:, ind -1] , linewidth=1.0, c = 'k', figure=fig)
        #ax1.set_xlabel(u'Time [second]')
        ax1.set_yticks([])
        ax1.set_xlim(xlim[0], xlim[1])
        

        # Set scond x-axis
        ax2 = ax1.twiny()

        # Decide the ticklabel position in the new x-axis,
        # then convert them to the position in the old x-axis
        newlabel = []
        for i in range(nTick+1):
            newlabel.append(i*step) # labels of the xticklabels: the position in the new x-axis
        n2t = lambda t: t/df # convert function: from Kelvin to Degree Celsius
        newpos   = [n2t(t) for t in newlabel]   # position of the xticklabels in the old x-axis
        ax2.set_xticks(newpos)
        ax2.set_xticklabels(newlabel)
        ax2.set_yticks([])
        #ax2.set_xlabel('Sample')
        ax2.set_xlim(ax1.get_xlim())

        self.spanMarker = self.refFig.axes[0].axvspan(xlim[0], xlim[1], facecolor='#2ca02c', alpha=0.5)   
        fig.subplots_adjust(left=0.02, bottom=0.25, right=0.98, top=0.75)
        
        fig.canvas.draw()

        

        
        return line
        
    def resizeEvent(self, ev):
        pass
        #print(ev)
        
        # # incorrect code here: only figure size changed while canvas not
        # self.refFig.set_size_inches(self.size().width()/self.refFig.get_dpi(),
        #         self.size().height() * 0.1/self.refFig.get_dpi())
        # self.refFig.canvas.draw()
        


    def plotWaveform(self, traces, xlim, nrow, ncol, fig, color):

        
        ns, ntr = traces.shape
        #t = np.arange(ns, dtype=np.float32) / df
        
        
        xData = np.linspace(1, ns, ns)
        lines = []


        for irow in range(nrow):
            if irow == 0:
                
                ax1 = fig.add_subplot(nrow, ncol, irow + 1)
                line = ax1.plot(xData, traces[:, irow]  , linewidth=1.0, c = color, figure=fig)
                ax1.callbacks.connect('xlim_changed', self.onXlimsChanged)  
                
                ax1.set_yticks([])
                ax1.set_xlim(int(xlim[0]), int(xlim[1]))
                ax1.set_xticks([])
            
            else:
                    
                subPlot = fig.add_subplot(nrow, ncol, irow + 1, sharex = ax1, sharey = ax1)
                subPlot.callbacks.connect('xlim_changed', self.onXlimsChanged)
                line = subPlot.plot(xData, traces[:, irow]  , linewidth=1.0, c = color, figure=self.fig)

            lines.append(line[0])

        fig.subplots_adjust(left=0.02, bottom=0.02, right=0.99, top=0.98)
        #self.fig.tight_layout() 
        fig.canvas.draw()
        return lines

    def onExport(self):

        self.updateCurrentEvent2File()
        
        fileName, ok = QFileDialog.getSaveFileName(self,
                                    "Export",
                                    "C:\\",
                                    "All Files (*);;CSV Files (*.csv)")

        if fileName:

            markers = self.markers

            dics = []

            dic = {'event_id':None,
                'file_name': None,
                'receiver_id': None,
                'p_pos': None, 
                's_pos':None}
            

            if len(markers[str(self.currentEventId)]):

                item  = markers[str(self.currentEventId)]
                    
                for plot_id, markers in item.items():

                    dic['event_id'] = self.currentEventId
                    dic['file_name'] = self.currentFile
                    dic['receiver_id'] = int(plot_id) + 1
                    if markers['p'] != None:
                        dic['p_pos'] =  markers['p']['pos']
                    else:
                        dic['p_pos'] =  DEFAULT_NUMERIC_VALUE
                    if markers['s'] != None:
                        dic['s_pos'] =  markers['s']['pos']
                    else:
                        dic['s_pos'] =  DEFAULT_NUMERIC_VALUE

                    
                    dics.append(copy.deepcopy(dic))
                        

                
                
                df = pd.DataFrame(dics)
                df.to_csv(fileName)
                
                QMessageBox.information(self,
                                            "Information",  
                                            "Event #" + str(self.currentEventId) + " has been saved successfully!",  
                                            QMessageBox.Ok) 
            else:
                QMessageBox.warning(self,
                                            "Warning",  
                                            "No P-wave or S-wave arrival time has been picked for Event #" + str(self.currentEventId) + ".\nPlease pick at least one arrival time for exporting.",  
                                            QMessageBox.Ok)  


        

        
        


    def onEditEvents(self):
        print('edit event list')



    def onClearPick(self):
        self.clearMarkers()

    def onClearAllPick(self):
        self.clearAllMarkers()

    def clearMarkers(self):

                      
        if len(self.markers[str(self.currentEventId)]):
            item = self.markers[str(self.currentEventId)]            
            for plot_id, markers in item.items():
                subPlot = self.selectSubPlot(int(plot_id))	
                for flag in ['p', 's']:
                    marker = markers[flag] 
                    if marker != None:                                               
                        mk = marker['marker']
                        subPlot.lines.remove(mk)
                        markers[flag] = None 
            self.markers[str(self.currentEventId)].clear()
            self.markers.pop(str(self.currentEventId)) 
            self.fig.canvas.draw()  
                

    def clearAllMarkers(self):
    
                      
        if len(self.markers):
            for event_id, item in self.markers.items():
                for plot_id, markers in item.items():
                    subPlot = self.selectSubPlot(int(plot_id))	
                    for flag in ['p', 's']:
                        marker = markers[flag] 
                        if marker != None:                                               
                            mk = marker['marker']
                            subPlot.lines.remove(mk)
                            markers[flag] = None 
            self.markers.clear() 
            self.fig.canvas.draw()  
                
                    
        

    def deleteMarker(self,event):

        subPlotNr = self.getSubPlotNr(event)
        
        if subPlotNr == None:
            return

        subPlot = self.selectSubPlot(subPlotNr)	

        
        plotIdPopped = None
        for event_id, item in self.markers.items():
            for plot_id, markers in item.items():
                if plot_id == str(subPlotNr):
                    for flag in ['p', 's']:
                        marker = markers[flag]
                        if marker != None and abs (marker['pos'] - event.xdata) <=10:                        
                            mk = marker['marker']
                            subPlot.lines.remove(mk)
                            markers[flag] = None 
                if markers['p'] == None and markers['s'] == None:
                    plotIdPopped = plot_id

        if plotIdPopped != None:
            self.markers[str(self.currentEventId)].pop(plotIdPopped)
        self.fig.canvas.draw()            
        

        


        
    def getSubPlotNr(self, event):
    
        """
        Get the nr of the subplot that has been clicked
        
        Arguments:
        event -- an event
        
        Returns:
        A number or None if no subplot has been clicked
        """
    
        i = 0
        axisNr = None
        for axis in self.fig.axes:
            if axis == event.inaxes:
                axisNr = i		
                break
            i += 1
        return axisNr
        


        
    def selectSubPlot(self, i):	
        """
        Select a subplot		

        Arguments:
        i -- the nr of the subplot to select

        Returns:
        A subplot
        """
        
        
        #pyplot.subplot(self.nSubPlots, 1, i+1)
        return self.fig.axes[ i ]
    
        
    def onClick(self, event):
    
        """
        Process a mouse click event. If a mouse is right clicked within a
        subplot, the return value is set to a (subPlotNr, xVal, yVal) tuple and
        the plot is closed. With right-clicking and dragging, the plot can be
        moved.
        
        Arguments:
        event -- a MouseEvent event
        """
            
        mode = self.pltToolBar.mode 
        if event.button == 1 and mode != 'zoom rect' and self.modeFlag != 'a':	# left clicked	
        
            subPlotNr = self.getSubPlotNr(event)

            if subPlotNr == None:
                return
            else:
                if str(subPlotNr) not in self.markers[str(self.currentEventId)]:
                    self.markers[str(self.currentEventId)][str(subPlotNr)] = {'p': None, 's':None}    
                
                
                marker = {'pos': None,
                            'marker': None
                            }
            
            subPlot = self.selectSubPlot(subPlotNr)
            
            

            if self.markers[str(self.currentEventId)][str(subPlotNr)][self.modeFlag] == None:

                if self.modeFlag == 'p':
                    mks = subPlot.axvline(event.xdata, 0.1, 0.9, **self.p_line_style)
                else:
                    mks = subPlot.axvline(event.xdata, 0.1, 0.9, **self.s_line_style)

                marker['pos'] = event.xdata
                marker['marker'] = mks
                self.markers[str(self.currentEventId)][str(subPlotNr)][self.modeFlag] = marker

            else:
                QMessageBox.warning(self,
                                "Warning",
                                "For each microseismic event, there should only one P-wave arrival time and one S-wave arrival time be picked.\nPlease firstly clear the existing one and then re-pick the new one",
                                QMessageBox.Ok)
            self.fig.canvas.draw()        

        
        elif event.button == 3 and mode != 'zoom rect': # right clicked
            
            self.deleteMarker(event)
        # else:			
        #     # Start a dragFrom
        #     self.dragFrom = event.xdata
        
    def onKey(self, event):
        
        """
        Handle a keypress event. The plot is closed without return value on
        enter. Other keys are used to add a comment.
        
        Arguments:
        event -- a KeyEvent
        """
    
        # if event.key == 'enter':
        #     self.fig.close()
        #     return
            
        # if event.key == 'escape':
        #     self.clearMarker()
        #     return
            
        # if event.key == 'backspace':
        #     self.comment = self.comment[:-1]
        # elif len(event.key) == 1:			
        #     self.comment += event.key
        
        # event.canvas.draw()
        pass
            
    def onRelease(self, event):
    
        """
        Handles a mouse release, which causes a move
        
        Arguments:
        event -- a mouse event
        """
    
        if self.dragFrom == None or event.button != 3:
            return			
        dragTo = event.xdata
        dx = self.dragFrom - dragTo
        for i in range(self.nSubPlots):
            subPlot = self.selectSubPlot(i)			
            xmin, xmax = subPlot.get_xlim()
            xmin += dx
            xmax += dx				
            subPlot.set_xlim(xmin, xmax)
        event.canvas.draw()
                                            
    def onScroll(self, event):
    
        """
        Process scroll events. All subplots are scrolled simultaneously
        
        Arguments:
        event -- a MouseEvent
        """
    
        for i in range(self.nSubPlots):
            subPlot = self.selectSubPlot(i)		
            xmin, xmax = subPlot.get_xlim()
            dx = xmax - xmin
            cx = (xmax+xmin)/2
            if event.button == 'down':
                dx *= 1.1
            else:
                dx /= 1.1
            _xmin = cx - dx/2
            _xmax = cx + dx/2	
            subPlot.set_xlim(_xmin, _xmax)
        event.canvas.draw()


        
    def updateXLim(self, lim):
        '''
        lim: a tuple, (x1, x2)
        '''

        x1 = lim[0]
        x2 = lim[1]
        for axis in self.fig.axes:
                    axis.set_xlim(x1, x2)
                
        self.fig.canvas.draw()	

class AutoPickerSettingDialog(QDialog):

    applySignal = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(AutoPickerSettingDialog, self).__init__(parent)

        

        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(StaLtaTab(self), "STA/LTA")
        #tabWidget.addTab(ArAicTab(), "AR-AIC")

        defaultButton = QPushButton(' Restore Defaults ')
        spacer1 = QSpacerItem(20,20, QSizePolicy.Minimum)
        applyButton = QPushButton('Apply')
       
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        applyButton.clicked.connect(self.onApplyClicked)



        hbl = QHBoxLayout()
        hbl.addWidget(defaultButton)
        hbl.addItem(spacer1)
        hbl.addWidget(applyButton)
        hbl.addWidget(buttonBox)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addLayout(hbl)
        self.setLayout(mainLayout)

        self.setWindowTitle("AutoPicker Settings")

    def onApplyClicked(self):

        configDict = self.tabWidget.currentWidget().getConfig()        

        self.applySignal.emit(configDict)
        
        



class StaLtaTab(QWidget):
    def __init__(self, parent=None):
        super(StaLtaTab,self).__init__(parent)

        self.config = ConfigManager()

        self.config.set_defaults({            
            'stalta_algorithm': 'Recursive',            
            'nsta': '20',
            'nlta': '50',
            'pthreshold': '1.75',
            'sthreshold': '2.0'
        })
        
        self.initUI()
    
    def initUI(self):
        
        # Algrithm GroupBox
        self.algorithmGroupBox = QGroupBox('Algorithm', self)

        self.algorithmLabel = QLabel('Select an algorithm')
        
        self.algorithmComboBox = QComboBox()
        self.algorithmComboBox.addItems(['Recursive', 'Delayed', 'Classic'])
        self.config.add_handler('stalta_algorithm', self.algorithmComboBox)
        
        hb_algorithm = QHBoxLayout()
        hb_algorithm.addWidget(self.algorithmLabel)
        hb_algorithm.addWidget(self.algorithmComboBox)

        
        self.algorithmGroupBox.setLayout(hb_algorithm)

        # Window GroupBox
        self.windowGroupBox = QGroupBox('Window', self)

        self.staLabel = QLabel('Short Window Length')
        self.staLineEdit = QLineEdit()
        self.config.add_handler('nsta', self.staLineEdit)

        self.ltaLabel = QLabel('Long Window Length ')
        self.ltaLineEdit = QLineEdit()
        self.config.add_handler('nlta', self.ltaLineEdit)

        
        
        hb_window1 = QHBoxLayout()
        hb_window1.addWidget(self.staLabel)
        hb_window1.addWidget(self.staLineEdit)

        hb_window2 = QHBoxLayout()
        hb_window2.addWidget(self.ltaLabel)
        hb_window2.addWidget(self.ltaLineEdit)

        vb_window = QVBoxLayout()
        vb_window.addLayout(hb_window1)
        vb_window.addLayout(hb_window2)
        self.windowGroupBox.setLayout(vb_window)



        # Threshold GroupBox
        self.thresholdGroupBox = QGroupBox('Threshold', self)

        self.pThresholdLabel = QLabel('P-wave Threshold')
        self.pThresholdLineEdit = QLineEdit()
        self.config.add_handler('pthreshold', self.pThresholdLineEdit)

        self.sThresholdLabel = QLabel('S-wave Threshold')
        self.sThresholdLineEdit = QLineEdit()
        self.config.add_handler('sthreshold', self.sThresholdLineEdit)

        
        
        hb_threshold1 = QHBoxLayout()
        hb_threshold1.addWidget(self.pThresholdLabel)
        hb_threshold1.addWidget(self.pThresholdLineEdit)

        hb_threshold2 = QHBoxLayout()
        hb_threshold2.addWidget(self.sThresholdLabel)
        hb_threshold2.addWidget(self.sThresholdLineEdit)

        vb_threshold = QVBoxLayout()
        vb_threshold.addLayout(hb_threshold1)
        vb_threshold.addLayout(hb_threshold2)
        self.thresholdGroupBox.setLayout(vb_threshold)

        # # PushButtons: Apply, Cancel, OK
        # self.applyButton = QPushButton('Apply')
        # self.cancelButton = QPushButton('Cancel')
        # self.okButton = QPushButton('OK')

        # hb_button = QHBoxLayout()
        # hb_button.addWidget(self.applyButton)
        # hb_button.addWidget(self.cancelButton)
        # hb_button.addWidget(self.okButton)


        vbl= QVBoxLayout()
        vbl.addWidget(self.algorithmGroupBox)
        vbl.addWidget(self.windowGroupBox)
        vbl.addWidget(self.thresholdGroupBox)
        #vbl.addLayout(hb_button)

        self.setLayout(vbl)        

        self.config.updated.connect(self.showConfig)
        self.showConfig()

    def showConfig(self):
        '''
        test purpose only
        '''
        print(self.config.as_dict())

    def getConfig(self):
        return self.config.as_dict()









class EventIDWidget(QWidget):
    def __init__(self, parent=None):
        super(EventIDWidget,self).__init__(parent)

        self.parent = parent
        self.eventIdLabel = QLabel('Event ID')
        self.eventIdSpinBox = QSpinBox()
        self.eventIdSpinBox.setMinimum(int(1))
        self.eventIdSpinBox.setMaximum(int(1e4))
        self.eventIdSpinBox.valueChanged.connect(self.onValueChange)

        self.indList = []
        self.indList.append(1)
        

        hbox = QHBoxLayout()
        hbox.addWidget(self.eventIdLabel)
        hbox.addWidget(self.eventIdSpinBox)
        

        self.setLayout(hbox)

    def onValueChange(self):
        ind = self.eventIdSpinBox.value()
        self.indList.append(ind)
        self.parent.currentEventId = ind
        indPrevious = self.indList[-2]
        self.parent.updateEvent2File(indPrevious)
        #self.parent.clearMarkers()




class FileToolBar(QToolBar):

    #fileSelectedSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(FileToolBar,self).__init__(parent)


        self.parent = parent
        self.fileList = []
        self.currentFile = None
        self.currentIndex = 0
        self.indexMax = None

        self.actionPrevious = QAction(QIcon(':/icons/windows/previous-48.png'), "&Previous",
                self, shortcut= '',
                statusTip="Previous SEG-Y file", triggered=self.onPrevious)
        self.actionNext = QAction(QIcon(':/icons/windows/next-48.png'), "&Next",
                self, shortcut= '',
                statusTip="Next SEG-Y file", triggered=self.onNext)
        
        
        self.fileComboBox = QComboBox()
        #self.fileComboBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.fileComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        #self.fileComboBox.setMinimumHeight(self.height())


        
        

       
        self.addAction(self.actionPrevious)
        self.addWidget(self.fileComboBox)
        self.addAction(self.actionNext)

       

    def initWidget(self, fileList):
        '''
        fileList: file list
        '''
        self.fileList = fileList
        self.indexMax = len(self.fileList)
        fileNameList = []
        for item in fileList:            
            fileName = os.path.splitext(os.path.basename(item))[0]
            fileNameList.append(fileName)

        self.fileComboBox.addItems(fileNameList)
        self.fileComboBox.setCurrentIndex(0)
        # signals and slots        
        self.fileComboBox.currentIndexChanged.connect(self.selectionChanged)

    def selectionChanged(self):
        self.currentIndex = self.fileComboBox.currentIndex()
        self.currentFile = self.fileList[self.currentIndex]        
        self.parent.updateAll(self.currentFile)

    def onPrevious(self):
        if self.currentFile != 0:
            self.currentIndex -= 1
            self.fileComboBox.setCurrentIndex(self.currentIndex)
    
    def onNext(self):
        if self.currentFile != self.indexMax:
            self.currentIndex += 1
            self.fileComboBox.setCurrentIndex(self.currentIndex)

if __name__ == "__main__":
    qapp = QApplication(sys.argv)
    app = EventPicker()

    filename = 'xx' # replace this with your .sgy file
    
    segy = pssegy.Segy(filename)
    app.setSegy(segy) 
    app.initPlot()
    app.show()
    qapp.exec_()


