# dat2segy
Data format conversion from .dat to SEG-Y format.

This program is desgined for converting the .dat microseismic recording files to standrad SEG-Y revision 1 files.

The .dat file has an 512-byte empty header which needs to be skipped when reading. Trace values are stored in 32-bit integer ('>i4') and order is:
* 513-516 bytes: Y-component value
* 517-520 bytes: X-component value
* 521-524 bytes: Z-component value

All these .dat files are stored in multi-layer structured folders as follows:

-- 060 (Receiver name)
    -- 20190101 (Date)
            -- 01 (Time in hour)
                --01T.dat (Time in minute)

## How to use

1. Run 'main.py' to open a GUI program
2. Run 'batch.py' to do batch conversion without GUI
3. Run 'test.py' to convert an individual .dat file to SEG-Y file.


## License
MIT License.


## Authorship
dat2segy_jl was written in 2019. The sole contributor is Zhengguang Zhao, who now works for DeepListen Pty Ltd on part-time basis.
