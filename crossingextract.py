import csv, datetime, pathlib, os, re, pickle
import pandas as pd
import numpy as np
from spacepy import pycdf
import spiceypy as spice

class CrossingsDataCDF():

    def __init__(self,data_folder,fgm_folder):
        self.data_folder = pathlib.Path(data_folder)
        self.fgm_folder = pathlib.Path(fgm_folder)
        self.crossingdf = None
        self.cdfdf = pd.DataFrame()
        self.getData()
        self.getFgmData()
        

    def getData(self):
        for file_name in os.listdir(self.data_folder):
            file_path = os.path.join(self.data_folder,file_name)
            if file_path.endswith('.dat'):                
                dat = pd.read_csv(file_path)
                
                      
            else:continue
            if self.crossingdf is None:
                self.crossingdf = dat
            else:
                self.crossingdf = self.crossingdf.append(dat,ignore_index=True)
        #From here down the crossings dates are looked at to find which cooresponding mag data is available for each date
        self.file_dict = {}
        p = re.compile(r'\d{7}')
        for parent,child,files in os.walk(self.fgm_folder):
            for file_name in files:
                if file_name.endswith('.csv'):
                    file_path = os.path.join(self.fgm_folder,file_name)
                    date = p.search(file_name).group()
                    date_iso = datetime.datetime.strptime(date,'%Y%j').strftime('%Y-%m-%d')
                    
                    match = self.crossingdf.loc[self.crossingdf['DATE'] == date_iso]
                    self.cdfdf = self.cdfdf.append(match,ignore_index = True)
                    if date_iso not in self.file_dict.keys():
                        self.file_dict[date_iso] = file_path
            
    def getFgmData(self):
        for row in self.cdfdf.itertuples():
            date = row[1]
            time = row[2]
            type = row[3]
            crossing_stamp = datetime.datetime.strptime(f'{date}T{time}','%Y-%m-%dT%H:%M:%S')
            if date in self.file_dict.keys():
                
                fgm_data = pd.read_csv(self.file_dict[date])
                time_list = [datetime.datetime.fromisoformat(i) for i in fgm_data['SAMPLE UTC']]
                #crossing_index = min(time_list,key=lambda x: abs(x-crossing_stamp))
                crossing_index_plus = time_list.index(min(time_list,key=lambda x: abs(x-(crossing_stamp+datetime.timedelta(hours=2)))))
                crossing_index_minus = time_list.index(min(time_list,key=lambda x: abs(x-(crossing_stamp-datetime.timedelta(hours=2)))))
                save_time_list = [i.isoformat() for i in time_list[crossing_index_minus:crossing_index_plus+1]]

                spice.furnsh('juno_2019_v03.tm')
                spice_time_list = [spice.utc2et(i) for i in save_time_list]
                position_list = []
                latitude_list = []
                for spice_time in spice_time_list:
                    pos,lt = spice.spkpos('JUNO',spice_time,'IAU_JUPITER','NONE','JUPITER')
                    pos_vec = spice.vpack(pos[0],pos[1],pos[2])
                    rad_pos,long,lat = spice.reclat(pos_vec)
                    lat *= spice.dpr()
                    rad_pos /= 69911

                    position_list.append(rad_pos)
                    latitude_list.append(lat)
                spice.kclear()

                file_save_date = crossing_stamp.strftime('%Y%jT%H%M%S') + f'_{type}'
                cdf_file = pycdf.CDF(f'..\crossings\cdf\jno_mag_{file_save_date}.cdf','')
                cdf_file.attrs['Author'] = 'Andrew Schok'
                cdf_file['TIME'] = save_time_list
                cdf_file['BX DATA'] = fgm_data['BX PLANETOCENTRIC'][crossing_index_minus:crossing_index_plus+1]
                cdf_file['BX DATA'].attrs['units'] = 'nT'
                cdf_file['BY DATA'] = fgm_data['BY PLANETOCENTRIC'][crossing_index_minus:crossing_index_plus+1]
                cdf_file['BY DATA'].attrs['units'] = 'nT'
                cdf_file['BZ DATA'] = fgm_data['BZ PLANETOCENTRIC'][crossing_index_minus:crossing_index_plus+1]
                cdf_file['BZ DATA'].attrs['units'] = 'nT'
                cdf_file['X POSITION'] = [i/69911 for i in fgm_data['X'][crossing_index_minus:crossing_index_plus+1]]
                cdf_file['X POSITION'].attrs['units'] = 'Rj'
                cdf_file['Y POSITION'] = [i/69911 for i in fgm_data['Y'][crossing_index_minus:crossing_index_plus+1]]
                cdf_file['Y POSITION'].attrs['units'] = 'Rj'
                cdf_file['Z POSITION'] = [i/69911 for i in fgm_data['Z'][crossing_index_minus:crossing_index_plus+1]]
                cdf_file['Z POSITION'].attrs['units'] = 'Rj'
                cdf_file['RADIAL DISTANCE'] = position_list
                cdf_file['RADIAL DISTANCE'].attrs['units'] = 'Rj'
                cdf_file['LATITUDE'] = latitude_list
                cdf_file['LATITUDE'].attrs['units'] = 'deg'

                cdf_file.close()
                print(f'Created CDF for {type} crossing {crossing_stamp.strftime("%Y-%m-%dT%H:%M:%S")}')

