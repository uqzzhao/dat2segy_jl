# -*- coding: utf-8 -*-
"""
Data format conversion from .dat to SEG-Y format.

@author:     Zhengguang Zhao
@copyright:  Copyright 2016-2019, Zhengguang Zhao.
@license:    MIT
@contact:    zg.zhao@outlook.com


"""

import numpy as np

import matplotlib.pyplot as plt

from package.psmodule import pssegy 
from package.utils.utils import save_dict, transform_separator


import time
import struct
import datetime

l_int = struct.calcsize('i')
l_uint = struct.calcsize('I')
l_long = 4
# Next line gives wrong result on Linux!! (gives 8 instead of 4)
# l_long = struct.calcsize('l')
l_ulong = struct.calcsize('L')
l_short = struct.calcsize('h')
l_ushort = struct.calcsize('H')
l_char = struct.calcsize('c')
l_uchar = struct.calcsize('B')
l_float = struct.calcsize('f')

NUMPY_DTYPES = {'ibm':     np.dtype('>f4'),

                'int32':   np.dtype('>i4'),

                'int16':   np.dtype('>i2'),

                'uint16':   np.dtype('>u2'),

                'float32': np.dtype('>f4'),

                'int8':    np.dtype('>i1')}


def parseDataBuffer(fs, dsf = 'int32', endian = '>', skip = 512, com = 3):

    
    
    data = fs.read()

    filesize = len(data)

    headsize = skip

    tracesize = filesize - headsize

    

    cformat = NUMPY_DTYPES[dsf]
    
    if dsf == 'int32' or 'float32':
        bps = 4
        
        
    else:
        bps = 2

    ns_3c = int(np.floor(tracesize/bps))
     

    # read in trace values

    fs.seek(headsize) 
    trc=fs.read()
    traceData = np.frombuffer(trc, cformat)
    
    y = traceData[0:ns_3c:3] 
    x = traceData[1:ns_3c:3]
    z = traceData[2:ns_3c:3]
     

    traces=np.concatenate((y.reshape(-1,1),  x.reshape(-1,1),  z.reshape(-1,1)), axis=1)

    ns, ntr = traces.shape

    if dsf == 'int8':
    
        for i in range(ns):
            for j in range(ntr):
                if traces[i][j] > 128:
                    traces[i][j] = traces[i][j] - 256

    
    # # test code
    # import struct
    # fs.seek(headsize)
    # for chunk in iter(lambda: fs.read(4), ''):
    #     integer_value = struct.unpack('>l', chunk)[0]
        # print(integer_value)

    return traces

def saveSegy(filename, trace, dt = 1000):

    ## prepare SEGY header
    ns, ntr = trace.shape
    

    SH = pssegy.getDefaultSegyHeader(ntr, ns)
    STH = pssegy.getDefaultSegyTraceHeaders(ntr, ns, dt) 

    STH['TraceIdentificationCode'][0:ntr:3] = 14.0
    STH['TraceIdentificationCode'][1:ntr:3] = 13.0
    STH['TraceIdentificationCode'][2:ntr:3] = 12.0

    rcvlist = [1]
    STH['Inline3D'][0:int(ntr/3)] = np.array(rcvlist)
    STH['Inline3D'][int(ntr/3): 2*int(ntr/3)] = np.array(rcvlist)
    STH['Inline3D'][2*int(ntr/3): 3*int(ntr/3)] = np.array(rcvlist)


    # deal with date time
    
    ns_start = 0 #int(istart/1000) # delayed seconds
    # delay_hour = (ns_start/1000/60)//60
    # delay_min = floor(ns_start/1000/60)%60)
    # delay_sec = (ns_start/1000/60)%60 - delay_min) * 60

    # timestamp = 0
    # d = datetime.timedelta(seconds=ns_start)
    # new_timestamp = timestamp+d

    # record_day = datetime.datetime(2018,12,1)
    # day_of_year = (record_day - datetime.datetime(record_day.year, 1, 1)).days + 1
    # #print(day_of_year)
    

    # STH['YearDataRecorded'] = np.ones((ntr,), dtype = np.float) * 2018.0
    # STH['DayOfYear'] = np.ones((ntr,), dtype = np.float) * day_of_year
    # STH['HourOfDay'] = np.ones((ntr,), dtype = np.float) * new_timestamp.hour
    # STH['MinuteOfHour'] = np.ones((ntr,), dtype = np.float) * new_timestamp.minute
    # STH['SecondOfMinute'] = np.ones((ntr,), dtype = np.float) * new_timestamp.second
    

    # base_name = new_timestamp.strftime("%Y%m%d_%H%M%S")

    # write SEG-Y file to disk
    segy = pssegy.Segy(trace, SH, STH)
    segy.toSegyFile(filename)

 


