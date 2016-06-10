'''
name:		ws.py
author:		rmb

description: 	wrappers to talk to webservices
'''
import requests
from requests.exceptions import ConnectionError
import urllib
import json
import time

class ws_catalogue:
    def __init__(self, ip, port, err, logger, max_retries=5, retry_delay=5):
        self.ip         = ip
        self.port       = port
        self.err	= err
        self.logger	= logger
        self.status     = None
        self.text       = None
        self.max_retries = 5
        self.retry_delay = 20
        self.timeout     = 180
        
    def SCS(self, catalogue, ra, dec, sr, mag_col, mag_bright_lim, mag_faint_lim, order_col, max_sources, output_format):
        conn_retry_count = 1
        while conn_retry_count <= self.max_retries:
            try:
                req = requests.get('http://' + str(self.ip) + ':' + str(self.port) + '/scs/' + str(catalogue) + '/' + str(ra) 
                                   + '/' + str(dec) + '/' + str(sr) + '/' + mag_col + '/' + str(mag_bright_lim) + '/' 
                                   + str(mag_faint_lim) + '/' + order_col + '/' + str(max_sources) + '/' + output_format, timeout=self.timeout)   
		break
	    except:
	      	self.logger.warning("(ws.SCS) Webservice connection error (" + str(conn_retry_count) + "/" + str(self.max_retries) + "), retrying in " + str(self.retry_delay) + "s")
	        time.sleep(self.retry_delay)
	    conn_retry_count = conn_retry_count + 1
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code
        
    def skycam_catalogue_add_to_buffer(self, uuid, values): 
        conn_retry_count = 1
        while conn_retry_count <= self.max_retries:
	    try:
                req = requests.put('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/catalogue/buffer/' + uuid, json=values) 
                break
	    except ConnectionError:
	      	self.logger.warning("(ws.skycam_catalogue_add_to_buffer) Webservice connection error (" + str(conn_retry_count) + "/" + str(self.max_retries) + "), retrying in " + str(self.retry_delay) + "s")
	        time.sleep(self.retry_delay)
	    conn_retry_count = conn_retry_count + 1
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code       
        
    def skycam_catalogue_flush_buffer_to_db(self, schema, uuid):   
        conn_retry_count = 1
        while conn_retry_count <= self.max_retries:
	    try:
                req = requests.post('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/catalogue/buffer/' + schema + '/' + uuid)  
                break
	    except ConnectionError:
	      	self.logger.warning("(ws.skycam_catalogue_flush_buffer_to_db) Webservice connection error (" + str(conn_retry_count) + "/" + str(self.max_retries) + "), retrying in " + str(self.retry_delay) + "s")
	        time.sleep(self.retry_delay)
	    conn_retry_count = conn_retry_count + 1
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code         
                 
    def skycam_catalogue_insert(self, schema, values):
        conn_retry_count = 1
        while conn_retry_count <= self.max_retries:
	    try:
                req = requests.post('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/catalogue/' + schema, json=values)  
                break
	    except ConnectionError:
	      	self.logger.warning("(ws.skycam_catalogue_insert) Webservice connection error (" + str(conn_retry_count) + "/" + str(self.max_retries) + "), retrying in " + str(self.retry_delay) + "s")
	        time.sleep(self.retry_delay)
	    conn_retry_count = conn_retry_count + 1  
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code     
        
    def skycam_flush_buffers_by_uuid_to_db(self, schema, img_id, uuid):    
        conn_retry_count = 1
        while conn_retry_count <= self.max_retries:
	    try:
                req = requests.post('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/transactions/flush/' + schema + '/' + img_id + '/' + uuid)
                break
	    except ConnectionError:
	      	self.logger.warning("(ws.skycam_flush_two_buffers_to_db) Webservice connection error (" + str(conn_retry_count) + "/" + str(self.max_retries) + "), retrying in " + str(self.retry_delay) + "s")
	        time.sleep(self.retry_delay)
	    conn_retry_count = conn_retry_count + 1             
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code         
      
    def skycam_images_get_by_filename(self, schema, filename):
        conn_retry_count = 1
        while conn_retry_count <= self.max_retries:
	    try:
                req = requests.get('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/images/' + schema + '/filename/' + filename)  
                break
	    except ConnectionError:
	      	self.logger.warning("(ws.skycam_images_get_by_filename) Webservice connection error (" + str(conn_retry_count) + "/" + str(self.max_retries) + "), retrying in " + str(self.retry_delay) + "s")
	        time.sleep(self.retry_delay)
	    conn_retry_count = conn_retry_count + 1     
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code
        
    def skycam_images_insert(self, schema, values):
        conn_retry_count = 1
        while conn_retry_count <= self.max_retries:
	    try:
                req = requests.post('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/images/' + schema, json=values)
                break
	    except ConnectionError:
	      	self.logger.warning("(ws.skycam_images_insert) Webservice connection error (" + str(conn_retry_count) + "/" + str(self.max_retries) + "), retrying in " + str(self.retry_delay) + "s")
	        time.sleep(self.retry_delay)
	    conn_retry_count = conn_retry_count + 1                 
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code        
                
    def skycam_sources_add_to_buffer(self, uuid, values): 
        conn_retry_count = 1
        while conn_retry_count <= self.max_retries:
	    try:
                req = requests.put('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/sources/buffer/' + uuid, json=values) 
                break
	    except ConnectionError:
	      	self.logger.warning("(ws.skycam_sources_add_to_buffer) Webservice connection error (" + str(conn_retry_count) + "/" + str(self.max_retries) + "), retrying in " + str(self.retry_delay) + "s")
	        time.sleep(self.retry_delay)
	    conn_retry_count = conn_retry_count + 1                       
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code       
        
    def skycam_sources_flush_buffer_to_db(self, schema, uuid):    
        conn_retry_count = 1
        while conn_retry_count <= self.max_retries:
	    try:
                req = requests.post('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/sources/buffer/' + schema + '/' + uuid)
                break
	    except ConnectionError:
	      	self.logger.warning("(ws.skycam_sources_flush_buffer_to_db) Webservice connection error (" + str(conn_retry_count) + "/" + str(self.max_retries) + "), retrying in " + str(self.retry_delay) + "s")
	        time.sleep(self.retry_delay)
	    conn_retry_count = conn_retry_count + 1             
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code         
    
            
