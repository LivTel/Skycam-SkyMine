'''
name:		process.py
author:		rmb

description: 	A script to handle forked processes from run_pipe.py. Even 
		though it has a main function, it should never be 
		called directly.
'''
import os
import time
import logging
import json
import sys
import shutil

from errors import errors
from FITSFile import FITSFile
from pipeline import *
from util import compress_files, decompress_files, sort_image_directory_UTC
from archive import archive

class process():
    def __init__(self, params, err, logger):
        self.params = params
        self.err = err
        self.logger = logger

    def run(self):
        # create res directory to store metadata
        if os.path.exists(self.params['resPath']) is True:
            if self.params['clobber'] is True:
                for i in os.listdir(self.params['resPath']):    
                    os.remove(self.params['resPath'] + i)
                os.rmdir(self.params['resPath'])
            else:
                self.err.setError(-13)
                self.err.handleError()
        os.mkdir(self.params['resPath'])

        # now that we have an res directory, add a file handler to logger object
        fh = logging.FileHandler(self.params['resPath'] + "res.log")
        fh.setLevel(logging.DEBUG)

        ## set logging format
        formatter = logging.Formatter("(" + str(os.getpid()) + ") %(asctime)s:%(levelname)s: %(message)s")
        fh.setFormatter(formatter)

        ## add handlers to logging object
        logger.addHandler(fh)

        startProcessTime = time.time()

	if not self.params['skipArchive']:
            # retrieve images from lt-archive
            logger.info("(process.run) retrieving images from archive")
            ltarchive = archive(self.err, logger)
            ## search for images matching criteria
            MySQLLogFile = self.params['resPath'] + "res.skycamfiles"
            ltarchive.getMySQLLog(self.params['resPath'], "skycam", "skycam", self.params['dateFrom'], self.params['dateTo'], self.params['instrument'], MySQLLogFile) 
            ## get the data
            ltarchive.getData(MySQLLogFile, self.params['resPath'])
        else:
	    for f in os.listdir(params['tmpMockPath']):
                shutil.copyfile(params['tmpMockPath'] + str(f), self.params['resPath'] + str(f))
    
        # decompress and sort images by ascending datetime
        if not decompress_files(self.params['resPath'], logger):
            self.err.setError(-11)
            self.err.handleError()
        images = sort_image_directory_UTC(self.params['resPath'], self.err, logger)
        if not images:
            self.err.setError(-12)
            self.err.handleError()

	# START THE PIPELINE
        pipe = pipeline(images, self.params, self.err, logger)	# spawn pipeline instance
        pipe.run()						# and run

        # log result
        with open(self.params['resPath'] + 'res.exitcode', 'w') as f:
            f.write(str(self.err.getError()))

        # copy over web template to result directory
        shutil.copyfile(self.params['etcPath'] + "pipe/web_template.php", self.params['resPath'] + 'index.php')

        elapsed = (time.time() - startProcessTime)
        logger.info("(process.run) child process finished in " + str(round(elapsed)) + "s")

if __name__ == "__main__":
    # load and convert unicode json string into dict of strings
    params_unicode = json.loads(sys.argv[1])            # this returns a dict containing unicode instances
    params = {}
    ## convert unicode instances to strings, otherwise stuff breaks
    for key, value in params_unicode.iteritems():       
        key_safe = key.encode('utf-8') if isinstance(key, unicode) else key
        value_safe = value.encode('utf-8') if isinstance(value, unicode) else value
        params[key_safe] = value_safe

    # set console logging
    logger = logging.getLogger('skycam_pipeline_process')
    logger.setLevel(logging.DEBUG)

    ## create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    ## set logging format
    formatter = logging.Formatter("(" + str(os.getpid()) + ") %(asctime)s:%(levelname)s: %(message)s")
    ch.setFormatter(formatter)

    ## add handlers to logging object
    logger.addHandler(ch)

    # create error object
    err = errors(logger)

    this_run = process(params, err, logger)
    this_run.run()

