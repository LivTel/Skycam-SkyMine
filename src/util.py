'''
name:		util.py
author:		rmb

description: 	Utility functions
'''

import os
import logging
import subprocess as sp
import time
from time import mktime
import ConfigParser
import math
import tarfile

import pyspherematch as pysm
from FITSFile import FITSFile

def compress_files(files, outFilename, logger):
    '''
    gzip list of files
    '''
    tar_outFilename = outFilename + ".tar"
    for idx, f in enumerate(files):
        logger.info("(compress_files) Compressing file " + f)
        if idx is 0:
             if sp.call(["tar", "-cf", tar_outFilename, f]):
                 return False
        else:
             if sp.call(["tar", "-rf", tar_outFilename, f]):
                 return False

    if sp.call(["gzip", tar_outFilename]):
        return False

def decompress_files(path, logger):
    '''
    decompress .gz files in directory
    '''
    for f in os.listdir(path):
        if f.endswith(".fits.gz"):
    	    logger.info("(decompress_files) Decompressing file " + f)
            if sp.call(["gunzip", path + f]):
                return False

    return True
  
def dms_2_deg(DMS):
    return (float(DMS.split(':')[0])) + (float(DMS.split(':')[1])*(1./60.)) + (float(DMS.split(':')[2])*(1./3600.)); 
      
def find_pointing_angle_diff(pointing1, pointing2):
    '''
    find great circle difference in degrees between two sets of ra/dec
    '''
    return pysm._great_circle_distance(pointing1[0], pointing1[1], pointing2[0], pointing2[1])
  
def hms_2_deg(HMS):
    return (float(HMS.split(':')[0])*15.) + (float(HMS.split(':')[1])*(15./60.)) + (float(HMS.split(':')[2])*(15./3600.));

def read_password_file(pwFile, idToLookFor):
    with open(pwFile) as f:
        for line in f:
            if not line.startswith('#'):
                this_id = line.split()[0].strip('\n')
                if this_id == idToLookFor:
                    this_host = line.split()[1].strip('\n')
                    this_port = line.split()[2].strip('\n')
                    this_user = line.split()[3].strip('\n')
                    this_pw = line.split()[4].strip('\n')
                    return this_host, this_port, this_user, this_pw
    return None

def read_ini(path):
    ini = ConfigParser.ConfigParser()
    ini.read(path)
    cfg = {}
    for section in ini.sections():
        cfg[section] = {}
        for option in ini.options(section):
            cfg[section][option] = str(ini.get(section, option))  
    return cfg
  
def sf(num, sig_figs):
    try:
        rtn = round(num, -int(math.floor(math.log10(abs(num))) - (sig_figs - 1)))
        return rtn
    except ValueError:
        return 0.    

def sort_image_directory_UTC(path, err, logger):
    '''
    return list of images in directory in order of ascending observation time (DATE-OBS)
    '''
    images = {}
    for f in os.listdir(path):
        if f.endswith(".fits"):
	    # open FITS image and get headers
            im = FITSFile(os.path.abspath(path + f), err) 
	    if im.openFITSFile():
                im.getHeaders(0)

                # convert DATE-OBS -> unix time and add file path / unix time to dict
                try:
                    thisTime = time.strptime(im.headers["DATE-OBS"], '%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    pass

                thisTimeUnix = mktime(thisTime)
                images[path + f] = thisTimeUnix
 
                # close FITS file
                im.closeFITSFile() 

    if images is None:
        return False
    else:
        # sort and return
        return sorted(images, key=images.get)

def zip_output_files_in_directory(path, archive_name, err, logger):
    '''
    zip all files in a directory
    '''  
    tar = tarfile.open(path + archive_name, "w")
    for name in os.listdir(path):
        if "tar" not in name:
            if name.endswith(".fits"):
                tar.add(path + name, arcname='datafiles/' + name)
            elif name.endswith(".png"):
                tar.add(path + name, arcname='img/' + name)  
            else:
                tar.add(path + name, arcname='other/' + name)  
    tar.close()



