'''
name:		ws.py
author:		rmb

description: 	wrappers to talk to webservices
'''
import requests
import urllib
import json

class ws_catalogue:
    def __init__(self, ip, port, err, logger):
        self.ip         = ip
        self.port       = port
        self.err	= err
        self.logger	= logger
        self.status     = None
        self.text       = None
        
    def SCS(self, catalogue, ra, dec, sr, mag_col, mag_bright_lim, mag_faint_lim, order_col, max_sources, output_format):
        req = requests.get('http://' + str(self.ip) + ':' + str(self.port) + '/scs/' + str(catalogue) + '/' + str(ra) 
                           + '/' + str(dec) + '/' + str(sr) + '/' + mag_col + '/' + str(mag_bright_lim) + '/' 
                           + str(mag_faint_lim) + '/' + order_col + '/' + str(max_sources) + '/' + output_format) 
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code
        
    def skycam_catalogue_add_to_buffer(self, schema, sources): 
        req = requests.put('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/catalogue/buffer/' + schema + '/' + json.dumps(sources)) 
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code       
        
    def skycam_catalogue_flush_buffer_to_db(self, schema):    
        req = requests.post('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/catalogue/buffer/' + schema)    
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code         
                 
    def skycam_catalogue_insert(self, schema, values):
        req = requests.post('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/catalogue/' + schema + '/' + json.dumps(values))    
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code        
            
    def skycam_images_get_by_filename(self, schema, filename):
        req = requests.get('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/images/' + schema + '/filename/' + filename)    
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code
        
    def skycam_images_insert(self, schema, values, filename):
        req = requests.post('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/images/' + schema + '/' + json.dumps(values))    
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code
                
    def skycam_sources_add_to_buffer(self, schema, sources): 
        req = requests.put('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/sources/buffer/' + schema + '/' + json.dumps(sources)) 
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code       
        
    def skycam_sources_flush_buffer_to_db(self, schema):    
        req = requests.post('http://' + str(self.ip) + ':' + str(self.port) + '/skycam/tables/sources/buffer/' + schema)    
        if req.status_code == 200:
            self.text   = req.text
        else:
            self.text   = None
        self.status = req.status_code         
    
            