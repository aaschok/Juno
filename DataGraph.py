#!/usr/bin/env python3
from dataclasses import *
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import spiceypy as spice
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)


def getPosLabels(dataDict,num):
    stamp = str(dataDict['DATETIME_ARRAY'][min(range(len(dataDict['TIME_ARRAY'])), key=lambda j: abs(dataDict['TIME_ARRAY'][j]-num))])
                        
    position, lighttime = spice.spkpos('JUNO',spice.utc2et(stamp),'IAU_JUPITER','NONE','JUPITER')
            
    vectorPos = spice.vpack(position[0],position[1],position[2])
    radii,longitude,latitude = spice.reclat(vectorPos)
    lat = f'{round(latitude*spice.dpr(),2)}$^o$ Lat'
    dist = f'{round(radii/69911,3)} $R_j$'
    return lat,dist

def finalGraph():   #This is the final graph function I use

    timeStart = '2017-03-09T00:00:00'
    timeEnd = '2017-03-09T23:59:59'

    orbitsData = {1:'2016-07-31T19:46:02',
                2:'2016-09-23T03:44:48',
                3:'2016-11-15T05:36:45',
                4:'2017-01-07T03:11:30',
                5:'2017-02-28T22:55:48',
                6:'2017-04-22T19:14:57'}

    dataFolder = pathlib.Path('../data/jad')
    DOY,ISO,datFiles = getFiles(timeStart,timeEnd,'.DAT',dataFolder,'JAD_L30_LRS_ION_ANY_CNT') 
    jadeIon = JadeData(datFiles,timeStart,timeEnd)
    jadeIon.getIonData()

    dataFolder = pathlib.Path('../data/fgm')
    DOY,ISO,csvFiles = getFiles(timeStart,timeEnd,'.csv',dataFolder,'fgm_jno_l3') 
    fgm = FGMData(csvFiles,timeStart,timeEnd)

    dataFolder = pathlib.Path('../data/jad')
    DOY,ISO,datFiles = getFiles(timeStart,timeEnd,'.DAT',dataFolder,'JAD_L30_LRS_ELC_ANY_CNT') 
    jadeElec = JadeData(datFiles,timeStart,timeEnd)
    jadeElec.getElecData()

    dataFolder = pathlib.Path('../data/fgm')
    DOY,ISO,csvFiles = getFiles(timeStart,timeEnd,'.csv',dataFolder,'fgm_jno_l3') 
    q = turbulence(ISO,csvFiles,timeStart,timeEnd,1,60,1800,'.')

    metaKernel = 'juno_2019_v03.tm'
    spice.furnsh(metaKernel)

    for date in ISO:

        fgmStart = 0
        jadIonStart = 0
        jadElecStart = 0
        qStart = 0
        
        for i in range(1,5):
            fig, (ax1,ax2,ax3,ax4) = plt.subplots(4,1,sharex=True)
            latLabels, distLabels = [],[]

            if date in jadeIon.dataDict.keys(): #Ion spectrogram portion
                jadeIonData = jadeIon.dataDict[date]  

                jadIonIndex = min(range(len(jadeIonData['TIME_ARRAY'])), key=lambda j: abs(jadeIonData['TIME_ARRAY'][j]-i*6))
                
                spec = ax1.imshow(np.transpose(jadeIonData['DATA_ARRAY'][jadIonStart:jadIonIndex+1]),origin='lower',aspect='auto',cmap='jet',extent=((i-1)*6,i*6,0,64))

                axins = inset_axes(ax1,
                   width="2%",  # width = 5% of parent_bbox width
                   height="100%",  # height : 50%
                   loc='center right',
                   bbox_to_anchor=(0.04, 0, 1, 1),
                   bbox_transform=ax1.transAxes,
                   borderpad=0,
                   )
                cbr = plt.colorbar(spec,cax=axins)
                cbr.set_label('log(Counts/sec)',rotation=270, labelpad=10, size=9)

                dimData = np.array(jadeIonData['DIM1_ARRAY'])/1000
                ticks = [0.1,1,10]
                tickList = []
                dataTicks = []
                for ticknum in ticks:
                    tick = min(range(len(dimData)), key=lambda j: abs(dimData[j]-ticknum))
                    tickList.append(tick)
                    dataTicks.append(dimData[tick])

                ax1.set_yticks(tickList)
                ax1.set_yticklabels(np.round(dataTicks,1),fontsize=9)

                ax1.set_ylabel('E(eV/q)')
                ax1.yaxis.set_label_coords(-0.09,0.5)
                

                jadIonStart = jadIonIndex
            ax1.set_title(date)

            if date in jadeElec.dataDict.keys():    #Electron spectrogram portion
                jadeElecData = jadeElec.dataDict[date]

                jadElecIndex = min(range(len(jadeElecData['TIME_ARRAY'])), key=lambda j: abs(jadeElecData['TIME_ARRAY'][j]-i*6))
                
                elecspec = ax2.imshow(np.transpose(jadeElecData['DATA_ARRAY'][jadElecStart:jadElecIndex+1]),origin='lower',aspect='auto',cmap='jet',extent=((i-1)*6,i*6,0,64))
                
                jadElecStart = jadElecIndex
                axins = inset_axes(ax2,
                        width="2%",  # width = 5% of parent_bbox width
                        height="100%",  # height : 50%
                        loc='center right',
                        bbox_to_anchor=(0.04, 0, 1, 1),
                        bbox_transform=ax2.transAxes,
                        borderpad=0,
                        )
                cbr = plt.colorbar(elecspec,cax=axins)
                cbr.set_label('log(Counts/sec)',rotation=270, labelpad=10, size=9)

                dimData = np.array(jadeElecData['DIM1_ARRAY'])/1000
                ticks = [0.1,1,10]
                tickList = []
                dataTicks = []
                for ticknum in ticks:
                    tick = min(range(len(dimData)), key=lambda j: abs(dimData[j]-ticknum))
                    tickList.append(tick)
                    dataTicks.append(dimData[tick])

                ax2.set_yticks(tickList)
                ax2.set_yticklabels(np.round(dataTicks,1),fontsize=9) 

                ax2.set_ylabel('E(keV)')
                ax2.yaxis.set_label_coords(-0.09,0.5)

            if date in q.dataDict.keys():   #Graphing heating rate Density
                qData = q.dataDict[date]

                qEndIndex = min(range(len(qData['QTIME_ARRAY'])), key=lambda j: abs(qData['QTIME_ARRAY'][j]-i*6))

                timeloop = qData['QTIME_ARRAY'][qStart:qEndIndex+1]                                         #extracts time from time array to fit within 6 hr window
                qloop = qData['Q_ARRAY'][qStart:qEndIndex+1]                                         #extracts q from q array to correspond to the time
                
            
                ax3.plot(timeloop,qloop,'b')
                #for k in range(len(qloop)-1):
                #    ax3.plot((timeloop[k],timeloop[k+1]),(qloop[k],qloop[k]),'b')   #loop used to produce seperate horizontal lines for each value q         
                
                ax3.set_yscale('log')
                ax3.set_ylabel('[W/$m^2$]')
                ax3.yaxis.set_label_coords(-0.09,0.5)
                ax3.tick_params(axis='y',labelsize=9)
                
                qStart = qEndIndex

            if date in fgm.dataDict.keys():     #FGM graph portion
                fgmData = fgm.dataDict[date]
                
                fgmIndex = min(range(len(fgmData['TIME_ARRAY'])), key=lambda j: abs(fgmData['TIME_ARRAY'][j]-i*6))

                ax4.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['BX'][fgmStart:fgmIndex+1],label='$B_x$',linewidth=1)
                ax4.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['BY'][fgmStart:fgmIndex+1],label='$B_y$',linewidth=1)
                ax4.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['BZ'][fgmStart:fgmIndex+1],label='$B_z$',linewidth=1)
                ax4.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['B'][fgmStart:fgmIndex+1],'black',label='$^+_-|B|$',linewidth=0.5)
                ax4.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],-np.array(fgmData['B'][fgmStart:fgmIndex+1]),'black',linewidth=0.5)
                ax4.legend(loc=(1.01,0.07),prop={'size': 9})
                ax4.set_xlabel('Hrs')
                ax4.xaxis.set_label_coords(1.04,-0.07)
                ax4.set_ylabel('|B| (nT)')
                ax4.yaxis.set_label_coords(-0.09,0.5)
                ax4.tick_params(axis='y',labelsize=9)

                fgmStart = fgmIndex

            if date in fgm.dataDict.keys(): #Positional labels portion
                if i == 1:
                    for num in range(0,7):
                        lat, dist = getPosLabels(fgm.dataDict[date],num)
                        latLabels.append(lat)
                        distLabels.append(dist)                   
                elif i == 2:
                    for num in range(6,13):
                        lat, dist = getPosLabels(fgm.dataDict[date],num)
                        latLabels.append(lat)
                        distLabels.append(dist)                   
                elif i == 3:
                    for num in range(12,19):
                        lat, dist = getPosLabels(fgm.dataDict[date],num)
                        latLabels.append(lat)
                        distLabels.append(dist)
                elif i == 4:
                    for num in range(18,25):
                        lat, dist = getPosLabels(fgm.dataDict[date],num)
                        latLabels.append(lat)
                        distLabels.append(dist)

            elif date in jadeIon.dataDict[date]:
                if i == 1:
                    for num in range(0,7):
                        lat, dist = getPosLabels(jadeIon.dataDict[date],num)
                        latLabels.append(lat)
                        distLabels.append(dist)                   
                elif i == 2:
                    for num in range(6,13):
                        lat, dist = getPosLabels(jadeIon.dataDict[date],num)
                        latLabels.append(lat)
                        distLabels.append(dist)                   
                elif i == 3:
                    for num in range(12,19):
                        lat, dist = getPosLabels(jadeIon.dataDict[date],num)
                        latLabels.append(lat)
                        distLabels.append(dist)
                elif i == 4:
                    for num in range(18,25):
                        lat, dist = getPosLabels(jadeIon.dataDict[date],num)
                        latLabels.append(lat)
                        distLabels.append(dist)

            if date not in jadeIon.dataDict.keys() and date not in fgm.dataDict.keys():
                continue

            ax5 = ax4.twiny()
            ax6 = ax5.twiny()        

            ax5.set_xticks([0,1,2,3,4,5,6])
            ax5.set_xticklabels(latLabels)    
            ax5.xaxis.set_ticks_position('bottom')
            ax5.tick_params(axis='both',which='both',length=0,pad = 20)

            ax6.set_xticks([0,1,2,3,4,5,6])
            ax6.set_xticklabels(distLabels)    
            ax6.xaxis.set_ticks_position('bottom')
            ax6.tick_params(axis='both',which='both',length=0,pad = 33)

            for orbit, orbitStart in orbitsData.items():
                orbitStart = datetime.datetime.fromisoformat(orbitStart)
                currDate = datetime.date.fromisoformat(date)

                if orbitStart.date() > currDate:
                    orbitNum = orbit
                    break
                
            YDOY = datetime.date.fromisoformat(date).strftime('%Y%j')
            timeFormatDict = {1:'0000',2:'0600',3:'1200',4:'1800'}
            
            fileSaveName = f'jad_fgm_{YDOY}_{timeFormatDict[i]}'

            plt.savefig(pathlib.Path(f'../figures/orbit{orbitNum}/{fileSaveName}'),bbox_inches='tight',pad_inches=0.02,dpi=150)
            plt.close(fig)
        print(f'Graphs for {date} created')

