'''
name:		ws.py
author:		rmb

description: 	class to talk to webservices
'''
import requests

class ws_catalogue:
    def __init__(self, err, logger):
        self.err	= err
        self.logger	= logger
        self.status     = None
        self.text       = None
        
    def do_SCS(self, ip, port, catalogue, ra, dec, sr, mag_col, mag_bright_lim, mag_faint_lim, order_col, max_sources, output_format):
        req = requests.get('http://' + str(ip) + ':' + str(port) + '/scs/' + str(catalogue) + '/' + str(ra) 
                           + '/' + str(dec) + '/' + str(sr) + '/' + mag_col + '/' + str(mag_bright_lim) + '/' 
                           + str(mag_faint_lim) + '/' + order_col + '/' + str(max_sources) + '/' + output_format)    

        if req.status_code == 200:
            self.text   = req.text
        else:
            self.err.setError(15)
            self.err.handleError()
            self.status = req.status_code