def resample(input_signal,src_fs,tar_fs):
    dtype = np.float32
    signal_len = len(input_signal)
    signal_time_max = 1.0*(signal_len-1) / src_fs
    src_time = 1.0 * np.linspace(0,signal_len,signal_len) / src_fs
    tar_time = 1.0 * np.linspace(0,np.int(signal_time_max*tar_fs),np.int(signal_time_max*tar_fs)) / tar_fs
    output_signal = np.interp(tar_time,src_time,input_signal).astype(dtype)

    return output_signal


def wiggle(Data, SH={}, maxval=-1, skipt=1, lwidth=.5, x=[], t=[], gain=1, type='VA', color='black', ntmax=1e+9):
    """
    wiggle(Data,SH)
    """
    import matplotlib.pylab as plt
    import numpy as np
    import copy
    
    yl='Sample number'
    
    ns = Data.shape[0]
    ntraces = Data.shape[1]

    if ntmax<ntraces:
        skipt=int(np.floor(ntraces/ntmax))
        if skipt<1:
                skipt=1


    if len(x)==0:
        x=range(0, ntraces)

    if len(t)==0:
        t=range(0, ns)
    else:
        yl='Time  [s]'
    
    
    # overrule time form SegyHeader
    if 'time' in SH:
        t = SH['time']
        yl='Time  [s]'
    
        
    dx = x[1]-x[0]    
    if (maxval<=0):
        Dmax = np.nanmax(Data)
        maxval = -1*maxval*Dmax
        #print('pssegy.wiggle: maxval = %g' % maxval)
        
    fig, (ax1) = plt.subplots(1, 1)
    # fig = plt.gcf()
    # ax1 = plt.gca()
    
    for i in range(0, ntraces, skipt):
        # use copy to avoid truncating the data
        trace = copy.copy(Data[:, i])
        trace[0] = 0
        trace[-1] = 0
        ax1.plot(x[i] + gain * skipt * dx * trace / maxval, t, color=color, linewidth=lwidth)
        
        if type=='VA':
            for a in range(len(trace)):
                if (trace[a] < 0):
                    trace[a] = 0
                    # pylab.fill(i+Data[:,i]/maxval,t,color='k',facecolor='g')
            #ax1.fill(x[i] + dx * Data[:, i] / maxval, t, 'k', linewidth=0, color=color)
            ax1.fill(x[i] + gain * skipt * dx * trace / (maxval), t, 'k', linewidth=0, color=color)

    ax1.grid(True)
    ax1.invert_yaxis()
    plt.ylim([np.max(t),np.min(t)])
    

    plt.xlabel('Trace number')
    plt.ylabel(yl)
    if 'filename' in SH:
        plt.title(SH['filename'])
    ax1.set_xlim(-1, ntraces)
    plt.show()
    


def main():

    filename = 'D:/cgs_data/test/01T.dat'

    with open(filename, 'rb') as f:

        traces = parseDataBuffer(f, dsf = 'int32')


    # resample

    src_fs = 2000
    tar_fs = 500

    

    # plot

    fig, ax = plt.subplots()
    ax.plot(traces[:,0])
    plt.show()

    fig, ax = plt.subplots()
    ax.plot(traces[:,1])
    plt.show()

    fig, ax = plt.subplots()
    ax.plot(traces[:,2])
    plt.show()

    
    #wiggle(traces)

    # tile
    #data = np.tile(traces, 30)

    # write SEG-Y file to disk

    filename  = 'D:/cgs_data/test/01T.sgy'

    saveSegy(filename, traces, dt = 1000)



    

    







if __name__ == '__main__':

    main()