def testFunc():

    timeStart = '2017-03-09T00:00:00'
    timeEnd = '2017-03-09T23:59:59'

    orbitsData = {1:'2016-07-31T19:46:02',
                2:'2016-09-23T03:44:48',
                3:'2016-11-15T05:36:45',
                4:'2017-01-07T03:11:30',
                5:'2017-02-28T22:55:48',
                6:'2017-04-22T19:14:57'}

    dataFolder = pathlib.Path('../data/fgm')
    DOY,ISO,csvFiles = getFiles(timeStart,timeEnd,'.csv',dataFolder,'fgm_jno_l3') 
    q = turbulence(ISO,csvFiles,timeStart,timeEnd,1,60,1800,'.')
    fig,ax3=plt.subplots()

    for date in ISO:
        qStart = 0
        for i in range(1,5):
            qData = q.dataDict[date]

            qEndIndex = min(range(len(qData['QTIME_ARRAY'])), key=lambda j: abs(qData['QTIME_ARRAY'][j]-i*6))

            timeloop = qData['QTIME_ARRAY'][qStart:qEndIndex+1]                                         #extracts time from time array to fit within 6 hr window
            qloop = qData['Q_ARRAY'][qStart:qEndIndex+1]                                         #extracts q from q array to correspond to the time
                
            print(f'Q:{qloop}')
            print(f'Time: {timeloop}')
            
            ax3.plot(timeloop,qloop,'b')     
                
            ax3.set_yscale('log')
            ax3.set_ylabel('mean heating rate density [W/$m^2$]')
                
            qStart = qEndIndex
    plt.show()
if __name__ == '__main__':
    
    testFunc()


            

    
    