def dataToCDF():
    crossings_folder = r'..\crossings'
    fgm_folder = r'..\data\fgm'
    Crossings = CrossingsDataCDF(crossings_folder,fgm_folder)

def dataToPickle():
    orbits_begin = {1:'2016-07-31T19:46:02',
                            2:'2016-09-23T03:44:48',
                            3:'2016-11-15T05:36:45',
                            4:'2017-01-07T03:11:30',
                            5:'2017-02-28T22:55:48',
                            6:'2017-04-22T19:14:57'}
    
    file_dict = {}
    metaKernel = 'juno_2019_v03.tm'
    spice.furnsh(metaKernel)

    start_time = datetime.datetime.strptime(orbits_begin[1],'%Y-%m-%dT%H:%M:%S')
    
    end_time = datetime.datetime.strptime(orbits_begin[2],'%Y-%m-%dT%H:%M:%S')
    
    data_folder = pathlib.Path(r'..\data\fgm')
    p = re.compile(r'\d{7}')
    
    for parent,child,files in os.walk(data_folder):
        for name in files:
            if name.endswith('.csv'):
                file_path = os.path.join(data_folder,name)
                
                search = p.search(name).group()
                date = datetime.datetime.strptime(search,'%Y%j')
                
                if date.date() >= start_time.date() and date.date() <= end_time.date():
                    iso_date = date.strftime('%Y-%m-%d')
                    if iso_date not in file_dict.keys():
                        file_dict[iso_date] = [file_path]
                    elif iso_date in file_dict.keys() and file_dict[iso_date] != file_path: 
                        file_dict[iso_date].append(file_path)
    
    for date in file_dict.keys():
        fgmdf = pd.DataFrame(data={'TIME':[],'BX':[],'BY':[],'BZ':[],'LAT':[]})
        save_date = datetime.datetime.strptime(date,'%Y-%m-%d')
        file_list = file_dict[date]
        for file in file_list:
            
            temp = pd.read_csv(file)
            datetime_list = temp['SAMPLE UTC']
            time_list = [datetime.datetime.fromisoformat(i).strftime('%H:%M:%S') for i in datetime_list]
            
            for index,time in enumerate(datetime_list):
                
                position, lighttime = spice.spkpos('JUNO',spice.utc2et(time),'IAU_JUPITER','NONE','JUPITER')
            
                vectorPos = spice.vpack(position[0],position[1],position[2])
                radii,longitude,latitude = spice.reclat(vectorPos)
                lat = latitude*spice.dpr()
                
                if lat >= -10 and lat <= 10:
                    fgmdf = fgmdf.append({'TIME':time,'BX':temp['BX PLANETOCENTRIC'][index],'BY':temp['BY PLANETOCENTRIC'][index],'BZ':temp['BZ PLANETOCENTRIC'][index],'LAT':lat},ignore_index=True)
        fgmdf = fgmdf.sort_values(by=['TIME'])
        save_name = f'{save_date.strftime("%Y%m%d")}'
        save_path = pathlib.Path(f'..\data\pickledfgm\jno_fgm_{save_name}.pkl')
        pickledf = fgmdf.to_pickle(save_path)
        print(f'Saved pickle {date}')                                     

if __name__ == '__main__':
    dataToCDF()
    
    
    
    
