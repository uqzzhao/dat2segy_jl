# -*- coding: utf-8 -*-

import os
import copy

from PyQt5.QtCore import pyqtSignal, QThread
from ..psmodule import pssegy 
from ..utils.utils import save_dict, transform_separator


import numpy as np
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


HH = [  '00', 
        '01', 
        '02',
        '03',
        '04',
        '05',
        '06',
        '07',
        '08',
        '09',
        '10',
        '11',
        '12',
        '13',
        '14',
        '15',
        '16',
        '17',
        '18',
        '19',
        '20',
        '21',
        '22',
        '23']

MM = [  '00', 
        '01', 
        '02',
        '03',
        '04',
        '05',
        '06',
        '07',
        '08',
        '09',
        '10',
        '11',
        '12',
        '13',
        '14',
        '15',
        '16',
        '17',
        '18',
        '19',
        '20',
        '21',
        '22',
        '23',
        '24',
        '25',
        '26',
        '27',
        '28',
        '29',
        '30',
        '31',
        '32',
        '33',
        '34',
        '35',
        '36',
        '37',
        '38',
        '39',
        '40',
        '41',
        '42',
        '43',
        '44',
        '45',
        '46',
        '47',
        '48',
        '49',
        '50',
        '51',
        '52',
        '53',
        '54',
        '55',
        '56',
        '57',
        '58',
        '59']



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
    #print(ns)   

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

    

    return traces



def list_subfolders(root):

    folder_list = []
    map_dict = {} # key = folder name; value = full folder path

    # method 1
    # d = '.'
    # subdirs = [os.path.
    # (d, o) for o in os.listdir(d) if os.path.isdir(os.path.join(d,o))]

    # method 2

    if (os.path.exists(root)):
    
        files = os.listdir(root)

        for file in files:
            
            path = transform_separator(os.path.join(root,file))
            
            if (os.path.isdir(path)):
                h = os.path.split(path)

                folder = h[1]
                
                folder_list.append(folder)
                map_dict[folder] = path


    return folder_list, map_dict 

def list_subfiles(root):

    file_list = []
    map_dict = {} # key = folder name; value = full folder path

    # method 1
    # d = '.'
    # subdirs = [os.path.join(d, o) for o in os.listdir(d) if os.path.isdir(os.path.join(d,o))]

    # method 2

    if (os.path.exists(root)):
    
        files = os.listdir(root)

        for file in files:
            
            path = transform_separator(os.path.join(root,file))
            
            if (os.path.isfile(path)):
                h = os.path.split(path)

                file = h[1]
                
                file_list.append(file)
                map_dict[folder] = path


    return file_list, map_dict 


def createRcvList(rcvs, initial = 4):

    rcvNames_float = []
    for r in rcvs:

        rfloat = float(str(initial) + r)

        rcvNames_float.append(rfloat)

    return rcvNames_float


