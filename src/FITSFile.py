'''
name:		FITSFile.py
author:		rmb

description: 	A class to handle FITS files
'''

import os

import pyfits

from errors import errors

class FITSFile:
    def __init__(self, filepath, err):
        self.filePath	= filepath
	self.err	= err
	self.hduList	= None
	self.headers	= None
	self.data	= None
	self.fileOpen	= False

    def openFITSFile(self):
        '''
        check a FITS file exists and try to open it
        '''
	if os.path.exists(self.filePath):
            try:
                self.hduList = pyfits.open(self.filePath)
            except IOError:
                self.err.setError(11)
                self.err.handleError()  
                return False  
	    self.fileOpen = True
            return True
        else:
            self.err.setError(-1)
            self.err.handleError()
            return False

    def getHeaders(self, HDU):
        '''
        retrieve headers from a specified HDU
        '''
        if self.hduList is not None:
            self.headers = self.hduList[HDU].header
        else:
            self.err.setError(-2)
            self.err.handleError()
            return False

    def getData(self, HDU):
        '''
        get data from a specified HDU
        '''
        if self.hduList is not None:
            self.data = self.hduList[HDU].data
        else:
            self.err.setError(-3)
            self.err.handleError()
            return False       

    def closeFITSFile(self):
        '''
        close FITS file cleanly
        '''
        if self.hduList is not None:
            self.hduList.close()
	    self.fileOpen = False
            return True
        else:
            self.err.setError(-4)
            self.err.handleError()
            return False
