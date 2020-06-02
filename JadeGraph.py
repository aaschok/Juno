import numpy as np 
import matplotlib.pyplot as plt 
import os,struct,scipy

class JadeGraph():
    def __init__(self,dataFolder,startTime,endTime):
        self.dataFolder = dataFolder
        self.startTime = startTime
        self.endTime = endTime
    
    def Graph(self):
        with open(self.dataFolder, "rb") as f:
            species = 3
            windows = 1440
            timeList = np.array([])
            energyMatrix = []
            countSecMatrix = []
            for i in range(windows):
                data = f.read(259872)
                

                byteStart = 66-1
                byteEnd = byteStart+1
                dataSlice = data[byteStart:byteEnd]
                ionSpecies = struct.unpack('b',dataSlice)[0]
                
                if ionSpecies == species:

                    byteStart = 1-1
                    byteEnd = byteStart+21
                    timeStamp = str(data[byteStart:byteEnd],'ascii')
                    timeList = np.append(timeList,timeStamp[9:])

                    
                    byteStart = 69-1
                    byteEnd = byteStart+2
                    dataSlice = data[byteStart:byteEnd]
                    units = struct.unpack('H',dataSlice)[0]
                    

                    
                    byteEnd = 289 - 1
                    for i in range(1,65):
                        byteStart = byteEnd
                        byteEnd = byteStart + 4*78
                        dataSlice = data[byteStart:byteEnd]
                        countsSec = struct.unpack('f'*78,dataSlice)
                        countSecMatrix.append(countsSec)

                    byteEnd = 80161 - 1
                    for i in range(1,65):
                        byteStart = byteEnd
                        byteEnd = byteStart + 4*78
                        dataSlice = data[byteStart:byteEnd]
                        energy = struct.unpack('f'*78,dataSlice)
                        energyMatrix.append(energy)

        countSecMatrix = np.array(countSecMatrix)
        countSecArray = countSecMatrix.flatten()

        energyMatrix = np.array(energyMatrix)
        energyArray = energyMatrix.flatten()
        
        plt.plot(energyArray,countSecArray)
        plt.title('Counts Vs. E')
        plt.ylabel('Counts/Sec')
        plt.xlabel('eV/q')
        plt.show()
        print(len(energyArray))
        plt.specgram(energyArray,Fs=4992,NFFT=78,noverlap=0)
        plt.title('Energy Spec')
        plt.colorbar()
        plt.show()

        print(timeList)
        
        
        



if __name__ == '__main__':

    dataFolder = os.path.join('data','jad','ION_SPECIES','JAD_L30_LRS_ION_ANY_CNT_2017068_V02.DAT')
    #RJW, Name, Format, dimnum, size dim 1, size dim 2,...
    timeStart = 1
    timeEnd = 2

    jade = JadeGraph(dataFolder,timeStart,timeEnd)
    jade.Graph() 