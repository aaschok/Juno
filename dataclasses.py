import numpy as np 
import pandas as pd
import os,datetime,logging,pathlib,struct
import matplotlib.pyplot as plt
import spiceypy as spice
from scipy import signal
from sklearn.linear_model import LinearRegression

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
                    
                    self.dataDict[dateStamp]['DATA_ARRAY'].append(np.log(dataArray)) #The log of the data column is taken and appended to the data dictionary under the key DATA_ARRAY

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
        self.positionData()

    def positionData(self):
        spice.furnsh(self.meta) #loads the meta kernel that will load all kernels needed

        time = spice.utc2et(self.time)
        
        self.position, lighttime = spice.spkpos('JUNO',time,'IAU_JUPITER','NONE','JUPITER') #Finds the position in cartesian coords relative to jupiter
        
        pos = spice.vpack(self.position[0],self.position[1],self.position[2])   #Packs the position into a vector
        self.distance,self.longitude,self.latitude = spice.reclat(pos) #Finds radial dist, latitide and longitude
        self.latitude *= spice.dpr()
        self.distance /= 69911


def gyro(bx, by, bz, m, z, q):
    """finds a gyrofreqency given magnetosphere properties.  \n All inputs must be in
    fundamental units (T, m, etc.) \n Returns scalar qyrofrequency corresponding to given
    range of B"""
    mean_b = np.mean(np.sqrt(bx**2 + by**2 + bz**2))
    gyrofreq = (z*q/m)*(mean_b/(2*np.pi))
    return gyrofreq

#------------------------------------------------------------------------------------

def q(psd_perp,freq, bx, by, bz, b1, b2, m): 
    """Takes PSD of perpendicular component and other parameters to find q MHD 
    and q KAW.  \n Every parameter must be in base units (T, kg, m, etc).  \n Empirical
    parameters are subject to adjustment below.  \n Outputs ranges of q MHD and q KAW 
    over freqency domains, according to b1 and b2 (respectively MHD and KAW freqency 
    domains. \n MAG vector components used only to find theta for k perp.  """
    delta_b_perp3 = (psd_perp*freq)**(3/2)
    v_rel_x = -400e3                                                           #convert to m/s
    v_rel_y = -100e3                                                           #these parameters subject to change over spatial domain
    v_rel_mag = 300e3
    avgbx = np.mean(bx)*np.ones(len(bx))                                       #converted to vector for dot product
    avgby = np.mean(by)*np.ones(len(bx))
    avgbz = np.mean(bz)*np.ones(len(bz))
    mean_b_mag = np.sqrt(avgbx**2 + avgby**2 + avgbz**2)
    #dotfactor = (avgbx*v_rel_x + avgby*v_rel_y)/(mean_b_mag*v_rel_mag)        #find dot product and corresponding angle for k perp
    #theta = np.arccos((dotfactor))
    n_density = 0.1*(100**3)
    density = m*n_density
    mu_0 = np.pi*4*1e-7
    kperp = (2*np.pi*freq)/(v_rel_mag*np.sin(np.pi/2))                         #currently just assumes v rel and B are perpendicular
    rho_i = 1e7                                                                #parameter subject to change, currently an estimation from Tao et al
    
    qkaw = (0.5*(delta_b_perp3[b2])*kperp[b2]/np.sqrt(mu_0**3*density))*(1+kperp[b2]**2*rho_i**2)**0.5*(1+(1/(1+kperp[b2]**2*rho_i**2))*(1/(1+1.25*kperp[b2]**2*rho_i**2))**2)
    qmhd = (delta_b_perp3[b1])*kperp[b1]/(np.sqrt((mu_0**3)*density))
    
    return qmhd, qkaw
#--------------------------------------------------------------------------------
    
def freqrange(f, gyro):
    """Finds ranges of freqencies for MHD and KAW scales.\n  
    Inputs: f is frequency range for PSD, and gyro is the gyrofreqency for given domain. \n
    Returns the two frequency arrays and indices (tuples) for the two arrays. \n b1
    corresponds to MHD, b2 to KAW, and b3 to all real points of freqency range."""
    
    b1 = np.where((f>3E-4) & (f<(gyro)))                                       #MHD range
    freq_mhd = f[b1]
    
    b2 = np.where((f>(gyro*1.5)) & (f<0.1))                                    #KAW range
    freq_kaw = f[b2]
    
    b3 = np.where((f>0)&(f<0.5))                                               #range for all real frequency
    return freq_mhd, freq_kaw, b1, b2, b3 

#-------------------------------------------------------------------------------

