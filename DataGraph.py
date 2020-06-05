import numpy as np 
import pandas as pd
import os,datetime,logging,pathlib
import matplotlib.pyplot as plt

logging.basicConfig(filename='DataGraph.log',filemode='w',level=logging.DEBUG)

class JadeLabel():
    def __init__(self,labelFile):
        self.label = labelFile
        self.dataNames = ['DIM0_UTC','PACKET_SPECIES','DATA_UNITS','DATA','DIM1_E'] #All the data names you want to find info on from the .lbl file
        self.dataNameDict = {} #Initialization of a dictionary that will index other dictionaries based on the data name
        self.labelData = self.getLabelData() #Automatically calls the function to get data from the label 

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
                        self.bytesPerRow = line[1]
                        continue
                    elif line[0] in self.dataNames:
                        self.dataNameDict[line[0]] = {'FORMAT':line[1],'NUM_DIMS':line[2],'START_BYTE':byteNum}
                        for i in range(int(line[2])):
                            self.dataNameDict[line[0]]['DIM'+str(i+1)] = line[i+3]
                    if len(line) > 2:
                        byteNum += np.prod([int(i) for i in line[3:]])*byteSizeRef[line[1]]
        return self.dataNameDict 

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

def graphFGM(timeStart,timeEnd,dataFolder):

    doyList, isoList, filePathList = getFiles(timeStart,timeEnd,'.csv',dataFolder,'fgm')

    dateData = []
    xData = []
    yData = []
    zData = []
    timeData = []
    for i,dataFile in enumerate(filePathList):
        if 'r1s' in str(filePathList):
            data = pd.read_csv(dataFile)
            dateData = np.append(dateData,data['SAMPLE UTC'])
            xData = np.append(xData,data['BX PLANETOCENTRIC'])
            yData = np.append(yData,data['BY PLANETOCENTRIC'])
            zData = np.append(zData, data['BZ PLANETOCENTRIC'])
            timeData = np.append(timeData,data['DECIMAL DAY'])
    
    zippedList = zip(dateData,xData,yData,zData,timeData)
    sortedList = sorted(zippedList)
    dateSorted,xSorted,ySorted,zSorted,timeSorted = zip(*sortedList)

    for i,date in enumerate(dateSorted):
        pass


    
    



    
if __name__ == '__main__':
    dataFolder = pathlib.Path('..\\data\\fgm')
    timeStart = '2017-03-09T00:00:00.000' #Starting time for analyzing data can be in any UTC format
    timeEnd = '2017-03-09T23:59:59.000'
    meta = "juno_2019_v03.tm" 

    graphFGM(timeStart,timeEnd,dataFolder)


    testLabel = pathlib.Path('..\\data\\jad\\ION_SPECIES\\JAD_L30_LRS_ION_ANY_CNT_2017068_V02.LBL')
    label = JadeLabel(testLabel)
    print(label.labelData)
    