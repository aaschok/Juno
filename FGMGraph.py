import spiceypy as spice
import numpy as np 
import pandas as pd
import os,datetime
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

meta = "juno_2019_v03.tm" #Meta spice kernel to load which loads in all kernels needed to find desired spice data
spice.furnsh(meta)

step = 4000
pollingRate  = 1 #Seconds
polling = 'r' + str(pollingRate) + 's'

utc = ['2017-03-09T00:00:00.000', '2017-03-09T23:59:59.000'] #Time frame to look between

dateRangeTemp = (np.arange(utc[0][:10],np.datetime64(utc[1][:10]) + np.timedelta64(1,'D'),dtype='datetime64'))
dateRangeDay = [spice.et2utc(spice.utc2et(str(x) + 'T00:00:00.000'),'ISOD',3,9) for x in dateRangeTemp] 
beginTimeET = spice.utc2et(utc[0]) #Conversion of time frame from UTC time to Epoch after J2000
endTimeET = spice.utc2et(utc[1])

beginDOY = spice.et2utc(beginTimeET,'ISOD',3,9)
endDOY = spice.et2utc(endTimeET,'ISOD',3,9)

fileDict = {}
dataDict = {} #A dictionary holding the data in each file sorted by date 
for i,filename in enumerate(os.listdir('data\\magnetometer')):
    for date in dateRangeDay:
        if date[:4] in filename and date[5:] in filename and polling in filename and filename.endswith('.csv'):
            fileDict[date] = filename
            dataDict[date] = pd.read_csv(os.path.join('data\\magnetometer', filename))

posTimeData = []
for date,data in dataDict.items():
    xData = np.array(data['BX PLANETOCENTRIC'])
    yData = np.array(data['BY PLANETOCENTRIC'])
    zData = np.array(data['BZ PLANETOCENTRIC'])
    absData = np.sqrt(xData**2+yData**2+zData**2)
    timeData = np.array((data['DECIMAL DAY']-data['DECIMAL DAY'][0])*24)
    posTimeData = np.append(posTimeData,data['SAMPLE UTC'])
    
    maxTime = 6 #Maximum amount of time in hrs to show on a single graph

    n = int(round(timeData[-1]/maxTime))

    sliceIndex = [0]
    for i in range(1,n+1):
     sliceIndex = np.append(sliceIndex,(np.abs(timeData - maxTime*i)).argmin())

    for i in range(1,len(sliceIndex)):
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

print(posTimeData)

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
plt.show()



    










