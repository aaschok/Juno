import spiceypy as spice
import numpy as np 
import pandas as pd
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

meta = "juno_2019_v03.tm" #Meta spice kernel to load which loads in all kernels specified within
spice.furnsh(meta)

step = 4000

utc = ['2017-03-09T00:00:00.000', '2017-03-09T23:59:59.000'] #Time frame to look between

beginET = spice.utc2et(utc[0]) #Conversion of time frame from UTC time to Epoch after J2000
endET = spice.utc2et(utc[1])

beginTime = spice.et2utc(beginET,'C',3,25)
endTime = spice.et2utc(endET,'C',3,25)

fileData = {}
sortingDict = {}
tempDict = {}
sortingTime = {}
for i,filename in enumerate(os.listdir('data\\magnetometer')):
    if filename.endswith(".csv"):
        fileData[i] = pd.read_csv(os.path.join('data\\magnetometer', filename))

        sortingTime[i] = [spice.utc2et(x) for x in fileData[i]['SAMPLE UTC'].tolist()]
        timeBegin = sortingTime[i][0]
        timeEnd = sortingTime[i][-1]
        sortingDict[i] = [timeBegin,timeEnd]
        sortedDict = {k: v for k, v in sorted(sortingDict.items(),key=lambda item:item[1])}

xData = []
yData = []
zData = []
timeData = []

for i,data in sortedDict.items():
    timeData = np.append(timeData,sortingTime[i])
    xData = np.append(xData,fileData[i]['BX PLANETOCENTRIC'])
    yData = np.append(yData,fileData[i]['BY PLANETOCENTRIC'])
    zData = np.append(zData,fileData[i]['BZ PLANETOCENTRIC'])

timeData = np.asarray(timeData) 
startIndex = (np.abs(timeData - beginET)).argmin() #Arguments for finding closest time in the data pool to that specified in the beginning
endIndex = (np.abs(timeData - endET)).argmin() 

timeData = timeData[startIndex:endIndex]
xData = xData[startIndex:endIndex]
yData = yData[startIndex:endIndex]
zData = zData[startIndex:endIndex]
absData = np.sqrt(xData**2+yData**2+zData**2)



time0 = timeData[0]
timef = timeData[-1]
time0UTC = spice.et2utc(time0,'C',3,20)
timefUTC = spice.et2utc(timef,'C',3,20)
timeData = (timeData - time0)/(3600)

fig = plt.figure()
ax  = fig.add_subplot(111)
ax.set_title(f'Magnetometer data  {time0UTC} to {timefUTC}')
ax.set_xlabel('Time(hr)')
ax.set_ylabel('Magnetic Field(nT)')
ax.set_ylim(-15,15)
ax.plot(timeData,xData,label='$B_x$',linewidth=0.5)
ax.plot(timeData,yData,label='$B_y$',linewidth=0.5)
ax.plot(timeData,zData,label='$B_z$',linewidth=0.5)
ax.plot(timeData,absData,'black',linewidth=0.25)
ax.plot(timeData,-absData,'black',label='$^+_-|B|$',linewidth=0.25)
plt.legend()
plt.show()


n = int(round(timeData[-1]/6))

sliceIndex = [0]
for i in range(1,n+1):
 sliceIndex = np.append(sliceIndex,(np.abs(timeData - 6*i)).argmin())

for i in range(1,len(sliceIndex)):
    beginIndex = sliceIndex[i-1]
    endIndex = sliceIndex[i]
    fig = plt.figure()
    ax  = fig.add_subplot(111)
    ax.set_title(f'Magnetometer data  {time0UTC} to {timefUTC}')
    ax.set_xlabel('Time(hr)')
    ax.set_ylabel('Magnetic Field(nT)')
    ax.plot(timeData[beginIndex:endIndex],xData[beginIndex:endIndex],label='$B_x$',linewidth=0.5)
    ax.plot(timeData[beginIndex:endIndex],yData[beginIndex:endIndex],label='$B_y$',linewidth=0.5)
    ax.plot(timeData[beginIndex:endIndex],zData[beginIndex:endIndex],label='$B_z$',linewidth=0.5)
    ax.plot(timeData[beginIndex:endIndex],absData[beginIndex:endIndex],'black',label='$^+_-|B|$',linewidth=0.25)
    ax.plot(timeData[beginIndex:endIndex],-absData[beginIndex:endIndex],'black',linewidth=0.25)
    plt.legend()
    plt.show()

positions, lightTimes = spice.spkpos('JUNO', timeData, 'J2000', 'NONE', 'JUPITER BARYCENTER')
positions = positions.T

fig = plt.figure(figsize=(7,7))
ax  = fig.add_subplot(111, projection='3d')
ax.plot(positions[0], positions[1], positions[2])
plt.title(f'Juno Position from {beginTime} to {endTime}')
plt.show()

spice.unload(meta)






