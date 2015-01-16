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

import pyspherematch as pysm
from FITSFile import FITSFile

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

def findPointingAngleDiff(pointing1, pointing2):
    '''
    find great circle difference in degrees between two sets of ra/dec
    '''
    return pysm._great_circle_distance(pointing1[0], pointing1[1], pointing2[0], pointing2[1])

