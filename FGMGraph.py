import spiceypy as spice
import numpy as np 
import pandas as pd
import os,datetime
import tkinter as tk
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class FGMGraph():
    """Class for collecting FGM data from .csv files and plotting in variable time frames with cooresponding position.
        Input('Data folder path','Start time','End time','Meta kernel path','Polling rate of data')"""
    def __init__(self,dataFolder,timeStart,timeEnd,metaKern,pollingRate = None):
        self.dataFolder = dataFolder #The folder which contains all csv data files
        self.timeStart = timeStart
        self.timeEnd = timeEnd
        self.meta = metaKern    #Meta spice kernel to load which loads in all kernels needed to find desired spice data
        self.pollingRate = pollingRate #Rate at which data is recorded in the table, e.g. polling of one second has a data point every second
    
    def Graph(self,timeDomain):
        utc = [self.timeStart, self.timeEnd] #Time frame to look between should be any UTC time string

        spice.furnsh(self.meta)

        if self.pollingRate is None:    pass
        else:   polling = 'r' + str(self.pollingRate) + 's' #Put into the string format in which polling rate is expressed in the file name

        dateRangeTemp = (np.arange(utc[0][:10],np.datetime64(utc[1][:10]) + np.timedelta64(1,'D'),dtype='datetime64'))
        dateRangeDay = [spice.et2utc(spice.utc2et(str(x) + 'T00:00:00.000'),'ISOD',3,9) for x in dateRangeTemp] 

        fileDict = {}
        dataDict = {} #A dictionary holding the data in each file sorted by date 

        if self.pollingRate is None:
            for i,filename in enumerate(os.listdir(dataFolder)):
                for date in dateRangeDay:
                    if date[:4] in filename and date[5:] in filename and filename.endswith('.csv') and 'r1s' not in filename and 'r60s' not in filename:
                        fileDict[date] = filename
                        dataDict[date] = pd.read_csv(os.path.join(dataFolder, filename))
        
        elif self.pollingRate is not None:
            for i,filename in enumerate(os.listdir(dataFolder)):
                for date in dateRangeDay:
                    if date[:4] in filename and date[5:] in filename and filename.endswith('.csv') and polling in filename:
                        fileDict[date] = filename
                        dataDict[date] = pd.read_csv(os.path.join(dataFolder, filename))

        if fileDict == {}:
            print('No files with specified settings')
            return

        posTimeData = []
        for date,data in dataDict.items(): #All data for each day is collected and plotted
            xData = np.array(data['BX PLANETOCENTRIC'])
            yData = np.array(data['BY PLANETOCENTRIC'])
            zData = np.array(data['BZ PLANETOCENTRIC'])
            absData = np.sqrt(xData**2+yData**2+zData**2)
            timeData = np.array((data['DECIMAL DAY']-data['DECIMAL DAY'][0])*24)
            posTimeData = np.append(posTimeData,data['SAMPLE UTC'])
            
            maxTime = timeDomain #Maximum amount of time in hrs to show on a single graph

            n = int(round(timeData[-1]/maxTime))

            sliceIndex = [0]
            for i in range(1,n+1):
                sliceIndex = np.append(sliceIndex,(np.abs(timeData - maxTime*i)).argmin())

            for i in range(1,len(sliceIndex)): #Plotting in 6 hour time windows
                beginIndex = sliceIndex[i-1]
                endIndex = sliceIndex[i]
                fileSaveName = f'fgm-{spice.et2utc(spice.utc2et(str(date) + "T00:00:00.000"),"ISOC",3,11)}_{int(round(timeData[beginIndex]))}-{int(round(timeData[endIndex]))}hrs'
                fig = plt.figure()
                ax  = fig.add_subplot(111)
                ax.set_title(f'Magnetometer data {spice.et2utc(spice.utc2et(str(date) + "T00:00:00.000"),"C",3,13)}')
                ax.set_xlabel('Time(hr)')
                ax.set_ylabel('Magnetic Field(nT)')
                ax.plot(timeData[beginIndex:endIndex],xData[beginIndex:endIndex],label='$B_x$',linewidth=1)
                ax.plot(timeData[beginIndex:endIndex],yData[beginIndex:endIndex],label='$B_y$',linewidth=1)
                ax.plot(timeData[beginIndex:endIndex],zData[beginIndex:endIndex],label='$B_z$',linewidth=1)
                ax.plot(timeData[beginIndex:endIndex],absData[beginIndex:endIndex],'black',label='$^+_-|B|$',linewidth=0.5)
                ax.plot(timeData[beginIndex:endIndex],-absData[beginIndex:endIndex],'black',linewidth=0.5)
                plt.legend()
                plt.savefig(os.path.join('.\\figures', fileSaveName))

        timeDataET = [spice.utc2et(x) for x in posTimeData]

        positions, lightTimes = spice.spkpos('JUNO', timeDataET, 'J2000', 'NONE', 'JUPITER BARYCENTER')
        positions = positions.T/7.1492e7
        spice.unload(meta)

        fig = plt.figure(figsize=(7,7))
        ax  = fig.add_subplot(111, projection='3d')
        ax.set_xlabel('X($R_J)$')
        ax.set_ylabel('Y($R_J)$')
        ax.set_zlabel('Z($R_J)$')
        ax.plot(positions[0], positions[1], positions[2])
        fileSaveName = f'pos_{self.timeStart[:11]}-{self.timeEnd[:11]}'
        plt.savefig(os.path.join('.\\figures', fileSaveName))



if __name__ == '__main__':
    dataFolder = '..\\data\\fgm'
    timeStart = '2019-09-09T00:00:00.000' #Starting time for analyzing data can be in any UTC format
    timeEnd = '2019-09-14T23:59:59.000'
    meta = "juno_2019_v03.tm" 
    pollingRate  = 1 #Seconds can be 1, 60, or None

    timeDomain = 6 #Hours
    analyze = FGMGraph(dataFolder,timeStart,timeEnd,meta,pollingRate)
    analyze.Graph(timeDomain)
    






