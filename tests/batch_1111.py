
import os 
import numpy as np

import matplotlib.pyplot as plt

from package.psmodule import pssegy 
from package.utils.utils import save_dict, transform_separator, list_folders


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


NUMPY_DTYPES = {'ibm':     np.dtype('<f4'),

                'int32':   np.dtype('<i4'),

                'int16':   np.dtype('<i2'),

                'uint16':   np.dtype('<u2'),

                'float32': np.dtype('<f4'),

                'int8':    np.dtype('<i1')}


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

YMD = ['20191111', '20191112', '20191113', '20191114', '20191115','20191116','20191117']

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

    
    # # test code
    # import struct
    # fs.seek(headsize)
    # for chunk in iter(lambda: fs.read(4), ''):
    #     integer_value = struct.unpack('>l', chunk)[0]
        # print(integer_value)

    return traces

def saveSegy(filename, trace, dt = 500):

    ## prepare SEGY header
    ns, ntr = trace.shape
    

    SH = pssegy.getDefaultSegyHeader(ntr, ns)
    STH = pssegy.getDefaultSegyTraceHeaders(ntr, ns, dt) 

    STH['TraceIdentificationCode'][0:int(ntr/3)] = 14.0
    STH['TraceIdentificationCode'][int(ntr/3): 2*int(ntr/3)] = 13.0
    STH['TraceIdentificationCode'][2*int(ntr/3): 3*int(ntr/3)] = 12.0

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

     

    pssegy.writeSegy(filename, Data= trace, dt = 1000, STHin=STH, SHin=SH)


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

        for f in files:
            
            path = transform_separator(os.path.join(root,f))
            
            if (os.path.isfile(path)):
                h = os.path.split(path)

                f = h[1]
                
                file_list.append()
                map_dict[f] = path


    return file_list, map_dict 


def createRcvList(rcvs, initial = 4):

    rcvNames_float = []
    for r in rcvs:

        rfloat = float(str(initial) + r)

        rcvNames_float.append(rfloat)

    return rcvNames_float


def createRcvList3(rcvs, initial = 4):

    rcvNames_float = []
    for r in rcvs:

        rfloat = float(str(initial) + r[:3])

        rcvNames_float.append(rfloat)

    return rcvNames_float

def convert2segy(outfile, filelist, rcvlist, args):

    i = 0

    data = None
    inds = [0] # rcvlist effective

    for filename, rcvname in zip(filelist, rcvlist):


        with open(filename, 'rb') as f:

            traces = parseDataBuffer(f, dsf = args['dsf']) 
            #print(traces.shape) 

        if i == 0:

            data =  traces.copy()

        else:

            ld = data.shape[0]
            lt = traces.shape[0]

            if ld == lt:
            
                data = np.concatenate((data, traces), axis = 1)
                inds.append(i)

           

                



        i +=1




    ## prepare SEGY header
    dt = args['dt']
    ns, ntr = data.shape

    rcvs= np.array(rcvlist)[inds]
    

    SH = pssegy.getDefaultSegyHeader(ntr, ns, dt)
    STH = pssegy.getDefaultSegyTraceHeaders(ntr, ns, dt) 

    STH['TraceIdentificationCode'][0:ntr:3] = 14.0
    STH['TraceIdentificationCode'][1:ntr:3] = 13.0
    STH['TraceIdentificationCode'][2:ntr:3] = 12.0

    STH['Inline3D'][0:int(ntr/3)] = rcvs
    STH['Inline3D'][int(ntr/3): 2*int(ntr/3)] = rcvs
    STH['Inline3D'][2*int(ntr/3): 3*int(ntr/3)] = rcvs


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
    

    STH['YearDataRecorded'] = np.ones((ntr,), dtype = np.float) * 2018.0
    STH['DayOfYear'] = np.ones((ntr,), dtype = np.float) * day_of_year
    STH['HourOfDay'] = np.ones((ntr,), dtype = np.float) * hour
    STH['MinuteOfHour'] = np.ones((ntr,), dtype = np.float) * minute
    STH['SecondOfMinute'] = np.ones((ntr,), dtype = np.float) * second
    

 

    # write SEG-Y file to disk
    segy = pssegy.Segy(data, SH, STH)
    segy.toSegyFile(outfile)
   

    print(outfile, ' written[OK].')


   



def main():

    root = 'E:/浅钻数据20191111'

    outpath = 'E:/SEGY/JLU_1111'

    args = {'header_size': 512,
            'initial':4,
            'rcv_field': 'Inline3D',
            'dsf': 'int32',
            'dt': 1000}


    # read in geophone folders as reciever list

    rcvfolders, rcvfolder_dict = list_subfolders(root)


    # create reciver list in float

    initial = args['initial']

    rcv_list = createRcvList3(rcvfolders, initial = initial)
    
    

    # merge .dat files with same timestamp

   
    
 

    ymd = '20191111'
   

    for h in HH:

        tlist = []

        for m in HH:

            filelist = []
            
            rcvlist = []

            
            timestamp = ymd + '_' + h + m + '00'
            tlist.append(timestamp)

            for rcvfd in rcvfolders:

                rcv = rcvfd[:3]

                fd =  rcvfolder_dict[rcvfd]
                filename =  transform_separator(os.path.join(fd, h, m + 'T.dat'))

                if os.path.exists(filename):

                    filelist.append(filename)
                    rcvlist.append(rcv)
        
            outfile = transform_separator(os.path.join(outpath, timestamp + '.sgy'))

            convert2segy(outfile, filelist, rcvlist, args)

            



            





    



    

    







if __name__ == '__main__':

    main()