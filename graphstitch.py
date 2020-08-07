#!/usr/bin/env python3

import sys, os, pathlib, re, datetime

def stitch():
    pic_path1 = pathlib.Path('D:/Python/Juno Folder/figures/orbit6')
    pic_path2 = pathlib.Path("D:/Python/Juno Folder/figures/species/plot")
    
    file_dict = {}
    for parent,child,files in os.walk(pic_path1):
        for file in files:
            file_path = os.path.join(parent,file)

            date = datetime.datetime.strptime(file[8:-4],'%Y%j_%H%M').strftime('%Y-%jT%H')
            file_dict[date] = [file_path]
    
    for parent,child,files in os.walk(pic_path2):
        for file in files:
            file_path = os.path.join(parent,file)

            date = datetime.datetime.strptime(file[40:51],'%Y-%jT%H').strftime('%Y-%jT%H')

            if date in file_dict.keys():
                file_dict[date].append(file_path)
    
    for date,paths in file_dict.items():
        if len(paths) >= 2:
            print(f'convert {paths[0]} {paths[1]} -append jno_{date}.png')


if __name__ == '__main__':
    stitch()



