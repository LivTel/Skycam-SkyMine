'''
name:		ltarchive.py
author:		rmb

description: 	A class to talk to lt-archive
'''

import subprocess
import os
import paramiko
import logging
from errors import errors
import uuid

class archive:
    '''
    a class for querying lt-archive
    '''
    def __init__(self, err, logger):
        self.ip 	= "lt-archive"
        self.port 	= 22
        self.username	= "data"
        self.password 	= "ng@tdata"
        self.err	= err
        self.logger	= logger

    def SSHquery(self, query):
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
    
            client.connect(self.ip, port=self.port, username=self.username, password=self.password)
 
            stdin, stdout, stderr = client.exec_command(query)
            exit_status = stdout.channel.recv_exit_status()
            #stdout.read()
        finally:
            client.close()

    def getMySQLLog(self, resDir, mySQLUser, mySQLPass, dateFrom, dateTo, instrument, outputFilename):
        '''
        retrieve skycam MySQL log
        '''
        thisLogPath = '/tmp/skycam.' + str(uuid.uuid4()) + '.' + os.path.basename(resDir.rstrip('/'))

        # generate log
        self.logger.info("(archive.getMySQLLog) running MySQL query on archive")
        query = 'mysql skycam -u ' + mySQLUser + ' --password=' + mySQLPass + ''' -e 'SELECT __filename as filename, `DATE-OBS` as date FROM fitsheaders WHERE (str_to_date(`DATE-OBS`, "%Y-%m-%dT%H:%i:%s") between "''' + dateFrom + '" and "' + dateTo + '") AND (INSTRUME = "' + instrument + '") ORDER BY date ASC INTO OUTFILE "' + thisLogPath + '''" fields terminated by ",";' '''
        self.SSHquery(query)

        # retrieve log
        try:
            t = paramiko.Transport((self.ip, self.port))
            t.connect(username=self.username, password=self.password)
            self.logger.info("(archive.getMySQLLog) retrieving MySQL log from archive")
            sftp = paramiko.SFTPClient.from_transport(t)
            sftp.get(thisLogPath, outputFilename)
        finally:
            t.close()

    def getData(self, pathToMySQLLog, pathToDataDir):
        '''
        get data from archive using information from the log

        n.b. this has a hard-coded path to the data on lt-archive
        '''
        try:
            t = paramiko.Transport((self.ip, self.port))
            t.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(t)
 
            f = open(pathToMySQLLog, 'r')
            for line in f:
                thisFilename = line.split(',')[0]
                thisDate = line.split(',')[1].split('T')[0]
                thisYear = thisDate.split('-')[0]
                thisMonth = thisDate.split('-')[1]
                thisDay = thisDate.split('-')[2]

                thisFilePathOnArchive = "/mnt/newarchive1/lt/Skycam/" + thisYear + "/" + thisYear + thisMonth + thisDay + "/" + thisFilename + ".fits.gz"

                self.logger.info("(archive.getData) retrieving image " + thisFilePathOnArchive)
                try:
                    sftp.get(thisFilePathOnArchive, pathToDataDir + thisFilename + ".fits.gz")
                except IOError:
                    self.err.setError(10)
                    self.err.handleError()    
        finally:
            t.close()
    
