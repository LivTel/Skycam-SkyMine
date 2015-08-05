'''
name:		pysex.py
author:		rmb

description: 	A wrapper script for sExtractor
'''
import logging
import os, shutil

import asciidata

class pysex():
    ''' 
    bespoke skycam pipeline sExtractor class (based on pysex)
    '''
    def __init__(self, f, data_path, path_to_conf_file, err, logger):
        self.f = f
        self.data_path = data_path
        self.path_to_conf_file = path_to_conf_file
        self.catdata = None
        self.err = err
        self.logger = logger
        
    def _setup(self):
        # parse standard conf file into dict
        sEx_conf = {}
        with open(self.path_to_conf_file, 'r') as f:
            for line in f :
                key, value = line.rstrip('\n').split()
                sEx_conf[key] = value
        f.close()

        # check we're using the correct PARAMETERS file
        if not os.path.exists(sEx_conf["PARAMETERS_NAME"]):
            self.err.setError(-7)
            self.err.handleError()
        self.logger.info("(pysex._setup Using parameter file " + sEx_conf["PARAMETERS_NAME"])

        # append catalogue output file parameter based on data_path
        sEx_conf['CATALOG_NAME'] = self.data_path + ".pysex.cat"

        with open(self.data_path + ".pysex.sex", 'w') as f:
            for key, val in sEx_conf.iteritems():
                f.write(key + ' ' + val + '\n')

    def _get_cmd(self):
        cmd = 'sex ' + str(self.f) + ' -c ' + str(self.data_path) + '.pysex.sex'
        return cmd

    def _cleanup(self):
        files = [f for f in os.listdir(self.data_path) if '.pysex.' in f]
        for f in files:
            os.remove(self.data_path + f)

    def _read_cat(self):
        catdata = asciidata.open(self.data_path + '.pysex.cat')
        return catdata

    def run(self):
        self._setup()
        cmd = self._get_cmd()
        res = os.system(cmd)
        if res:
            self.err.setError(-17)
            self.err.handleError()
            _cleanup(image)
            return False

        self.catdata = self._read_cat()
        self._cleanup()

    def write_cat(self, path):
        '''
        write sExtractor catalogue to file
        '''
        self.logger.info("(pysex.write_cat) Writing sExtractor catalogue to " + path)
        self.catdata.writeto(path)

        return True


