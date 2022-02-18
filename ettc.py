# -*- coding: utf-8 -*-
"""
Created on Fri Oct  2 15:48:20 2020

@author: wardc
"""

import datetime
import time

#%
cycles=20
delay=1



ETTC={
      'start_time':datetime.datetime.now(),
      'total':cycles,
      'counter':0
      }

for i in range(cycles): ##remove the comments when ready for looping

    ETTC['cur_time']=datetime.datetime.now()
    ETTC['el_time']=(ETTC['cur_time']-ETTC['start_time']).seconds
    
    if ETTC['counter']==0:
        print('PROGRESS: {:.2F}% - ETC: {} of {} seconds - File {} of {}'.format(0,'????','????',ETTC['counter'],ETTC['total']))
        ETTC['counter']+=1
    else:
        ETTC['ettc']=(ETTC['el_time']/(ETTC['counter']/ETTC['total']))-ETTC['el_time']
        print('PROGRESS: {:.2F}% - ETC: {:.2F} remaining of {:.2F} seconds - File {:.0F} of {:.0F}'.format(
                ETTC['counter']/ETTC['total']*100,
                ETTC['ettc'],
                (ETTC['el_time']/(ETTC['counter']/ETTC['total'])),
                ETTC['counter'],
                ETTC['total']
                ))
        ETTC['counter']+=1
    
    time.sleep(delay)

ETTC['cur_time']=datetime.datetime.now()
ETTC['el_time']=(ETTC['cur_time']-ETTC['start_time']).seconds

    
ETTC['ettc']=(ETTC['el_time']/(ETTC['counter']/ETTC['total']))/60-ETTC['el_time']
print('PROGRESS: {:.2F}% - ETC: {:.2F} remaining of {:.2F} seconds - File {:.0F} of {:.0F}'.format(
                ETTC['counter']/ETTC['total']*100,
                0,
                (ETTC['el_time']/(ETTC['counter']/ETTC['total'])),
                ETTC['counter'],
                ETTC['total']
                ))