def PSDfxn(cwt,freq,sig,fs):
    """Finds PSD as per Tao et. al. 2015 given a morlet wavelet transform, frequency 
    range, the signal, and sampling frequency. \n Outputs an array of length of signal"""
    psd_list = []
    for i in range(len(sig)):
        psd = (2*fs/len(sig))*(sum(abs(cwt[i]**2)))/freq[i]
        psd_list.append(psd)
    psd = np.array(psd_list)
    return psd        

#------------------------------------------------------------------------------   
  
class turbulence(FGMData):
    """calculates heating rate density and power spectral density then creates various plots.  \n Step, window, and interval must be in seconds as an integer. \n
    Inherits FGMData class to extract BX, BY, and BZ data. \n
    dateList must be from getFiles, and startTime and endTime must be in UTC 
    i.e., "2016-09-22T00:00:00.0000\n Made by Ti Donaldson"""
    def __init__(self, dateList, filelist, startTime, endTime, step, window, interval,savePath):
        super().__init__(filelist, startTime, endTime)
        self.dateList = dateList
        self.step = step                                        
        self.window = window                                                   #for average B field
        self.interval = interval                                               #interval over which PSD is found
        self.savePath = savePath                                               #directory for figures to be saved to
        self.m = 23/6.0229e26                                                  #average ion mass
        self.z = 1.6                                                           #charge state  
        self.q = 1.6e-19                                                       #elementary charge
        self.mhd_slopelist = []
        self.kaw_slopelist = []
        self.qmhd_biglist = []
        self.qkaw_biglist = []
        self.get_q()

    def get_q(self):
        for date in self.dateList:
            bx = np.array(self.dataDict[date]['BX'])                           #extract MAG data for each day, compile into arrays         
            by = np.array(self.dataDict[date]['BY'])
            bz = np.array(self.dataDict[date]['BZ'])
            qmhd_list = []
            qkaw_list = []
            avgbx = []
            avgby = []
            avgbz = []
            freq = 0
            for i in range(len(bx)):
                avebx = np.mean(bx[i*self.step:i*self.step + self.window])     #find average B field, given the window for taking running average 
                aveby = np.mean(by[i*self.step:i*self.step +self.window])
                avebz = np.mean(bz[i*self.step:i*self.step +self.window])
                avgbx.append(avebx)
                avgby.append(aveby)
                avgbz.append(avebz)
            avgbx = np.array(avgbx)
            avgby = np.array(avgby)
            avgbz = np.array(avgbz)
                
            for i in range(int(len(bx)/self.interval)):                        #find PSD and q over given interval                 
                
                avgbxloop = avgbx[i*self.interval:(1+i)*self.interval]         #extracts average B field into arrays of size of interval
                avgbyloop = avgby[i*self.interval:(1+i)*self.interval]
                avgbzloop = avgbz[i*self.interval:(1+i)*self.interval] 
                
                delta_bx = bx[i*self.interval:(1+i)*self.interval] - avgbxloop #B - B0 to get delta B
                delta_by = by[i*self.interval:(1+i)*self.interval] - avgbyloop
                delta_bz = bz[i*self.interval:(1+i)*self.interval] - avgbzloop
                
                dotfactor = (delta_bx*avgbxloop + delta_by*avgbyloop +delta_bz*avgbzloop)/(avgbxloop**2 + avgbyloop**2 + avgbzloop**2)
                
                delta_bx_par = dotfactor*avgbxloop                             #decomposition of delta B alligned to average B field
                delta_by_par = dotfactor*avgbyloop
                delta_bz_par = dotfactor*avgbzloop
                
                delta_bx_perp1 = delta_bx - delta_bx_par                       #subtract parallel component from delta B to get first perpendicular vector
                delta_by_perp1 = delta_by - delta_by_par
                delta_bz_perp1 = delta_bz - delta_bz_par
                
                delta_bx_perp2 = []
                delta_by_perp2 = []
                delta_bz_perp2 = []
                
                for j in range(len(delta_bx_perp1)):                           #difficult to perform numpy cross without involvement of lists
                    cross = np.cross([delta_bx_par[j],delta_by_par[j],delta_bz_par[j]],[delta_bx_perp1[j],delta_by_perp1[j],delta_bz_perp1[j]])
                    delta_bx_perp2.append(cross[0])                            #extracts x, y, z components of 2nd perpendicular vector
                    delta_by_perp2.append(cross[1])
                    delta_bz_perp2.append(cross[2])
                delta_bx_perp2 = np.array(delta_bx_perp2)
                delta_by_perp2 = np.array(delta_by_perp2)
                delta_bz_perp2 = np.array(delta_bz_perp2)
                
                delta_b_perp1 = np.sqrt(delta_bx_perp1**2 + delta_by_perp1**2 + delta_bz_perp1**2)   #find magnitudes of each vector
                delta_b_perp2 = np.sqrt(delta_bx_perp2**2 + delta_by_perp2**2 + delta_bz_perp2**2)
                delta_b_par = np.sqrt(delta_bx_par**2 + delta_by_par**2 + delta_bz_par**2)
                
                fs = int(1/(self.step))                                        #sampling freqency, based off of given step size
                freq = np.arange(0.1,len(delta_b_par))*fs/len(delta_b_par)     #finds freqency range (this is ~divided by 2~ as per FFT analysis in freqrange function)
                widths = 1/(1.03*freq)                                         #parameter for cwt
                w0 = 6                                                         #as per Tao et. al. 2015
                
                #psd_par = PSDfxn(signal.cwt(delta_b_par,signal.morlet2, widths,w = w0), freq, delta_b_par, fs)
                psd_perp1 = PSDfxn(signal.cwt(delta_b_perp1, signal.morlet2, widths, w = w0), freq, delta_b_perp1, fs)
                psd_perp2 = PSDfxn(signal.cwt(delta_b_perp2, signal.morlet2, widths, w = w0), freq, delta_b_perp2, fs)
                psd_perp = (psd_perp1 + psd_perp2)*1e-18                       #calls PSDfxn to find PSD given morlet wavelet transforms of each vector component.  
                                                                                #the two perpendicular compoenents are summed to find total perpendicular, converted to T^2
                
                gyrofreq = gyro(bx[self.interval*i:(1+i)*self.interval]*1e-9, by[self.interval*i:(i+1)*self.interval]*1e-9, bz[self.interval*i:(1+i)*self.interval]*1e-9, self.m, self.z, self.q)
                                                                               #finds gyrofreqency according to B values on given interval (which is why the above line is so long)
                freq_mhd, freq_kaw, b1, b2, b3 = freqrange(freq, gyrofreq)     #uses freqrange function to find MHD and KAW frequency ranges 
                
                q_mhd, q_kaw = q(psd_perp, freq, bx[i*self.interval:(1+i)*self.interval]*1e-9, by[i*self.interval:(1+i)*self.interval]*1e-9, bz[i*self.interval:(1+i)*self.interval]*1e-9, b1, b2, self.m)
                                                                               #finds q MHD and q KAW, which have length of b1 and b2 respectively
                mean_q_mhd = np.mean(q_mhd)                                    #finds average q values for given interval
                mean_q_kaw = np.mean(q_kaw)
                
                qmhd_list.append(mean_q_mhd)
                qkaw_list.append(mean_q_kaw)
                
                self.qmhd_biglist.append(mean_q_mhd)                           #appends mean q values to list of every q value over the date range for histogram
                self.qkaw_biglist.append(mean_q_kaw)
                
                if len(q_mhd) == 0 or len(q_kaw) == 0:                          #check that there is a KAW or MHD scale on frequency range
                    pass
                
                else:
                
                    r = LinearRegression()                                         #perform linear regression to find power law fits
                    r.fit(np.reshape(np.log10(freq_mhd),(-1,1)), np.reshape(np.log10(psd_perp[b1]),(-1,1)))
                    self.mhd_slopelist.append(r.coef_)                             #append to list of slopes for KAW and MHD per each interval.  
                                                                               #I.E. each interval corresponds to one value of KAW slope and one value of MHD slope
                    r.fit(np.reshape(np.log10(freq_kaw),(-1,1)), np.reshape(np.log10(psd_perp[b2]),(-1,1)))
                    self.kaw_slopelist.append(r.coef_)
                
                #fig = plt.figure()                                             #plot heating rate densities on frequency domain
                #ax1 = fig.add_subplot(211)
                #ax1.loglog(freq_mhd,q_mhd,'r')
                #ax1.loglog(freq_kaw,q_kaw,'b')
                #ax1.loglog(freq_mhd,np.linspace(mean_q_mhd,mean_q_mhd,len(freq_mhd)),'black')
                #ax1.loglog(freq_kaw,np.linspace(mean_q_kaw,mean_q_kaw,len(freq_kaw)),'black')
                #ax1.set_title(date + '  ' + str(datetime.timedelta(seconds = i*self.interval)))
                #ax1.set_ylabel('heating rate density \n [W/$m^2$]')
                #ax1.set_yticks([1e-19,1e-17,1e-15,1e-13,1e-11])
                
                
                #ax2 = fig.add_subplot(212, sharex =ax1)                        #plot power spectral density and gyrofrequency
                #ax2.loglog(freq[b3],psd_perp[b3]*1e18, linewidth = 1)
                #ax2.loglog(freq_mhd,psd_perp[b1]*1e18,'r', linewidth = 0.5)
                #ax2.loglog(freq_kaw,psd_perp[b2]*1e18,'b', linewidth = 0.5)
                #ax2.loglog((gyrofreq,gyrofreq),(0,np.max(psd_perp)*1e20),'g--')
                #ax2.set_xlabel('frequency [Hz]')
                #ax2.set_ylabel('Power Density \n [$nT^2$/Hz]')
                #ax2.set_yticks([1e-3,1e-1,1e1,1e3,1e5])
                #plt.tight_layout()
                
                
                #saveName = f'PSD_and_q_{date}_{i}'                             #create file name with date and interval on that day
                #plt.savefig(f'{self.savePath}\\{saveName}')
               
            mean_q = (np.array(qmhd_list) + np.array(qkaw_list))/2
            time = np.linspace(np.min(self.dataDict[date]['TIME_ARRAY']),np.max(self.dataDict[date]['TIME_ARRAY']),len(mean_q))
            
            self.dataDict[date]['QTIME_ARRAY'] = time
            self.dataDict[date]['Q_ARRAY'] = mean_q
            #for i in range(4):
                
            #    xtick = np.arange(i*6,(1+i)*6+1)
            #    plt.figure(figsize = (10,4))                                     #plot q over time on a 6 hour window
            #    index = np.where((i*6<=time) & ((i+1)*6>=time))                 #index for time within each 6 hr window
                
            #    timeloop = time[index]                                         #extracts time from time array to fit within 6 hr window
            #    qloop = mean_q[index]                                          #extracts q from q array to correspond to the time
                
            #    for k in range(len(qloop)-1):
            #        plt.plot((timeloop[k],timeloop[k+1]),(qloop[k],qloop[k]),'b')   #loop used to produce seperate horizontal lines for each value q         
                
                
            #    plt.xticks(xtick, [str(xtick[0])+':00',str(xtick[1])+':00',str(xtick[2])+':00',str(xtick[3])+':00',str(xtick[4])+':00',str(xtick[5])+':00',str(xtick[6])+':00'])
            #    plt.rcParams['xtick.bottom'] = plt.rcParams['xtick.labelbottom']=True
            #    plt.rcParams['xtick.top'] = True                                    #format tick marks
                
            #    plt.title(date)
            #    plt.yscale('log')
            #    plt.xlabel('time [hours]')
            #    plt.ylabel('mean heating rate density [W/$m^2$]')
        
            #    timeFormat = {0:'0000',1:'0600',2:'1200',3:'1800'}
                #saveName = f'q_time_domain_{date}_{timeFormat[i]}'             #produces file name with date and start time
                
                #plt.savefig(f'{self.savePath}/{saveName}')
        
        #mhd_slope = np.array(self.mhd_slopelist)
        #kaw_slope = np.array(self.kaw_slopelist)
        
        #plt.figure()                                                           #create histograms of power laws and KAW and MHD differences
        #plt.hist(np.reshape(mhd_slope,(-1,1)),8)
        #plt.plot((-5/3,-5/3),(0,len(self.mhd_slopelist)))                       #theoretical power law
        #plt.xlabel('MHD Power Law')
        #plt.ylabel('count')
        #plt.title('MHD')
        
        #saveName = f'hist_MHD_power_law_{min(self.dateList)}_{max(self.dateList)}'
        #plt.savefig(f'{self.savePath}/{saveName}')
        
        #plt.figure()
        #plt.hist(np.reshape(kaw_slope,(-1,1)),8)
        #plt.plot((-7/3,-7/3),(0,len(self.kaw_slopelist)))                      #theoretical power law
        #plt.xlabel('KAW Power Law')
        #plt.ylabel('count')
        #plt.title('KAW')
        
        #saveName = f'hist_KAW_power_law_{min(self.dateList)}_{max(self.dateList)}'
        #plt.savefig(f'{self.savePath}/{saveName}')
        
        #q_diff = np.log10(np.array(self.qmhd_biglist))-np.log10(np.array(self.qkaw_biglist)) #find the log difference bewteen KAW and MHD scales
        #plt.figure()
        #plt.hist(q_diff,8)
        #plt.ylabel('count')
        #plt.xlabel('$log_1$$_0$($q_M$$_H$$_D$)-$log_1$$_0$(q$_K$$_A$$_W$)')
        
        #saveName = f'hist_scale_diff_{min(self.dateList)}_{max(self.dateList)}'
        #plt.savefig(f'{self.savePath}/{saveName}')          
#-------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    pass
        