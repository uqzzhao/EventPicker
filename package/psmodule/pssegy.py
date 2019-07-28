import numpy as np  
# -*- coding: utf-8 -*-

"""

A class based on io functions in segypy.py to read and write SEG-Y Rev 1.0 files

@author:     Zhengguang Zhao
@copyright:  Copyright 2016-2019, Zhengguang Zhao.
@license:    LGPL v2.1
@contact:    zg.zhao@outlook.com


"""

from package.psmodule.segypy import readSegy

##############
# segy class

class Segy:
    
    def __init__(self, fileName):



        self.traceData = None
        self.volHeader =  None
        self.traceHeader =  None
        self.zTraces = None
        self.xTraces = None
        self.yTraces = None

        self.df = None # unit is Hz
        self.dt = None # unit is second

        self.ns = None
        self.ntr = None

        self.componentFlag = int(3) # default is 1C


        self.loadSegy(fileName)
        self.setSampleRate(self.traceHeader)
        self.setComponentFlag(self.traceHeader)
        self.setSampleNumber(self.volHeader)
        self.setTraceNumber(self.volHeader)
        self.setComponentData()

    
    def pArrivals(self):
        return self.pPicks

    def sArrivals(self):
        return self.sPicks

    def pickPS(self, p_cfs, s_cfs, p_thres, s_thres):
        from package.psmodule.pspicker import trigger_onset

        count = 0
        sPicks = {}
        pPicks = {}

        ns, ntr = p_cfs.shape

        for i in range(ntr):
            
            p_on_off = trigger_onset(p_cfs[:,i], p_thres, p_thres)
            if len(p_on_off):
                pPicks[str(i)] = p_on_off[:, 0]
            else:
                pPicks[str(i)] = []
                

            s_on_off = trigger_onset(s_cfs[:,i], s_thres, s_thres)
            if len(s_on_off):
                sPicks[str(i)] = s_on_off[:, 0]
            else:
                sPicks[str(i)] = []

        return pPicks, sPicks   

    

    
    def setComponentData(self):
        ntr = self.ntr
        if self.traceHeader['TraceIdentificationCode'][0] == 12: 
            self.zTraces = self.traceData[:,0:ntr:3] # indexing from first element to last element with increment(skipt) 3 
            self.xTraces = self.traceData[:,1:ntr:3] 
            self.yTraces = self.traceData[:,2:ntr:3] 
        else:
            self.xTraces = self.traceData[:,0:ntr:3] # indexing from first element to last element with increment(skipt) 3 
            self.yTraces = self.traceData[:,1:ntr:3] 
            self.zTraces = self.traceData[:,2:ntr:3]

        

    
    def loadSegy(self, fileName):
        traceData, volHeader, traceHeader =  readSegy(fileName)
        self.traceData = traceData
        self.volHeader = volHeader
        self.traceHeader = traceHeader


    def setTraceNumber(self, vh ):
        '''
        vh: volume header

        '''
        self.ntr = vh['ntraces']

    def setSampleNumber(self, vh ):
        '''
        vh: volume header

        '''
        self.ns = vh['ns']
    

    def setComponentFlag(self, th):
        '''
        th: trace header

        '''
        cdp = th['cdp']
        inline3D = th['Inline3D']
        code = th['TraceIdentificationCode']
        if cdp[0] != cdp[1] or inline3D[0] != inline3D[1] or code[0] != code[1]:
            self.componentFlag = int(3)
        else:
            self.componentFlag = int(1)

    def setSampleRate(self, th):
        '''
        th: trace header

        '''

        dt = th['dt'][0]  # unit is us

        self.dt = dt*1e-6
        self.df = 1.0/self.dt

