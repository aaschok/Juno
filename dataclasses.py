import numpy as np 
import pandas as pd
import os,datetime,logging,pathlib,struct
import matplotlib.pyplot as plt

logging.basicConfig(filename='dataclasses.log',filemode='w',level=logging.DEBUG)
logging.disable(logging.DEBUG)

def getFiles(startTime, endTime, fileType, dataFolder, instrument):
    """Function whitch finds all files that have your specified parameters in their name.\n
        Start time must be in UTC e.g. '2017-03-09T00:00:00.000'.\n
        End time must be in UTC e.g. '2017-03-09T00:00:00.000'.\n
        Filetype must be string preceding period is optional.\n
        Datafolder must be the highest directory in which your files will be.\n
        Instrument must be string containing any identifiable strings to differentiat the files you want from those you dont. e.g. 'JAD_L30_LRS_ION'\n
        Returns a list of dates in the range in Day of year format, ISO format and a list of file paths.
        """
    if fileType.startswith('.'): pass #Ensure there is a preceding period on the file extension
    else: fileType = '.' + fileType

    utc = [startTime, endTime] #Time frame to look between should be any UTC time string

    dateRangeISOTemp = np.arange(datetime.datetime.fromisoformat(startTime).date(),(datetime.datetime.fromisoformat(endTime)+datetime.timedelta(days=1)).date()).astype(datetime.date) #Range of dates in the datetime.date format
    dateRangeISO = [datetime.date.isoformat(x) for x in dateRangeISOTemp] #Range of dates in string format 'Y-M-D'
    
    dateRangeDOY = [] #Range of dates in string 'YearDayofyear' format
    for date in dateRangeISOTemp: #Creates an array of all days between the two specified times in Y-DOY format
        if datetime.date.timetuple(date).tm_yday < 10: #Datetime does not return day of year with preceding zeros if necessary so they must be added here
            dateDOY = str(datetime.date.timetuple(date).tm_year)+'00'+str(datetime.date.timetuple(date).tm_yday)
            dateRangeDOY = np.append(dateRangeDOY,dateDOY)

        elif datetime.date.timetuple(date).tm_yday >= 100:
            dateDOY = str(datetime.date.timetuple(date).tm_year)+str(datetime.date.timetuple(date).tm_yday)
            dateRangeDOY = np.append(dateRangeDOY,dateDOY)
        
        elif datetime.date.timetuple(date).tm_yday < 100:
            dateDOY = str(datetime.date.timetuple(date).tm_year)+'0'+str(datetime.date.timetuple(date).tm_yday)
            dateRangeDOY = np.append(dateRangeDOY,dateDOY) 

    filePathList = []
    fileNameList = []
    for (parentDir,childDirs,files) in os.walk(dataFolder): #Using os.walk each directory within the given data directory is combed through searching for files that match the criteria
        for i,fileName in enumerate(files):
            for j,date in enumerate(dateRangeDOY):
                if fileName.endswith(fileType) and date in fileName and fileName not in fileNameList and fileName[:len(instrument)] == instrument:
                    fileNameList = np.append(fileNameList,fileName) #List of all filenames is created to cheack and ensure the same file is not selected twice
                    filePathList = np.append(filePathList,os.path.join(parentDir, fileName))    #The path to the correct file is saved in a list                    
    return dateRangeDOY, dateRangeISO, filePathList #The range of dates in DOY and ISO formats as well as the file paths list is returned
