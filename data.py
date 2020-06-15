import numpy as np 
import pandas as pd
import os,datetime,logging,pathlib
import matplotlib.pyplot as plt

class PDS3Label():
    """Class for reading and parsing PDS3 labels, this will only work with labels that contain the comma seperated commant keys "/*RJW,...*/"""
    def __init__(self,labelFile):
        self.label = labelFile
        self.dataNames = ['DIM0_UTC','PACKET_SPECIES','DATA','DIM1_E'] #All the data names you want to find info on from the .lbl file
        self.dataNameDict = {} #Initialization of a dictionary that will index other dictionaries based on the data name
        self.data = self.getLabelData() #Automatically calls the function to get data from the label 

    def getLabelData(self):
        byteSizeRef = {'c':1,'b':1,'B':1,'?':1,'h':2,'H':2,'i':4,'I':4,'l':4,'L':4,'q':8,'Q':8,'f':4,'d':8} #Size of each binary format character in bytes to find the starting byte
        byteNum = 0
        with open(self.label) as f:
            line = f.readline()
            while line != '':
                line = f.readline()
                if line[:6] == '/* RJW':
                    line = line.strip().strip('/* RJW,').strip().split(', ')
                    if line[0] == 'BYTES_PER_RECORD':
                        self.bytesPerRow = int(line[1])
                        continue
                    elif line[0] in self.dataNames:
                        self.dataNameDict[line[0]] = {'FORMAT':line[1],'NUM_DIMS':line[2],'START_BYTE':byteNum}
                        for i in range(int(line[2])):
                            self.dataNameDict[line[0]]['DIM'+str(i+1)] = line[i+3]
                    if len(line) > 2:
                        byteNum += np.prod([int(i) for i in line[3:]])*byteSizeRef[line[1]]
        return self.dataNameDict 
#----------------------------------------------------------------------------------------
def getFiles(startTime, endTime, fileType, dataFolder, instrument):

    if fileType.startswith('.'): pass
    else: fileType = '.' + fileType

    utc = [startTime, endTime] #Time frame to look between should be any UTC time string

    dateRangeISOTemp = np.arange(datetime.datetime.fromisoformat(startTime).date(),(datetime.datetime.fromisoformat(timeEnd)+datetime.timedelta(days=1)).date()).astype(datetime.date) #Range of dates in the datetime.date format
    dateRangeISO = [datetime.date.isoformat(x) for x in dateRangeISOTemp] #Range of dates in string format 'Y-M-D'
    
    dateRangeDOY = []
    for date in dateRangeISOTemp:
        if datetime.date.timetuple(date).tm_yday < 10:
            dateDOY = str(datetime.date.timetuple(date).tm_year)+'00'+str(datetime.date.timetuple(date).tm_yday)
            dateRangeDOY = np.append(dateRangeDOY,dateDOY)

        elif datetime.date.timetuple(date).tm_yday >= 100:
            dateDOY = str(datetime.date.timetuple(date).tm_year)+str(datetime.date.timetuple(date).tm_yday)
            dateRangeDOY = np.append(dateRangeDOY,dateDOY)
        
        elif datetime.date.timetuple(date).tm_yday < 100:
            dateDOY = str(datetime.date.timetuple(date).tm_year)+'0'+str(datetime.date.timetuple(date).tm_yday)
            dateRangeDOY = np.append(dateRangeDOY,dateDOY) #Range of dates in string 'YearDayofyear' format

    filePathList = []
    fileNameList = []

    for (parentDir,childDirs,files) in os.walk(dataFolder):
        for i,fileName in enumerate(files):
            for j,date in enumerate(dateRangeDOY):
                if fileName.endswith(fileType) and date in fileName and fileName not in fileNameList and fileName[:len(instrument)] == instrument:
                    fileNameList = np.append(fileNameList,fileName)
                    filePathList = np.append(filePathList,os.path.join(dataFolder, fileName))                    
    return dateRangeDOY, dateRangeISO, filePathList
#--------------------------------------------------------------------------------
class JadeData():
    def __init__(self,dataFile,startTime,endTime):
        self.dataFile = dataFile
        self.startTime = startTime
        self.endTime = endTime
        self.dataDict = {}
        self.dataAvg = []

    def test(self):
        labelPath = self.dataFile.rstrip('.DAT') + '.lbl'
        label = PDS3Label(labelPath)

        rows = 8640

        with open(self.dataFile, 'rb') as f:
            for _ in range(rows):
                data = f.read(label.bytesPerRow)
                
                for key,value in label.dataNameDict.items():
                    



    def getData(self):
        with open(self.dataFile, "rb") as f:
            species = 3
            rows = 8640
            data = f.read(259872)
            for i in range(rows):
                
                byteStart = 66-1
                byteEnd = byteStart+1
                dataSlice = data[byteStart:byteEnd]
                ionSpecies = struct.unpack('b',dataSlice)[0]
                                
                if ionSpecies == species:

                    byteStart = 1-1
                    byteEnd = byteStart+21
                    timeStamp = str(data[byteStart:byteEnd],'ascii')                                    
                    
                    byteEnd = 289 - 1
                    countSecMatrix = []
                    temp = []
                    for i in range(1,65):
                        byteStart = byteEnd
                        byteEnd = byteStart + 4*78
                        dataSlice = data[byteStart:byteEnd]
                        countsSec = struct.unpack('f'*78,dataSlice)
                        countSecMatrix.append(countsSec)
                        temp.append(np.mean(countsSec))
                    self.dataAvg.append(temp)



                    byteEnd = 80161 - 1
                    energyMatrix = []
                    for i in range(1,65):
                        byteStart = byteEnd
                        byteEnd = byteStart + 4*78
                        dataSlice = data[byteStart:byteEnd]
                        energy = struct.unpack('f'*78,dataSlice)
                        energyMatrix.append(energy)
                self.dataDict[timeStamp] = {'DATA':countSecMatrix,'DIM1':energyMatrix,'DIM2':None}
                data = f.read(259872)
            
            f.close()

if __name__ == '__main__':

    dataFolder = os.path.join('..','data','jad','JNO-J_SW-JAD-3-CALIBRATED-V1.0','ION_SPECIES','JAD_L30_LRS_ION_ANY_CNT_2017068_V02.DAT')
    #RJW, Name, Format, dimnum, size dim 1, size dim 2,...
    timeStart = 
    timeEnd = 2

    jade = JadeData(dataFolder,timeStart,timeEnd)
    jade.test() 
