# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 14:53:32 2017

@author: Robert Voorheis
"""

from distutils.core import setup
import py2exe

wd_path = 'C:\\Users\\Joe Vandagriff\\.conda\\envs\\py34\\lib\\site-packages\\selenium\\webdriver'
required_data_files = [('selenium/webdriver/firefox',
                    ['{}\\firefox\\webdriver.xpi'.format(wd_path), 
                     '{}\\firefox\\webdriver_prefs.json'.format(wd_path)])]

setup(
    console= {"amz-qty.py"},
    data_files = required_data_files,
    options = {
           "py2exe":{
                    "skip_archive": True,
                    "unbuffered": True,
                    'optimize': 2
                    }
           },
    requires=['selenium'],
)
