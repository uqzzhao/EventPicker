# -*- coding: utf-8 -*-


"""

Utility functions 

@author:     Zhengguang Zhao
@copyright:  Copyright 2016-2019, Zhengguang Zhao.
@license:    LGPL v2.1
@contact:    zg.zhao@outlook.com


"""

import numpy as np
import csv
import re
import linecache
import os
import dis
import inspect
import sys

import _pickle as pickle

from datetime import datetime
import logging
from math import isnan, isinf, sqrt

Nan = float("nan") # Not-a-number capitalized like None, True, False
Inf = float("inf") # infinite value capitalized ...




def signorm (Data):

    dim = Data.ndim

    if dim == 1:
        Data = Data.reshape(len(Data), 1)
    
    (ns, nt) = Data.shape
    # find max of each trace to normalization
    normed = np.empty((ns, nt), dtype='float32')
    maxval = np.empty((nt, 1), dtype='float32')
    for i in range(0, nt, 1):
        trace = np.array(Data[:, i])
        if trace.max() > abs(trace.min()):
            maxval[i] = trace.max()
        else:
            maxval[i] = abs(trace.min())
        normed[:,i] = trace/maxval[i]    
    
    return normed 




def save_dict(di_, filename_):
    with open(filename_, 'wb') as f:
        pickle.dump(di_, f)

def load_dict(filename_):
    with open(filename_, 'rb') as f:
        ret_di = pickle.load(f)
    return ret_di

def unique_list(listA):
    return sorted(set(listA), key = listA.index)

def reduce_list(listA, listB): # sequence of elements will change randomly
     return list(set(listA) - set(listB))



