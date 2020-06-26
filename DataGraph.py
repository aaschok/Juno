#!/usr/bin/env python3
from dataclasses import *
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import spiceypy as spice

def graph():

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
    jade = JadeData(datFiles,timeStart,timeEnd)

    dataFolder = os.path.join('..','data','fgm')
    DOY,ISO,csvFiles = getFiles(timeStart,timeEnd,'.csv',dataFolder,'fgm_jno_l3') 
    fgm = FGMData(csvFiles,timeStart,timeEnd)

    metaKernel = 'juno_2019_v03.tm'
    spice.furnsh(metaKernel)

    for date in ISO:
        
        fgmStart = 0
        jadStart = 0
        
        for i in range(1,5):
            fig, (ax1,ax2) = plt.subplots(2,1,sharex=True,figsize=(10,4))
            latLabels, distLabels = [],[]

            if date in jade.dataDict.keys():
                jadeData = jade.dataDict[date]  

                jadIndex = min(range(len(jadeData['TIME_ARRAY'])), key=lambda j: abs(jadeData['TIME_ARRAY'][j]-i*6))
                
                spec = ax1.imshow(np.transpose(jadeData['DATA_ARRAY'][jadStart:jadIndex+1]),origin='lower',aspect='auto',cmap='jet',extent=((i-1)*6,i*6,0,64))

                axins = inset_axes(ax1,
                   width="2%",  # width = 5% of parent_bbox width
                   height="100%",  # height : 50%
                   loc='center right',
                   bbox_to_anchor=(0.04, 0, 1, 1),
                   bbox_transform=ax1.transAxes,
                   borderpad=0,
                   )
                fig.colorbar(spec,cax=axins)

                if i == 1:
                    for num in range(0,7):
                        stamp = str(jadeData['DATETIME_ARRAY'][min(range(len(jadeData['TIME_ARRAY'])), key=lambda j: abs(jadeData['TIME_ARRAY'][j]-num))])
                        
                        position, lighttime = spice.spkpos('JUNO',spice.utc2et(stamp),'IAU_JUPITER','NONE','JUPITER')
            
                        pos = spice.vpack(position[0],position[1],position[2])
                        radii,longitude,latitude = spice.reclat(pos)
                        latLabels.append(f'{round(latitude*spice.dpr(),2)}$^o$ Lat')
                        distLabels.append(f'{round(radii/69911,3)} $R_j$')
                
                elif i == 2:
                    for num in range(6,13):
                        stamp = str(jadeData['DATETIME_ARRAY'][min(range(len(jadeData['TIME_ARRAY'])), key=lambda j: abs(jadeData['TIME_ARRAY'][j]-num))])
                        
                        position, lighttime = spice.spkpos('JUNO',spice.utc2et(stamp),'IAU_JUPITER','NONE','JUPITER')
            
                        pos = spice.vpack(position[0],position[1],position[2])
                        radii,longitude,latitude = spice.reclat(pos)
                        latLabels.append(f'{round(latitude*spice.dpr(),2)}$^o$ Lat')
                        distLabels.append(f'{round(radii/69911,3)} $R_j$')
                
                elif i == 3:
                    for num in range(12,19):
                        stamp = str(jadeData['DATETIME_ARRAY'][min(range(len(jadeData['TIME_ARRAY'])), key=lambda j: abs(jadeData['TIME_ARRAY'][j]-num))])
                        
                        position, lighttime = spice.spkpos('JUNO',spice.utc2et(stamp),'IAU_JUPITER','NONE','JUPITER')
            
                        pos = spice.vpack(position[0],position[1],position[2])
                        radii,longitude,latitude = spice.reclat(pos)
                        latLabels.append(f'{round(latitude*spice.dpr(),2)}$^o$ Lat')
                        distLabels.append(f'{round(radii/69911,3)} $R_j$')

                elif i == 4:
                    for num in range(18,25):
                        stamp = str(jadeData['DATETIME_ARRAY'][min(range(len(jadeData['TIME_ARRAY'])), key=lambda j: abs(jadeData['TIME_ARRAY'][j]-num))])
                        
                        position, lighttime = spice.spkpos('JUNO',spice.utc2et(stamp),'IAU_JUPITER','NONE','JUPITER')
            
                        pos = spice.vpack(position[0],position[1],position[2])
                        radii,longitude,latitude = spice.reclat(pos)
                        latLabels.append(f'{round(latitude*spice.dpr(),2)}$^o$ Lat')
                        distLabels.append(f'{round(radii/69911,3)} $R_j$')

                jadStart = jadIndex
            ax1.set_title(date)
            

            if date in fgm.dataDict.keys():
                fgmData = fgm.dataDict[date]
                
                fgmIndex = min(range(len(fgmData['TIME_ARRAY'])), key=lambda j: abs(fgmData['TIME_ARRAY'][j]-i*6))

                ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['BX'][fgmStart:fgmIndex+1],label='$B_x$',linewidth=1)
                ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['BY'][fgmStart:fgmIndex+1],label='$B_y$',linewidth=1)
                ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['BZ'][fgmStart:fgmIndex+1],label='$B_z$',linewidth=1)
                ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],fgmData['B'][fgmStart:fgmIndex+1],'black',label='$^+_-|B|$',linewidth=0.5)
                ax2.plot(fgmData['TIME_ARRAY'][fgmStart:fgmIndex+1],-np.array(fgmData['B'][fgmStart:fgmIndex+1]),'black',linewidth=0.5)
                ax2.legend(loc=(1.01,0.1))
                ax2.set_xlabel('Hrs')
                ax2.xaxis.set_label_coords(1.04,-0.053)
                ax2.set_ylabel('|B| (nT)')

                if len(latLabels) == 0 and len(distLabels) == 0:
                    if i == 1:
                        for num in range(0,7):
                            stamp = fgmData['DATETIME_ARRAY'][min(range(len(fgmData['TIME_ARRAY'])), key=lambda j: abs(fgmData['TIME_ARRAY'][j]-num))]
                            
                            position, lighttime = spice.spkpos('JUNO',spice.utc2et(stamp),'IAU_JUPITER','NONE','JUPITER')
                
                            pos = spice.vpack(position[0],position[1],position[2])
                            radii,longitude,latitude = spice.reclat(pos)
                            latLabels.append(f'{round(latitude*spice.dpr(),2)}$^o$ Lat')
                            distLabels.append(f'{round(radii/69911,3)} $R_j$')
                    
                    elif i == 2:
                        for num in range(6,13):
                            stamp = fgmData['DATETIME_ARRAY'][min(range(len(fgmData['TIME_ARRAY'])), key=lambda j: abs(fgmData['TIME_ARRAY'][j]-num))]
                            
                            position, lighttime = spice.spkpos('JUNO',spice.utc2et(stamp),'IAU_JUPITER','NONE','JUPITER')
                
                            pos = spice.vpack(position[0],position[1],position[2])
                            radii,longitude,latitude = spice.reclat(pos)
                            latLabels.append(f'{round(latitude*spice.dpr(),2)}$^o$ Lat')
                            distLabels.append(f'{round(radii/69911,3)} $R_j$')
                    
                    elif i == 3:
                        for num in range(12,19):
                            stamp = fgmData['DATETIME_ARRAY'][min(range(len(fgmData['TIME_ARRAY'])), key=lambda j: abs(fgmData['TIME_ARRAY'][j]-num))]
                            
                            position, lighttime = spice.spkpos('JUNO',spice.utc2et(stamp),'IAU_JUPITER','NONE','JUPITER')
                
                            pos = spice.vpack(position[0],position[1],position[2])
                            radii,longitude,latitude = spice.reclat(pos)
                            latLabels.append(f'{round(latitude*spice.dpr(),2)}$^o$ Lat')
                            distLabels.append(f'{round(radii/69911,3)} $R_j$')

                    elif i == 4:
                        for num in range(18,25):
                            stamp = fgmData['DATETIME_ARRAY'][min(range(len(fgmData['TIME_ARRAY'])), key=lambda j: abs(fgmData['TIME_ARRAY'][j]-num))]
                            
                            position, lighttime = spice.spkpos('JUNO',spice.utc2et(stamp),'IAU_JUPITER','NONE','JUPITER')
                
                            pos = spice.vpack(position[0],position[1],position[2])
                            radii,longitude,latitude = spice.reclat(pos)
                            latLabels.append(f'{round(latitude*spice.dpr(),2)}$^o$ Lat')
                            distLabels.append(f'{round(radii/69911,3)} $R_j$')

                fgmStart = fgmIndex
            
            if date not in jade.dataDict.keys() and date not in fgm.dataDict.keys():
                continue

            ax3 = ax2.twiny()
            ax4 = ax3.twiny()        

            ax3.set_xticks([0,1,2,3,4,5,6])
            ax3.set_xticklabels(latLabels)    
            ax3.xaxis.set_ticks_position('bottom')
            ax3.tick_params(axis='both',which='both',length=0,pad = 20)

            ax4.set_xticks([0,1,2,3,4,5,6])
            ax4.set_xticklabels(distLabels)    
            ax4.xaxis.set_ticks_position('bottom')
            ax4.tick_params(axis='both',which='both',length=0,pad = 33)

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

def posTest():

    timeStart = '2017-03-08T06:00:00'
    timeEnd = '2017-02-20T23:59:59'
    kernel = 'juno_2019_v03.tm'

    spice = SpiceData(kernel,timeStart,timeEnd)
    spice.getData()

if __name__ == '__main__':
    
    graph()
    


            

    
    