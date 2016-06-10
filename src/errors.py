'''
name:		errors.py
author:		rmb

description: 	A class to handle errors
'''

import logging
import sys

class errors:
    def __init__(self, logger, isDaemon):
        self.logger		= logger
        self.isDaemon           = isDaemon
        self._errorCode		= 0
	self._errorCodeDict	= {0:"No errors encountered",
				   -1:"(FITSFile.openFITSFile) Unable to open FITS file. File not found", 
                                   -2:"(FITSFile.getHeaders) Unable to get headers",
                                   -3:"(FITSFile.getData) Unable to get data",
                                   -4:"(FITSFile.closeFITSFile) Unable to close file. File not open",
                                   -5:"",
                                   -6:"(catalogue.sExCatalogue.query) Config file doesn't exist",
                                   -7:"(catalogue.sExCatalogue.query) Params file doesn't exist",
                                   -8:"",
                                   -9:"",
                                   -10:"",
                                   -11:"",
                                   -12:"(process.run_*) Sorted image list is Nonetype. Probably no images found",
                                   -13:"(process._create_output_dir) res directory exists but clobber is not set",
                                   -14:"(database_*.execute) execute query failed",
                                   -15:"(archive.__init__) Password list not found",
                                   -16:"(archive.__init__) Archive credentials not found in password file",
                                   -17:"(catalogue.*Catalogue.__init__) Password list not found",
                                   -18:"(catalogue.*Catalogue.__init__) Catalogue credentials not found in password file",
                                   -19:"(pipeline._storeToPostgresDatabase) Password list not found",
                                   -20:"(pipeline._storeToPostgresDatabase) Catalogue credentials not found in password file",
                                   -21:"(archive.__init__) Skycam lookup database credentials not found in password file",
				   1:"(pipeline._extractSources) Image doesn't have valid WCS, ignoring",              
                                   2:"(process.run_sync) Iteration raised a CRITICAL fault, ignoring",
                                   3:"(pipeline._extractSources) Pointing angle difference is too large, ignoring",
                                   4:"(pipeline._extractSources) Image has too few sources, ignoring",
                                   5:"(pipeline._extractSources) Image contains source with too long an elongation, ignoring",
                                   6:"(pipeline._extractSources) Image has object angles with too high an excess kurtosis, ignoring",
                                   7:"(pipeline._extractSources) Image has failed combined elongation/kurtosis check, ignoring",
                                   8:"(pipeline._extractSources) Image contains a source with too high a flux, ignoring",
                                   9:"(pipeline._extractSources) Image has no sources, ignoring",
                                   10:"(archive.getData) Failed to retrieve image(s) from archive",
                                   11:"(FITSFile.openFITSFile) Header missing END card. Skipping file",
                                   12:"(pipeline._XMatchSources) Image contains too few matched sources, ignoring",
                                   13:"(process.run_sync) Processing time is longer than sync check time",
                                   14:"(pipeline.run) No valid images found for this run",
                                   15:"(ws.*) Web service did not return a status code of 200",
                                   16:"(pipeline._XMatchSources_*) matchedSources list is empty",
                                   17:"(pipeline._XMatchSources) Query returned no sources",
                                   18:"(pipeline._storeToPostgresDatabase) Image already processed, ignoring",
				   19:"(util.decompress_files) Failed to decompress a file"
                                   }

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
            if self.isDaemon:
                raise RuntimeError
            else:
                sys.exit(1)
        elif self._errorCode > 0:
            self.logger.warning(errorMsg)
