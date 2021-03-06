'''
name:		database.py
author:		rmb

description: 	A lightweight class to abstract basic database interaction
'''
import logging
import time

import MySQLdb
import psycopg2

from errors import errors

class database_mysql:
    '''
    a class for interacting with a mysql database
    '''
    def __init__(self, host, user, password, database, err):
        self.host 	= host
        self.user 	= user
        self.password 	= password
        self.database	= database
        self.err	= err

    def connect(self):
	self.db = MySQLdb.connect(self.host, self.user, self.password, self.database)

    def read(self, query):
        cursor = self.db.cursor()
        cursor.execute(query)
	return cursor

    def execute(self, query, retry=10):
        cursor = self.db.cursor()
        status = False
        for attempt in range(retry):
            try:
                cursor.execute(query)
                self.db.commit()
                status = True
                break
            except MySQLdb.Error, e:
                self.db.rollback()
                print e
                time.sleep(1)

        if status:
	    return cursor
        else:
            self.err.setError(-14)
            self.err.handleError()

    def close(self):
	self.db.close()

class database_postgresql:
    '''
    a class for interacting with a postgresql database
    '''
    def __init__(self, host, port, user, password, database, err):
        self.host 	= host
        self.port	= port
        self.user 	= user
        self.password 	= password
        self.database	= database
        self.err	= err

    def connect(self):
	self.db = psycopg.connect("dbname='" + self.database + "' port='" + str(self.port) + "' user='" + self.user + "' host='" + self.host + "' password='" + self.password + "'")

    def read(self, query):
        cursor = self.db.cursor()
        cursor.execute(query)
	return cursor

    def execute(self, query):
        cursor = self.db.cursor()
        try:
            cursor.execute(query)
            self.db.commit()
        except psycopg.Error, e:
            self.db.rollback()
            print e
            self.err.setError(-14)
            self.err.handleError()
	return cursor

    def create_schema(self, name):
        cmd = "CREATE SCHEMA " + name
        self.execute(cmd)

    def drop_schema(self, name):
        cmd = "DROP SCHEMA " + name + " cascade"
        self.execute(cmd)

    def check_schema_exists(self, name):
        cmd = "SELECT count(*) FROM information_schema.schemata WHERE schema_name = '" + name +"'"
        res = self.read(cmd)
        return res.fetchone()[0]

    def create_index(self, table, column, indexName, spatial=False):
        if spatial:
             cmd = "CREATE INDEX " + indexName + " ON " + table + " USING GIST(" + column + ")"
        else:
             cmd = "CREATE INDEX " + indexName + " ON " + table + " (" + column + ")"
        res = self.execute(cmd)

    def drop_index(self, indexName):
        cmd = "DROP INDEX IF EXISTS " + indexName
        res = self.execute(cmd)

    def close(self):
	self.db.close()

