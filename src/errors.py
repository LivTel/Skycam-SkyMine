'''
name:		errors.py
author:		rmb

description: 	A class to handle errors
'''

import logging
import sys

class errors:
    '''
    a class for handling errors.
    '''
    def __init__(self, logger):
        self.logger		= logger
        self._errorCode		= 0
	self._errorCodeDict	= {0:"No errors encountered",
				   -1:"(FITSFile.openFITSFile) Unable to open FITS file. File not found", 
                                   -2:"(FITSFile.getHeaders) Unable to get headers",
                                   -3:"(FITSFile.getData) Unable to get data",
                                   -4:"(FITSFile.closeFITSFile) Unable to close file. File not open",
                                   -5:"(calibrate._extractSources) RA_CENT||DEC_CENT keyword doesn't exist in file header",
                                   -6:"(sExCatalogue.query) Config file doesn't exist",
                                   -7:"(sExCatalogue.query) Params file doesn't exist",
                                   -8:"(pipeline._extractSources) Insufficient images for calibration to be made",
                                   -9:"(pipeline._matchSources_USNOB1) matchedSources list is empty",
                                   -10:"(pipeline._extractSources) Purged all images",
                                   -11:"(pipe.run) Failed to decompress files",
                                   -12:"(pipe.run) Sorted image list is Nonetype. Probably no images found",
                                   -13:"(pipe.run) res directory already exists and clobber is not set",
                                   -14:"(database_*.execute) execute query failed",
				   1:"(pipeline._extractSources) Image doesn't have valid WCS, ignoring",              
                                   2:"(pipeline._extractSources) Image is first in list, ignoring",
                                   3:"(pipeline._extractSources) Pointing angle difference is too large, ignoring",
                                   4:"(pipeline._extractSources) Image has too few sources, ignoring",
                                   5:"(pipeline._extractSources) Image contains source with too long an elongation, ignoring",
                                   6:"(pipeline._extractSources) Image has object angles with too high an excess kurtosis, ignoring",
                                   7:"(pipeline._extractSources) Image has failed combined elongation/kurtosis check, ignoring",
                                   8:"(pipeline._extractSources) Image contains a source with too high a flux, ignoring",
                                   9:"(pipeline._extractSources) Image has no sources, ignoring",
                                   10:"(archive.getData) Failed to retrieve image from archive",
                                   11:"(FITSFile.openFITSFile) Header missing END card. Skipping file",
                                   12:"(pipeline) Image contains too few matched sources, ignoring"}

    def setError(self, newErrorCode):
        '''
        set internal error code
        '''
        self._errorCode = newErrorCode
        return True

    def getError(self):
        '''
        get internal error code
        '''
        return self._errorCode

    def handleError(self):
        '''
        handle internal error code
        '''
        errorMsg = self._errorCodeDict.get(self._errorCode)
        if self._errorCode is 0:
            self.logger.info(errorMsg)
        elif self._errorCode < 0:
            self.logger.critical(errorMsg)
            sys.exit(1)
        elif self._errorCode > 0:
            self.logger.warning(errorMsg)