#-------------------------------------------------------------------------------------------------------------------------------------------------
class PDS3Label(): 
    """Class for reading and parsing PDS3 labels, this will only work with labels that contain the comma seperated comment keys. e.g. /*RJW, Name, Format, dimnum, size dim 1, size dim 2,...*/\n
    returns a dictionary """
    def __init__(self,labelFile):
        self.label = labelFile
        self.dataNames = ['DIM0_UTC','PACKET_SPECIES','DATA'] #All the object names you want to find info on from the .lbl file
        self.dataNameDict = {} #Initialization of a dictionary that will index other dictionaries based on the data name
        self.getLabelData() #Automatically calls the function to get data from the label 
        

    def getLabelData(self):
        byteSizeRef = {'c':1,'b':1,'B':1,'?':1,'h':2,'H':2,'i':4,'I':4,'l':4,'L':4,'q':8,'Q':8,'f':4,'d':8} #Size of each binary format character in bytes to help find starting byte
        byteNum = 0
        with open(self.label) as f:
            line = f.readline()
            while line != '':   #Each line is read through in the label
                line = f.readline()
                if line[:6] == '/* RJW':    #If a comment key is found parsing it begins
                    line = line.strip().strip('/* RJW,').strip().split(', ')    #The key is split up into a list removing the RJW
                    if line[0] == 'BYTES_PER_RECORD':
                        self.bytesPerRow = int(line[1])
                        continue
                    if len(line) > 2:
                        if line[0] in self.dataNames:   #If the line read is a comment key for one of the objects defined above the data will be put into a dictionary
                            self.dataNameDict[line[0]] = {'FORMAT':line[1],'NUM_DIMS':line[2],'START_BYTE':byteNum}
                            for i in range(int(line[2])):
                                self.dataNameDict[line[0]]['DIM'+str(i+1)] = int(line[i+3])
                        byteNum += np.prod([int(i) for i in line[3:]])*byteSizeRef[line[1]] #Using the above dictionary the total size of the object is found to find the ending byte
                        if line[0] in self.dataNames:
                            self.dataNameDict[line[0]]['END_BYTE'] = byteNum
                    
        return self.dataNameDict #The dictionary is returned
#-------------------------------------------------------------------------------------------------------------------------------------------------
class JadeData():
    """Class for reading and getting data from a single .dat file jade provides.\n
    Datafile must be a single .dat file.\n
    Start time must be in UTC e.g. '2017-03-09T00:00:00.000'.\n
    End time must be in UTC e.g. '2017-03-09T00:00:00.000'.\n
    """
    def __init__(self,dataFile,startTime,endTime):
        self.dataFileList = dataFile
        self.startTime = datetime.datetime.fromisoformat(startTime)
        self.endTime = datetime.datetime.fromisoformat(endTime)
        self.dataDict = {}
        self.getData() #Automatically gets the data from the file
        

    def getData(self):
        for dataFile in self.dataFileList:
            labelPath = dataFile.rstrip('.DAT') + '.lbl'    #All .dat files should come with an accompanying .lbl file
            label = PDS3Label(labelPath)    #The label file is parsed for the data needed
            logging.debug(label.dataNameDict)
            rows = 8640
            species = 3

            with open(dataFile, 'rb') as f:
                for _ in range(rows):
                    data = f.read(label.bytesPerRow)
                    
                    timeData = label.dataNameDict['DIM0_UTC']
                    startByte = timeData['START_BYTE']
                    endByte = timeData['END_BYTE']
                    dataSlice = data[startByte:endByte]
                    dateTimeStamp = datetime.datetime.strptime(str(dataSlice,'ascii'),'%Y-%jT%H:%M:%S.%f')
                    dateStamp = str(dateTimeStamp.date())
                    time = dateTimeStamp.time()
                    timeStamp = time.hour + time.minute/60 + time.second/3600

                    if dateStamp in self.dataDict:
                        pass
                    else:
                        self.dataDict[dateStamp] = {}
                        
                    if dateTimeStamp > self.endTime:
                            return self.dataDict

                    speciesObjectData = label.dataNameDict['PACKET_SPECIES']
                    startByte = speciesObjectData['START_BYTE']
                    endByte = speciesObjectData['END_BYTE']
                    dataSlice = data[startByte:endByte]
                    ionSpecies = struct.unpack(speciesObjectData['FORMAT'],dataSlice)[0]

                    if ionSpecies == species:
                        
                        if 'TIME_ARRAY' not in self.dataDict[dateStamp]:
                            self.dataDict[dateStamp]['TIME_ARRAY'] = []
                        self.dataDict[dateStamp]['TIME_ARRAY'].append(timeStamp)
                            


                        dataObjectData = label.dataNameDict['DATA']
                        startByte = dataObjectData['START_BYTE']
                        endByte = dataObjectData['END_BYTE']
                        dataSlice = data[startByte:endByte]
                        temp = struct.unpack(dataObjectData['FORMAT']*dataObjectData['DIM1']*dataObjectData['DIM2'],dataSlice)
                        temp = np.asarray(temp).reshape(dataObjectData['DIM1'],dataObjectData['DIM2'])
                        dataArray = [np.mean(row) for row in temp]

                        if 'DATA_ARRAY' not in self.dataDict[dateStamp]:
                            self.dataDict[dateStamp]['DATA_ARRAY'] = []
                        
                        self.dataDict[dateStamp]['DATA_ARRAY'].append(np.log(dataArray))
            f.close()
                    
