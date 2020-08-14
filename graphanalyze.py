#!/usr/bin/env python3

import sys, os, pathlib, re, datetime, pyautogui
from PIL import Image
from pynput import mouse
from pyhooked import Hook, KeyboardEvent, MouseEvent

def analyze():    
        
    #pic_folder = pathlib.Path('../figures/orbit6')
    #pics = os.listdir(pic_folder)
    #pic_paths = [os.path.join(pic_folder,pic) for pic in pics]
    #pic_num = 0    

    #graph = Image.open(pic_paths[pic_num])
    #graph.show()
    
    #graphArea = 0
    
    


    def handle_events(args):
        if isinstance(args, KeyboardEvent):
            print(args.key_code)
            if args.current_key == 'A' and args.event_type == 'key down' and 'Lcontrol' in args.pressed_key:
                print("Ctrl + A was pressed")
            elif args.current_key == 'Q' and args.event_type == 'key down' and 'Lcontrol' in args.pressed_key:
                hk.stop()
                print('Quitting.')
                

        if isinstance(args, MouseEvent):
            if args.current_key == 'LButton' and args.event_type == 'key down' in args:
                print('Clicked') 

    hk = Hook()  # make a new instance of PyHooked
    hk.handler = handle_events  # add a new shortcut ctrl+a, or triggered on mouseover of (300,400)
    hk.hook()  # hook into the events, and listen to the presses


if __name__ == '__main__':

    analyze()