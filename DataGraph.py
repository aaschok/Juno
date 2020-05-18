import spiceypy as spice
import numpy as np 
import pandas as pd
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

meta = "juno_2019_v03.tm" #Meta spice kernel to load which loads in all kernels specified within
spice.furnsh(meta)

step = 4000

utc = ['2017-02-20T00:00:01.497', '2017-02-20T23:6:00.000'] #Time frame to look between

beginET = spice.utc2et(utc[0]) #Conversion of time frame from UTC time to Epoch after J2000
endET = spice.utc2et(utc[1])

# times = [x*(endET-beginET)/step + beginET for x in range(step)]
# positions, lightTimes = spice.spkpos('JUNO', times, 'J2000', 'NONE', 'JUPITER BARYCENTER')
# positions = positions.T

beginTime = spice.et2utc(beginET,'C',3,25)
endTime = spice.et2utc(endET,'C',3,25)

fileList = []
fileData = {}
sortingDict = {}
tempDict = {}
sortingTime = {}
decDay = {}
for i,filename in enumerate(os.listdir('data\\magnetometer')):
    if filename.endswith(".csv"):
        fileList.append(filename)
        fileData[i] = pd.read_csv(os.path.join('data\\magnetometer', filename))

        sortingTime[i] = [spice.utc2et(x) for x in fileData[i]['SAMPLE UTC'].tolist()]
        decDay[i] = fileData[i]['DECIMAL DAY'].tolist()
        timeBegin = sortingTime[i][0]
        timeEnd = sortingTime[i][-1]
        sortingDict[i] = [timeBegin,timeEnd]
        sortedDict = {k: v for k, v in sorted(sortingDict.items(),key=lambda item:item[1])}

xData = []
yData = []
zData = []
timeData = []
timeday = []
for i in sortedDict.keys():
    timeData = np.append(timeData,sortingTime[i])
    xData = np.append(xData,fileData[i]['BX PLANETOCENTRIC'])
    yData = np.append(yData,fileData[i]['BY PLANETOCENTRIC'])
    zData = np.append(zData,fileData[i]['BZ PLANETOCENTRIC'])

timeData = np.asarray(timeData) 
startIndex = (np.abs(timeData - beginET)).argmin() 
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
ax.plot(timeData,xData,label='$B_x$',linewidth=0.25)
ax.plot(timeData,yData,label='$B_y$',linewidth=0.25)
ax.plot(timeData,zData,label='$B_z$',linewidth=0.25)
ax.plot(timeData,absData,label='$|B|$',linewidth=0.25)
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






