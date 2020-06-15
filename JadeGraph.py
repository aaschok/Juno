import numpy as np 
import matplotlib.pyplot as plt 
import os,struct,scipy,logging

logging.basicConfig(filename='test.log',filemode='w',level=logging.DEBUG)

class JadeData():
    def __init__(self,dataFolder,startTime,endTime):
        self.dataFolder = dataFolder
        self.startTime = startTime
        self.endTime = endTime
        self.dataDict = {}
        self.dataAvg = []

    def test(self):
        for jadeFile in self.dataFolder:
            with open(jadeFile,'rb') as f:
                species = 3
                


    def getData(self):
        with open(self.dataFolder, "rb") as f:
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
    timeStart = 1
    timeEnd = 2

    jade = JadeData(dataFolder,timeStart,timeEnd)
    jade.getData() 
    print(jade.dataDict.keys())

    plt.imshow(np.log(np.array(jade.dataAvg).T)>0,origin='lower',aspect='auto',cmap='plasma')
    plt.colorbar()
    plt.show()
            
