'''
name:		archive.py
author:		rmb

description: 	A class to talk to lt-archive
'''
import subprocess
import os
import logging

import paramiko
import uuid

from errors import errors
from util import read_password_file as rpf

class archive:
    def __init__(self, pw_file, archive_pw_file_id, skycam_lup_pw_file_id, err, logger):
        self.err	= err
        self.logger	= logger
        # archive
        try:
            self.archive_ip, self.archive_port, self.archive_username, self.archive_password = rpf(pw_file, archive_pw_file_id);
            self.archive_port = int(self.archive_port)
        except IOError:
            self.err.setError(-15)
            self.err.handleError()       
        except TypeError:
            self.err.setError(-16)
            self.err.handleError()    
            
        # skycam lookup
        try:
            tmp, tmp, self.sky_lup_username, self.sky_lup_password = rpf(pw_file, skycam_lup_pw_file_id);
        except IOError:
            self.err.setError(-15)
            self.err.handleError()       
        except TypeError:
            self.err.setError(-21)
            self.err.handleError()
            
    def SSHquery(self, query):
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
    
            client.connect(self.archive_ip, port=self.archive_port, username=self.archive_username, password=self.archive_password)
 
            stdin, stdout, stderr = client.exec_command(query)
            exit_status = stdout.channel.recv_exit_status()
            #stdout.read()
        finally:
            client.close()

    def getMySQLLog(self, resDir, mySQLUser, mySQLPass, dateFrom, dateTo, instrument, outputFilename):
        '''
        retrieve skycam MySQL log
        
        returns the number of lines in the resulting log file
        '''
        thisLogPath = '/tmp/skycam.' + str(uuid.uuid4()) + '.' + os.path.basename(resDir.rstrip('/'))

        # generate log
        self.logger.info("(archive.getMySQLLog) running MySQL query on archive")
        query = 'mysql skycam -u ' + self.sky_lup_username + ' --password=' + self.sky_lup_password + ''' -e 'SELECT __filename as filename, `DATE-OBS` as date FROM fitsheaders WHERE (str_to_date(`DATE-OBS`, "%Y-%m-%dT%H:%i:%s") between "''' + dateFrom + '" and "' + dateTo + '") AND (INSTRUME = "' + instrument + '") ORDER BY date ASC INTO OUTFILE "' + thisLogPath + '''" fields terminated by ",";' '''
        self.SSHquery(query)

        # retrieve log
        try:
            t = paramiko.Transport((self.archive_ip, self.archive_port))
            t.connect(username=self.archive_username, password=self.archive_password)
            self.logger.info("(archive.getMySQLLog) retrieving MySQL log from archive")
            sftp = paramiko.SFTPClient.from_transport(t)
            sftp.get(thisLogPath, outputFilename)
        finally:
            t.close()
            
        return sum(1 for line in open(outputFilename))
            
    def getData(self, pathToMySQLLog, pathToDataDir):
        '''
        get data from archive using information from the log

        n.b. this has a hard-coded path to the data on lt-archive
        '''
        try:
            t = paramiko.Transport((self.archive_ip, self.archive_port))
            t.connect(username=self.archive_username, password=self.archive_password)
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
    
