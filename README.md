# EventPicker
Microseismic event P- and/or S-wave first arrival time picking package. Written in Python3. 
EventPicker allows users to pick both P-phase and S-phase arrivals manually and picks can be exported to .csv file for further processing.

* eventpicker.py - the mainwindow of EventPicker program
* pssegy.py - A class based on io functions in segypy.py to read and write SEG-Y Rev 1.0 files

## Usage
1. Build and run from source code:
To run this program from source codes, you need to firstly install the following dependencies:
* PyQt5
* Matplotlib
* Numpy
* Pandas
* SegyPy

2. Run this GUI program using the released .exe file on Windows:
Simply download the eventpicker.exe file from the released package and double click the .exe on Windows


## License
LGPL v2.1.

## Authorship
EventPicker was written in 2016. The sole contributor is [Zhengguang Zhao](https://www.researchgate.net/profile/Zhengguang_Zhao2), who now works for DeepListen on part-time basis.