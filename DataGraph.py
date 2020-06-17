#!/usr/bin/env python3
from dataclasses import *
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

def Graph():

    timeStart = '2017-03-08T00:00:00.000'
    timeEnd = '2017-03-09T23:59:59.000'

    dataFolder = os.path.join('..','data','jad')
    DOY,ISO,datFiles = getFiles(timeStart,timeEnd,'.DAT',dataFolder,'JAD_L30_LRS_ION_ANY_CNT') 

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
            jadIndex = min(range(len(jadeData['TIME_ARRAY'])), key=lambda j: abs(jadeData['TIME_ARRAY'][j]-i*6))
            fgmIndex = min(range(len(fgmData['TIME_ARRAY'])), key=lambda j: abs(fgmData['TIME_ARRAY'][j]-i*6))

            fig, (ax1,ax2) = plt.subplots(2,1,sharex=True,figsize=(9,4))
            pcm = ax1.imshow(np.transpose(jadeData['DATA_ARRAY'][jadStart:jadIndex+1]),origin='lower',aspect='auto',cmap='jet',extent=((i-1)*6,i*6,0,64))
            ax1.set_title(date)

            ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['BX'][fgmStart:fgmIndex+1],label='$B_x$',linewidth=1)
            ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['BY'][fgmStart:fgmIndex+1],label='$B_y$',linewidth=1)
            ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['BZ'][fgmStart:fgmIndex+1],label='$B_z$',linewidth=1)
            ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['B'][fgmStart:fgmIndex+1],'black',label='$^+_-|B|$',linewidth=0.5)
            ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],-fgmData['B'][fgmStart:fgmIndex+1],'black',linewidth=0.5)
            ax2.legend(loc=(1.01,0.1))
            ax2.set_xlabel('Hrs')
            ax2.xaxis.set_label_coords(1.05,-0.025)
            ax2.set_ylabel('|B| (nT)')

            
            # latPos = []
            # latLabels = []
            # ax3 = ax2.twiny()
            # ax3.set_xticks([6])
            # ax3.set_xticklabels([newTicks])
            # ax3.xaxis.set_ticks_position('bottom') # set the position of the second x-axis to bottom
            # ax3.xaxis.set_label_position('bottom') # set the position of the second x-axis to bottom
            # ax3.spines['bottom'].set_position(('outward',20))

            fgmStart = fgmIndex
            jadStart = jadIndex

            YDOY = datetime.date.fromisoformat(date).strftime('%Y%j')
            timeFormatDict = {1:'00000-0600',2:'0600-1200',3:'1200-1800',4:'1800-2400'}
            
            fileSaveName = f'jad_fgm_{YDOY}_{timeFormatDict[i]}'

            plt.savefig(os.path.join('..\\figures', fileSaveName),bbox_inches='tight',pad_inches=0.02,dpi=150)


if __name__ == '__main__':
    
    Graph()
    


            

    
    