class FGMData():
    def __init__(self,dataFile,startTime,endTime):
        self.dataFileList = dataFile
        self.startTime = datetime.datetime.fromisoformat(startTime)
        self.endTime = datetime.datetime.fromisoformat(endTime)
        self.dataDict = {}
        self.getData()

    def getData(self):
        
        for dataFile in self.dataFileList:
            data = pd.read_csv(dataFile)
            dateTimeStamp = data['SAMPLE UTC']
            
            
            closestStart = min(dateTimeStamp, key=lambda x: abs(datetime.datetime.fromisoformat(x) - self.startTime))
            closestEnd = min(dateTimeStamp, key=lambda x: abs(datetime.datetime.fromisoformat(x) - self.endTime))
            
            if closestStart == 0 and closestEnd == len(dateTimeStamp):  
                dateTimeStamp = dateTimeStamp[closestStart:closestEnd]
                magXData = data['BX PLANETOCENTRIC'][closestStart:closestEnd+1]
                magYData = data['BY PLANETOCENTRIC'][closestStart:closestEnd+1]
                magZData = data['BZ PLANETOCENTRIC'][closestStart:closestEnd+1]
            else:
                magXData = data['BX PLANETOCENTRIC']
                magYData = data['BY PLANETOCENTRIC']
                magZData = data['BZ PLANETOCENTRIC']

            for stamp in dateTimeStamp:
                date = str(datetime.datetime.fromisoformat(stamp).date())

                time = datetime.datetime.fromisoformat(stamp).time()
                time = time.hour + time.minute/60 + time.second/3600


                if date not in self.dataDict:
                    self.dataDict[date] = {'TIME_ARRAY':[]}
                self.dataDict[date]['TIME_ARRAY'].append(time)
            self.dataDict[date]['BX'] = magXData
            self.dataDict[date]['BY'] = magYData
            self.dataDict[date]['BZ'] = magZData
            self.dataDict[date]['B'] = np.sqrt(magXData**2+magYData**2+magZData**2)
        
        
if __name__ == '__main__':
    
    timeStart = '2017-03-09T00:00:00.000'
    timeEnd = '2017-03-09T23:59:59.000'

    dataFolder = os.path.join('..','data','jad')
    DOY,ISO,datFiles = getFiles(timeStart,timeEnd,'.DAT',dataFolder,'JAD_L30_LRS_ION') 

    jade = JadeData(datFiles,timeStart,timeEnd)

    dataFolder = os.path.join('..','data','fgm')
    DOY,ISO,csvFiles = getFiles(timeStart,timeEnd,'.csv',dataFolder,'fgm_jno_l3') 
    
    fgm = FGMData(csvFiles,timeStart,timeEnd)

    for date in jade.dataDict.keys():
        
        jadeData = jade.dataDict[date]      
        fgmData = fgm.dataDict[date]
        
        fgmStart = 0
        jadStart = 0
        for i in range(1,5):
            jadIndex = min(range(len(jadeData['TIME_ARRAY'])), key=lambda j: abs(jadeData['TIME_ARRAY'][j]-i*6))+1
            fgmIndex = min(range(len(fgmData['TIME_ARRAY'])), key=lambda j: abs(fgmData['TIME_ARRAY'][j]-i*6))+1

            fig, (ax1,ax2) = plt.subplots(2,1,sharex=True,figsize=(9,4))
            pcm = ax1.imshow(np.transpose(jadeData['DATA_ARRAY'][jadStart:jadIndex])>0,origin='lower',aspect='auto',cmap='plasma',extent=((i-1)*6,i*6,0,64))


            ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex],fgmData['BX'][fgmStart:fgmIndex],label='$B_x$',linewidth=1)
            ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex],fgmData['BY'][fgmStart:fgmIndex],label='$B_y$',linewidth=1)
            ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex],fgmData['BZ'][fgmStart:fgmIndex],label='$B_z$',linewidth=1)
            ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex],fgmData['B'][fgmStart:fgmIndex],'black',label='$^+_-|B|$',linewidth=0.5)
            ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex],-fgmData['B'][fgmStart:fgmIndex],'black',linewidth=0.5)
            ax2.legend(loc=(1.01,0.1))

            fgmStart = fgmIndex
            jadStart = jadIndex

            

    
    plt.show()
        