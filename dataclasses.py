import numpy as np 
import pandas as pd
import os,datetime,logging,pathlib,struct
import matplotlib.pyplot as plt
import spiceypy as spice


# logging.basicConfig(filename=pathlib.Path('..\\logs\\datagraph.log'),filemode='w',level=logging.DEBUG) #Creates a log file to show any outputs uncomment to use


def getFiles(startTime, endTime, fileType, dataFolder, instrument):
    """Function which finds all files that have your specified parameters in their name.\n
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
    for date in dateRangeISOTemp: 
            dateDOY = date.strftime('%Y%j')
            dateRangeDOY = np.append(dateRangeDOY,dateDOY)   
    dateRangeDOY = np.sort(dateRangeDOY)  

    filePathList = []
    fileNameList = []
    for (parentDir,childDirs,files) in os.walk(dataFolder): #Using os.walk each directory within the given data directory is combed through searching for files that match the criteria
        for i,fileName in enumerate(files):
            for j,date in enumerate(dateRangeDOY):
                if fileName.endswith(fileType) and date in fileName and fileName not in fileNameList and fileName[:len(instrument)] == instrument:
                    fileNameList = np.append(fileNameList,fileName) #List of all filenames is created to cheack and ensure the same file is not selected twice
                    filePathList = np.append(filePathList,os.path.join(parentDir, fileName))    #The path to the correct file is saved in a list 

    temp = []
    for i,j in enumerate(dateRangeDOY):
        for k in filePathList:
            if j in k:
                temp = np.append(temp,k)
    filePathList = temp

    return dateRangeDOY, dateRangeISO, filePathList #The range of dates in DOY and ISO formats as well as the file paths list is returned
#-------------------------------------------------------------------------------------------------------------------------------------------------
class PDS3Label(): 
    """Class for reading and parsing PDS3 labels, this will only work with labels that contain the comma seperated comment keys. e.g. /*RJW, Name, Format, dimnum, size dim 1, size dim 2,...*/\n
    returns a dictionary """
    def __init__(self,labelFile):
        self.label = labelFile
        self.dataNames = ['DIM0_UTC','PACKET_SPECIES','DATA','DIM1_E','SC_POS_LAT','SC_POS_R'] #All the object names you want to find info on from the .lbl file
        self.dataNameDict = {} #Initialization of a dictionary that will index other dictionaries based on the data name
        self.getLabelData() #Automatically calls the function to get data from the label 
        

    def getLabelData(self):
        byteSizeRef = {'c':1,'b':1,'B':1,'?':1,'h':2,'H':2,'i':4,'I':4,'l':4,'L':4,'q':8,'Q':8,'f':4,'d':8} #Size of each binary format character in bytes to help find starting byte
        byteNum = 0
        with open(self.label) as f:
            line = f.readline()
            while line != '':   #Each line is read through in the label
                line = f.readline()
                if 'FILE_RECORDS' in line:
                    self.rows = int(line[12:].strip().lstrip('=').strip())
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
    """Class for reading and getting data from a list of .dat file from the get files function provides.\n
    Datafile must be a single .dat file.\n
    Start time must be in UTC e.g. '2017-03-09T00:00:00.000'.\n
    End time must be in UTC e.g. '2017-03-09T00:00:00.000'.\n
    """
    def __init__(self,dataFile,startTime,endTime):
        self.dataFileList = dataFile
        self.startTime = datetime.datetime.fromisoformat(startTime) #Converted to datetime.datetime object for easier date manipulation
        self.endTime = datetime.datetime.fromisoformat(endTime)
        self.dataDict = {}
        

    def getIonData(self):
        for dataFile in self.dataFileList:
            labelPath = dataFile.rstrip('.DAT') + '.LBL'    #All .dat files should come with an accompanying .lbl file
            label = PDS3Label(labelPath)    #The label file is parsed for the data needed
            logging.debug(label.dataNameDict)
            rows = label.rows #All LRS jade data has 8640 rows of data per file
            species = 3 #The ion species interested in as defined in the label
            with open(dataFile, 'rb') as f:
                for _ in range(rows):
                    data = f.read(label.bytesPerRow)    
                    
                    timeData = label.dataNameDict['DIM0_UTC']   #Label data for the time stamp
                    startByte = timeData['START_BYTE']  #Byte where the time stamp starts
                    endByte = timeData['END_BYTE']  #Byte where the time stamp ends
                    dataSlice = data[startByte:endByte] #The slice of data that contains the time stamp
                    dateTimeStamp = datetime.datetime.strptime(str(dataSlice,'ascii'),'%Y-%jT%H:%M:%S.%f')  #The time stamp is converted from DOY format to a datetime object
                    dateStamp = str(dateTimeStamp.date())   #A string of the day date to be used as the main organizational key in the data dictionary
                    time = dateTimeStamp.time() #The time in hours to microseconds for the row
                    timeStamp = time.hour + time.minute/60 + time.second/3600   #Convert the time to decimal hours

                    if dateStamp in self.dataDict:  #Check if a entry for the date already exists in the data dictionary
                        pass
                    else:
                        self.dataDict[dateStamp] = {}
                        
                    if dateTimeStamp > self.endTime:    #If the desired end date has been passed the function ends
                            f.close()   
                            return 

                    speciesObjectData = label.dataNameDict['PACKET_SPECIES']    #The species data from teh label is pulled
                    startByte = speciesObjectData['START_BYTE']
                    endByte = speciesObjectData['END_BYTE']
                    dataSlice = data[startByte:endByte]
                    ionSpecies = struct.unpack(speciesObjectData['FORMAT']*speciesObjectData['DIM1'],dataSlice)[0] #Species type for the row is found

                    dataObjectData = label.dataNameDict['DIM1_E'] #Label data for the data is found 
                    startByte = dataObjectData['START_BYTE']
                    endByte = dataObjectData['END_BYTE']
                    dataSlice = data[startByte:endByte] #Slice containing the data for that row is gotten
                    temp = struct.unpack(dataObjectData['FORMAT']*dataObjectData['DIM1']*dataObjectData['DIM2'],dataSlice) #The binary format of the data is multiplied by the dimensions to allow unpacking of all data at once
                    temp = np.asarray(temp).reshape(dataObjectData['DIM1'],dataObjectData['DIM2'])  #The data is put into a matrix of the size defined in the label
                    dataArray = [row[0] for row in temp]  #Each rows average is found to have one column 

                    if 'DIM1_ARRAY' not in self.dataDict[dateStamp]:
                        self.dataDict[dateStamp]['DIM1_ARRAY'] = dataArray

                    if ionSpecies == species:   #If the species for the row is the desired species continue finding data
                        
                        if 'TIME_ARRAY' not in self.dataDict[dateStamp]:
                            self.dataDict[dateStamp]['TIME_ARRAY'] = []
                        self.dataDict[dateStamp]['TIME_ARRAY'].append(timeStamp)   #Array to hold time stamps is created and the decimal hour time is appended to it

                        if 'DATETIME_ARRAY' not in self.dataDict[dateStamp]:
                            self.dataDict[dateStamp]['DATETIME_ARRAY'] = []
                        self.dataDict[dateStamp]['DATETIME_ARRAY'].append(str(dateTimeStamp))   #Array to hold time stamps is created and the decimal hour time is appended to it
                            
                        dataObjectData = label.dataNameDict['DATA'] #Label data for the data is found 
                        startByte = dataObjectData['START_BYTE']
                        endByte = dataObjectData['END_BYTE']
                        dataSlice = data[startByte:endByte] #Slice containing the data for that row is gotten
                        temp = struct.unpack(dataObjectData['FORMAT']*dataObjectData['DIM1']*dataObjectData['DIM2'],dataSlice) #The binary format of the data is multiplied by the dimensions to allow unpacking of all data at once
                        temp = np.asarray(temp).reshape(dataObjectData['DIM1'],dataObjectData['DIM2'])  #The data is put into a matrix of the size defined in the label
                        dataArray = [np.mean(row) for row in temp]  #Each rows average is found to have one column 

                        if 'DATA_ARRAY' not in self.dataDict[dateStamp]:
                            self.dataDict[dateStamp]['DATA_ARRAY'] = []
                        
                        self.dataDict[dateStamp]['DATA_ARRAY'].append(np.log(dataArray)) #The log of the data column is taken and appended to the data dictionary under the key DATA_ARRAY

                        latObjectData = label.dataNameDict['SC_POS_LAT'] #Label data for the data is found 
                        startByte = latObjectData['START_BYTE']
                        endByte = latObjectData['END_BYTE']
                        dataSlice = data[startByte:endByte] #Slice containing the data for that row is gotten
                        latArray = struct.unpack(latObjectData['FORMAT']*latObjectData['DIM1'],dataSlice)[0] #The binary format of the data is multiplied by the dimensions to allow unpacking of all data at once

            f.close()

    def getElecData(self):
        for dataFile in self.dataFileList:
            labelPath = dataFile.rstrip('.DAT') + '.LBL'    #All .dat files should come with an accompanying .lbl file
            label = PDS3Label(labelPath)    #The label file is parsed for the data needed
            logging.debug(label.dataNameDict)
            rows = label.rows #All LRS jade data has 8640 rows of data per file
            with open(dataFile, 'rb') as f:
                for _ in range(rows):
                    data = f.read(label.bytesPerRow)    
                    
                    timeData = label.dataNameDict['DIM0_UTC']   #Label data for the time stamp
                    startByte = timeData['START_BYTE']  #Byte where the time stamp starts
                    endByte = timeData['END_BYTE']  #Byte where the time stamp ends
                    dataSlice = data[startByte:endByte] #The slice of data that contains the time stamp
                    dateTimeStamp = datetime.datetime.strptime(str(dataSlice,'ascii'),'%Y-%jT%H:%M:%S.%f')  #The time stamp is converted from DOY format to a datetime object
                    dateStamp = str(dateTimeStamp.date())   #A string of the day date to be used as the main organizational key in the data dictionary
                    time = dateTimeStamp.time() #The time in hours to microseconds for the row
                    timeStamp = time.hour + time.minute/60 + time.second/3600   #Convert the time to decimal hours

                    if dateStamp in self.dataDict:  #Check if a entry for the date already exists in the data dictionary
                        pass
                    else:
                        self.dataDict[dateStamp] = {}
                        
                    if dateTimeStamp > self.endTime:    #If the desired end date has been passed the function ends
                            f.close()   
                            return 
                    
                    if 'TIME_ARRAY' not in self.dataDict[dateStamp]:
                            self.dataDict[dateStamp]['TIME_ARRAY'] = []
                    self.dataDict[dateStamp]['TIME_ARRAY'].append(timeStamp)   #Array to hold time stamps is created and the decimal hour time is appended to it

                    if 'DATETIME_ARRAY' not in self.dataDict[dateStamp]:
                        self.dataDict[dateStamp]['DATETIME_ARRAY'] = []
                    self.dataDict[dateStamp]['DATETIME_ARRAY'].append(str(dateTimeStamp))   #Array to hold time stamps is created and the decimal hour time is appended to it
                            
                    dataObjectData = label.dataNameDict['DATA'] #Label data for the data is found 
                    startByte = dataObjectData['START_BYTE']
                    endByte = dataObjectData['END_BYTE']
                    dataSlice = data[startByte:endByte] #Slice containing the data for that row is gotten
                    temp = struct.unpack(dataObjectData['FORMAT']*dataObjectData['DIM1']*dataObjectData['DIM2'],dataSlice) #The binary format of the data is multiplied by the dimensions to allow unpacking of all data at once
                    temp = np.asarray(temp).reshape(dataObjectData['DIM1'],dataObjectData['DIM2'])  #The data is put into a matrix of the size defined in the label
                    dataArray = [np.mean(row) for row in temp]  #Each rows average is found to have one column 

                    if 'DATA_ARRAY' not in self.dataDict[dateStamp]:
                        self.dataDict[dateStamp]['DATA_ARRAY'] = []
                    
                    dataObjectData = label.dataNameDict['DIM1_E'] #Label data for the data is found 
                    startByte = dataObjectData['START_BYTE']
                    endByte = dataObjectData['END_BYTE']
                    dataSlice = data[startByte:endByte] #Slice containing the data for that row is gotten
                    temp = struct.unpack(dataObjectData['FORMAT']*dataObjectData['DIM1']*dataObjectData['DIM2'],dataSlice) #The binary format of the data is multiplied by the dimensions to allow unpacking of all data at once
                    temp = np.asarray(temp).reshape(dataObjectData['DIM1'],dataObjectData['DIM2'])  #The data is put into a matrix of the size defined in the label
                    dataArray = [row[0] for row in temp]  #Each rows average is found to have one column 


                    if 'DIM1_ARRAY' not in self.dataDict[dateStamp]:
                        self.dataDict[dateStamp]['DIM1_ARRAY'] = dataArray

                    

#-------------------------------------------------------------------------------------------------------------------------------------------------     
class FGMData():
    """A class for reading singular csv files and getting data for Bx, By, and Bz.\n
    Datafile must be a list of .csv files from the getFies unc.\n
    Start time must be in UTC e.g. '2017-03-09T00:00:00.000'.\n
    End time must be in UTC e.g. '2017-03-09T00:00:00.000'.
    """
    def __init__(self,dataFile,startTime,endTime):
        self.dataFileList = dataFile
        self.startTime = datetime.datetime.fromisoformat(startTime) #Converted to datetime.datetime object for easier date manipulation
        self.endTime = datetime.datetime.fromisoformat(endTime)
        self.dataDict = {}
        self.getMagData() #Automatically gets the data from the file

    def getMagData(self):
        
        for dataFile in self.dataFileList:
            data = pd.read_csv(dataFile)    #Using pandas module the csv is read
            
            dateTimeStamp = data['SAMPLE UTC']
                
            for row,stamp in enumerate(dateTimeStamp): #For each time stamp the day date is found and decimal hour is found
                
                dateTimeStamp = datetime.datetime.fromisoformat(stamp)
                date = str(dateTimeStamp.date())
                time = datetime.datetime.fromisoformat(stamp).time()
                time = time.hour + time.minute/60 + time.second/3600

                magXData = data['BX PLANETOCENTRIC'][row]
                magYData = data['BY PLANETOCENTRIC'][row]
                magZData = data['BZ PLANETOCENTRIC'][row]
                magTot = np.sqrt(magXData**2+magYData**2+magZData**2)
                
                if date not in self.dataDict:   #If a key entry for the day doesnt exist one is created
                    self.dataDict[date] = {'DATETIME_ARRAY':[],'TIME_ARRAY':[], 'BX':[], 'BY':[], 'BZ':[], 'B':[]}

                self.dataDict[date]['DATETIME_ARRAY'].append(dateTimeStamp)
                self.dataDict[date]['TIME_ARRAY'].append(time)  #Time stamp for each time in the day is added to the array
                self.dataDict[date]['BX'].append(magXData)    #Full Bx data array is added to the dictionary
                self.dataDict[date]['BY'].append(magYData)    #Full By data array is added to the dictionary
                self.dataDict[date]['BZ'].append(magZData)    #Full Bz data array is added to the dictionary
                self.dataDict[date]['B'].append(magTot) #Full B data array is added to the dictionary
            
#-------------------------------------------------------------------------------------------------------------------------------------------------        
class SpiceData():

    def __init__(self,metaKernel,time):
        self.meta = metaKernel
        self.time = time
        self.position = None
        self.distance = None
        self.latitude = None
        self.longitude = None

    def positionData(self):
        spice.furnsh(self.meta) #loads the meta kernel that will load all kernels needed

        time = spice.utc2et(self.time)

        self.position, lighttime = spice.spkpos('JUNO',time,'IAU_JUPITER','NONE','JUPITER') #Finds the position in cartesian coords relative to jupiter
    
        pos = spice.vpack(self.position[0],self.position[1],self.position[2])   #Packs the position into a vector
        self.distance,self.longitude,self.latitude = spice.reclat(pos) #Finds radial dist, latitide and longitude
        self.latitude *= spice.dpr()
        self.distance /= 69911
        
        
#-------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    pass
        