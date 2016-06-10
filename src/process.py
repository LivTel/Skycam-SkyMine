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
from util import compress_files, decompress_files, sort_image_directory_UTC, sf, zip_output_files_in_directory
from archive import archive

class process():
    def __init__(self, params):
        self.params             = self._load_params(params)
        self.logger             = self._setup_logging()
        self.err                = self._setup_errors()
        self._add_stream_logging_handler()
        self._create_output_dir()
        self._add_file_logging_handler()
        
    def _add_file_logging_handler(self):
        # now that we have an res directory, add a file handler to logger object
        fh = logging.FileHandler(self.params['resPath'] + "log")
        fh.setLevel(logging.DEBUG)

        ## set logging format
        formatter = logging.Formatter("(" + str(os.getpid()) + ") %(asctime)s:%(levelname)s: %(message)s")
        fh.setFormatter(formatter)

        ## add handlers to logging object
        self.logger.addHandler(fh)
        
    def _add_stream_logging_handler(self):
        ## create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        ## set logging format
        formatter = logging.Formatter("(" + str(os.getpid()) + ") %(asctime)s:%(levelname)s: %(message)s")
        ch.setFormatter(formatter)

        ## add handlers to logging object
        self.logger.addHandler(ch)
        
    def _purge_output_dir(self, skipTarFiles=False):
        for i in os.listdir(self.params['resPath']): 
            if skipTarFiles and "tar" in i:
                continue
            os.remove(self.params['resPath'] + i)   
        
    def _create_output_dir(self):
        # create res directory to store metadata
        if os.path.exists(self.params['resPath']) is True:
            if self.params['clobber'] is True:
                self._purge_output_dir()
            else:
                self.err.setError(-13)
                self.err.handleError()
        else:
            os.mkdir(self.params['resPath'])
        
    def _load_params(self, in_params):
        # load and convert unicode json string into dict of strings
        params_unicode = json.loads(in_params)  # this returns a dict containing unicode instances
        params = {}
        ## convert unicode instances to strings, otherwise stuff breaks
        for key, value in params_unicode.iteritems():       
            key_safe = key.encode('utf-8') if isinstance(key, unicode) else key
            value_safe = value.encode('utf-8') if isinstance(value, unicode) else value
            params[key_safe] = value_safe
        return params

    def run_async(self):
        startProcessTime = time.time()
	if not self.params['skipArchive']:
            # retrieve images from lt-archive
            self.logger.info("(process.run_async) retrieving images from archive")
            ltarchive = archive(self.params['path_pw_list'], self.params['archive_credentials_id'], self.params['skycam_lup_db_credentials_id'], self.err, self.logger)
            
            ## search for images matching criteria
            MySQLLogFile = self.params['resPath'] + "skycamfiles"
            ltarchive.getMySQLLog(self.params['resPath'], "skycam", "skycam", self.params['dateFrom'], self.params['dateTo'], self.params['instrument'], MySQLLogFile) 
            
            ## get the data
            ltarchive.getData(MySQLLogFile, self.params['resPath'])
        else:
	    for f in os.listdir(self.params['tmpMockPath']):
                shutil.copyfile(self.params['tmpMockPath'] + str(f), self.params['resPath'] + str(f))
    
        # decompress and sort images by ascending datetime
        decompress_files(self.params['resPath'], self.err, self.logger)
        images = sort_image_directory_UTC(self.params['resPath'], self.err, self.logger)
        if not images:
            self.err.setError(-12)
            self.err.handleError()

	# START THE PIPELINE
        pipe = pipeline(self.params, self.err, self.logger)	# spawn pipeline instance
        pipe.run(images)					# and run for these images

        # log error code
        with open(self.params['resPath'] + 'res.exitcode', 'w') as f:
            f.write(str(self.err.getError()))
            
        # zip files in directory and purge res dir
        archive_name = self.params['dateFrom'].replace(" ", "T").replace("-", "").replace(":", "") + ".tar"
        zip_output_files_in_directory(self.params['resPath'], archive_name, self.err, self.logger)      
        self._purge_output_dir(skipTarFiles=True)

        elapsed = (time.time() - startProcessTime)
        self.logger.info("(process.run_async) child process finished in " + str(round(elapsed)) + "s")
        
    def run_sync(self):
        self.logger.info("(process.run_sync) starting synchronous process... ")
        
        pipe = pipeline(self.params, self.err, self.logger)
        
        UT_time_end_iter = time.time() - (60*3600)
        current_lag = 0
        while True:
            UT_time_end = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(UT_time_end_iter))  
            UT_time_st_iter = UT_time_end_iter - self.params['t_sync_check']             
            UT_time_st  = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(UT_time_st_iter)) 
            self.logger.info("(process.run_sync) searching for files between " + UT_time_st + " and " + UT_time_end)
           
            startProcessTime = time.time()

            try:            
                # retrieve latest images from lt-archive
                self.logger.info("(process.run) retrieving latest images from archive")
                ltarchive = archive(self.params['path_pw_list'], self.params['archive_credentials_id'], self.params['skycam_lup_db_credentials_id'], self.err, self.logger)
                
                ## search for images matching criteria
                MySQLLogFile = self.params['resPath'] + "res.skycamfiles"
                num_files = ltarchive.getMySQLLog(self.params['resPath'], "skycam", "skycam", UT_time_st, UT_time_end, self.params['instrument'], MySQLLogFile) 
                if num_files > 0:
                    ## get the data
                    ltarchive.getData(MySQLLogFile, self.params['resPath'])
            
                    # decompress and sort images by ascending datetime
                    decompress_files(self.params['resPath'], self.err, self.logger)
                    images = sort_image_directory_UTC(self.params['resPath'], self.err, self.logger)
                    if not images:
                        self.err.setError(-12)
                        self.err.handleError()
                        
                    # run pipeline
                    pipe.run(images) 
                      
                    # zip files in directory and purge res dir
                    archive_name = UT_time_st.replace(" ", "").replace("-", "").replace(":", "") + ".tar"
                    zip_output_files_in_directory(self.params['resPath'], archive_name, self.err, self.logger)        
                    self._purge_output_dir(skipTarFiles=True)
                else:
                    self.logger.info("(process.run_sync) no files found for this time range, continuing")
            except RuntimeError:
                self.err.setError(2)
                self.err.handleError()  
                
            elapsed = (time.time() - startProcessTime)
            if elapsed > self.params['t_sync_check']:   # we're lagging this iteration
                self.err.setError(13)
                self.err.handleError()
                
            current_lag = current_lag + (elapsed - self.params['t_sync_check'])
            if current_lag > 0:
                self.logger.info("(process.run_sync) processing is lagging by " + str(sf(current_lag, 2)) + "s")
            else:
                current_lag = 0 
                
            # wait some time before we query archive again, unless we're lagging
            time_to_wait = self.params['t_sync_check'] - elapsed - current_lag
            if time_to_wait > 0:
                time.sleep(time_to_wait)
                
            UT_time_end_iter = UT_time_end_iter + self.params['t_sync_check']
       
    def _setup_errors(self):
        # create error object
        err = errors(self.logger, self.params['daemon'])
        
        return err
        
    def _setup_logging(self):
        # set console logging
        logger = logging.getLogger('skycam_pipeline_process')
        logger.setLevel(logging.DEBUG)

        return logger
    
if __name__ == "__main__":              # this is the entry point for async operations
    this_run = process(sys.argv[1])
    this_run.run_async()