def convert2segy(outfile, filelist, rcvlist, args):

    i = 0

    data = None

    for filename, rcvname in zip(filelist, rcvlist):


        with open(filename, 'rb') as f:

            traces = parseDataBuffer(f, dsf = args['dsf'], skip = args['header_size']) 
            #print(traces.shape) 

        if i == 0:

            data =  traces.copy()

        else:

            data = np.concatenate((data, traces), axis = 1)



        i +=1




    ## prepare SEGY header
    dt = args['dt']
    ns, ntr = data.shape
    

    SH = pssegy.getDefaultSegyHeader(ntr, ns, dt)
    STH = pssegy.getDefaultSegyTraceHeaders(ntr, ns, dt) 

    STH['TraceIdentificationCode'][0:ntr:3] = 14.0
    STH['TraceIdentificationCode'][1:ntr:3] = 13.0
    STH['TraceIdentificationCode'][2:ntr:3] = 12.0

    field = args['rcv_field']

    STH[field][0:int(ntr/3)] = np.array(rcvlist)
    STH[field][int(ntr/3): 2*int(ntr/3)] = np.array(rcvlist)
    STH[field][2*int(ntr/3): 3*int(ntr/3)] = np.array(rcvlist)


    # deal with date time

    basename = os.path.basename(outfile)
    fname  = os.path.splitext(basename)[0]

    ymd_hms = fname.split('_')
    ymd = ymd_hms[0]
    hms = ymd_hms[1]




    yy = int(float(ymd[:4]))
    mm = int(float(ymd[4:6]))
    dd = int(float(ymd[6:]))

    hour = int(float(hms[:2]))
    minute = int(float(hms[2:4]))
    second = 0

    record_day = datetime.datetime(yy,mm,dd)
    day_of_year = (record_day - datetime.datetime(record_day.year, 1, 1)).days + 1
    #print(day_of_year)
    

    STH['YearDataRecorded'] = np.ones((ntr,), dtype = np.float) * yy
    STH['DayOfYear'] = np.ones((ntr,), dtype = np.float) * day_of_year
    STH['HourOfDay'] = np.ones((ntr,), dtype = np.float) * hour
    STH['MinuteOfHour'] = np.ones((ntr,), dtype = np.float) * minute
    STH['SecondOfMinute'] = np.ones((ntr,), dtype = np.float) * second
    

 

    # write SEG-Y file to disk
    segy = pssegy.Segy(data, SH, STH)
    segy.toSegyFile(outfile)
   

    print(outfile, ' written[OK].')



class SegyConverterThread(QThread):
    """
    Thread for merging SEGY files
    """
    labelSignal_ = pyqtSignal(str)
    progressSignal_ = pyqtSignal(int, int)
    
    finishSignal_ = pyqtSignal(int, str)

    sendError_ = pyqtSignal(str)


    def __init__(self, inpath, outpath, args, parent=None):
        super(SegyConverterThread, self).__init__(parent)

        
        self.running = True

        
        
        self.inpath = inpath

        self.outpath = outpath

        self.args = args


        
    
    def run(self):

        try:

            
            self.exportSegy()

        except  Exception as reason:
            
            self.sendError_.emit(str(reason))

    def stop(self):
    
        self.running = False
        
        self.terminate()
    
    def __del__(self):

        self.quit()
        self.wait()


       
         

    def exportSegy(self):

        self.labelSignal_.emit("Writing to SEG-Y files in process...")


        root = self.inpath

        outpath = self.outpath

        args = self.args


        # read in geophone folders as reciever list

        rcvfolders, rcvfolder_dict = list_subfolders(root)


        # create reciver list in float

        initial = args['initial']

        rcv_list = createRcvList(rcvfolders, initial = initial)


        # create time list as dict, key = rcv, value = yymmdd

        rcv_ymd_dict = {}

        ymdfolders = []
        ymdfolder_dict = {}

        # ymd

        for fd in rcvfolders:
    

            rcvpath = rcvfolder_dict[fd] # receiver folder

            ymdfolders, ymdfolder_dict = list_subfolders(rcvpath)

            rcv_ymd_dict[fd] = ymdfolders

        

        # merge .dat files with same timestamp


        maxVal = len(ymdfolders)
        self.progressSignal_.emit(0, maxVal)

        for n, fd in enumerate(ymdfolders):

            if not self.running:                                       
                self.running = True
                break

            for h in HH:

                tlist = []

                for m in MM:

                    filelist = []
                    
                    rcvlist = []

                    
                    timestamp = fd + '_' + h + m + '00'
                    tlist.append(timestamp)

                    for i, rcv in enumerate(rcvfolders):

                        filename =  transform_separator(os.path.join(root, rcv, fd, h, m + 'T.dat'))

                        if os.path.exists(filename):

                            filelist.append(filename)
                            rcvlist.append(rcv_list[i])
                
                    outfile = transform_separator(os.path.join(outpath, timestamp + '.sgy'))

                    self.labelSignal_.emit('Writing SEG-Y file: ' + outfile)    
                    print('Writing SEG-Y file: ' + outfile)

                    if len(filelist):
                        convert2segy(outfile, filelist, rcvlist, args)
                        self.progressSignal_.emit(n, maxVal) 

        self.finishSignal_.emit(int(1), 'SEG-Y files conversion completed.') 



       

        
           

    
    
    
    