'''
name:		catalogue.py
author:		rmb

description: 	Catalogue classes
'''
import subprocess
import os
import json

import asciidata
import pywcs

from errors import errors
from FITSFile import FITSFile
from pysex import pysex
from database import database_postgresql
from util import read_password_file as rpf
from ws import ws_catalogue as wsc

class Catalogue():
    def __init__(self):  
        self.NAME = []
        self.REF = []
        self.RA = []
        self.DEC = [] 
        
    def insert(self):
        pass
      
    def query(self):
        pass

class APASSCatalogue(Catalogue):
    def __init__(self, err, logger):
        Catalogue.__init__(self) 
        self.NAME = "APASS"
        self.RAERR = []
        self.DECERR = []  
        self.VMAG = []  
        self.BMAG = []          
        self.GMAG = []
        self.RMAG = []  
        self.IMAG = []    
        self.VMAGERR = []
        self.BMAGERR = []
        self.GMAGERR = []
        self.RMAGERR = [] 
        self.IMAGERR = []   
        self.NOBS = []
        self.err = err
        self.logger = logger
        
    def insert(self, apassref, ra, dec, raerr, decerr, vmag, bmag, gmag, rmag, imag, vmagerr, bmagerr, gmagerr, rmagerr, imagerr, nobs):
        '''
        insert APASS object into catalogue
        '''
        self.REF.append(apassref)
        self.RA.append(ra)    
        self.DEC.append(dec)
        self.RAERR.append(raerr)    
        self.DECERR.append(decerr)        
        self.VMAG.append(vmag) 
        self.BMAG.append(bmag)          
        self.GMAG.append(gmag)  
        self.RMAG.append(rmag)
        self.IMAG.append(imag)    
        self.VMAGERR.append(vmagerr)    
        self.GMAGERR.append(gmagerr)
        self.BMAGERR.append(bmagerr)    
        self.RMAGERR.append(rmagerr)
        self.IMAGERR.append(imagerr)    
        self.NOBS.append(nobs)

    def query(self, pw_file, pw_file_id, raDeg, decDeg, searchRadius, limitingMag, maxNumSourcesXMatch, appendToCat=True):
        ''' 
        do SCS on APASS catalogue
        '''
        try:
            ip, port, username, password = rpf(pw_file, pw_file_id)
            port = int(port)
        except IOError:
            self.err.setError(-17)
            self.err.handleError()       
        except TypeError:
            self.err.setError(-18)
            self.err.handleError()  
            
        # ws call outputs json
        ws_cat = wsc(ip, port, self.err, self.logger)
        ws_cat.SCS(self.NAME.lower(), raDeg, decDeg, searchRadius, 'rmag', -1, limitingMag, 'distance', maxNumSourcesXMatch, 'json')
        
        # append to internal catalogue
        if ws_cat.text is not None:
            if appendToCat:        
                for entry in json.loads(ws_cat.text): 
                    try:
                        APASSREF    = str(entry['apassref'])
                        RA          = float(entry['ra'])
                        DEC         = float(entry['dec'])
                        RAERR       = float(entry['raerrasec'])
                        DECERR      = float(entry['decerrasec'])
                        VMAG        = float(entry['vmag'])
                        BMAG        = float(entry['bmag'])
                        GMAG        = float(entry['gmag'])
                        RMAG        = float(entry['rmag'])
                        IMAG        = float(entry['imag'])
                        VMAGERR     = float(entry['verr'])
                        BMAGERR     = float(entry['berr'])
                        GMAGERR     = float(entry['gerr'])
                        RMAGERR     = float(entry['rerr'])
                        IMAGERR     = float(entry['ierr'])
                        NOBS        = int(entry['nobs'])
                        self.insert(apassref=APASSREF, ra=RA, dec=DEC, raerr=RAERR, decerr=DECERR, vmag=VMAG, bmag=BMAG, gmag=GMAG, rmag=RMAG, imag=IMAG, 
                                    vmagerr=VMAGERR, bmagerr=BMAGERR, gmagerr=GMAGERR, rmagerr=RMAGERR, imagerr=IMAGERR, nobs=NOBS)
                    except ValueError: 
                        continue        
                      
class SkycamCatalogue(Catalogue):
    def __init__(self, err, logger, schema):
        Catalogue.__init__(self) 
        self.NAME = schema
        self.RAERR = []
        self.DECERR = []  
        self.APASSREF = []  
        self.USNOBREF = []          
        self.NOBS = []
        self.APASSXMATCHBRCOLOUR = []
        self.USNOBXMATCHBRCOLOUR = []
        self.APASSXMATCHDISTASEC = []
        self.USNOBXMATCHDISTASEC = []
        self.ROLLINGMEANAPASSMAG = []  
        self.ROLLINGSTDEVAPASSMAG = []    
        self.ROLLINGMEANUSNOBMAG = []  
        self.ROLLINGSTDEVUSNOBMAG = []  
        self.APASSNUMTIMESSWITCHED = []
        self.USNOBNUMTIMESSWITCHED = []
        self.err = err
        self.logger = logger
        
    def insert(self, skycamref, ra, dec, raerr, decerr, apassref, usnobref, nobs, apassxmatchbrcolour, usnobxmatchbrcolour, apassxmatchdistasec, usnobxmatchdistasec, rollingmeanapassmag, rollingstdevapassmag, rollingmeanusnobmag, rollingstdevusnobmag, apassnumtimesswitched, usnobnumtimesswitched):
        '''
        insert Skycam object into catalogue
        '''
        self.REF.append(skycamref)
        self.RA.append(ra)    
        self.DEC.append(dec)
        self.RAERR.append(raerr)
        self.DECERR.append(decerr)  
        self.APASSREF.append(apassref)  
        self.USNOBREF.append(usnobref)          
        self.NOBS.append(nobs)
        self.APASSXMATCHBRCOLOUR.append(apassxmatchbrcolour)
        self.USNOBXMATCHBRCOLOUR.append(usnobxmatchbrcolour)
        self.APASSXMATCHDISTASEC.append(apassxmatchdistasec)
        self.USNOBXMATCHDISTASEC.append(usnobxmatchdistasec)
        self.ROLLINGMEANAPASSMAG.append(rollingmeanapassmag) 
        self.ROLLINGSTDEVAPASSMAG.append(rollingstdevapassmag)    
        self.ROLLINGMEANUSNOBMAG.append(rollingmeanusnobmag)  
        self.ROLLINGSTDEVUSNOBMAG.append(rollingstdevusnobmag)  
        self.APASSNUMTIMESSWITCHED.append(apassnumtimesswitched)  
        self.USNOBNUMTIMESSWITCHED.append(usnobnumtimesswitched)

    def query(self, pw_file, pw_file_id, raDeg, decDeg, searchRadius, limitingMag, maxNumSourcesXMatch, appendToCat=True):
        ''' 
        do SCS on skycam[tz?] catalogue
        '''
        try:
            ip, port, username, password = rpf(pw_file, pw_file_id)
            port = int(port)
        except IOError:
            self.err.setError(-17)
            self.err.handleError()       
        except TypeError:
            self.err.setError(-18)
            self.err.handleError()  
            
        # ws call outputs json
        ws_cat = wsc(ip, port, self.err, self.logger)
        ws_cat.SCS(self.NAME.lower(), raDeg, decDeg, searchRadius, 'xmatch_apass_rollingmeanmag', '-1', limitingMag, 'distance', maxNumSourcesXMatch, 'json')
        
        # append to internal catalogue
        if ws_cat.text is not None:
            if appendToCat:        
                for entry in json.loads(ws_cat.text): 
                    try:
                        SKYCAMREF             = str(entry['skycamref'])
                        RA                    = float(entry['ra'])
                        DEC                   = float(entry['dec'])
                        RAERR                 = float(entry['raerrasec'])
                        DECERR                = float(entry['decerrasec'])
                        APASSREF              = str(entry['xmatch_apassref'])
                        USNOBREF              = str(entry['xmatch_usnobref'])
                        NOBS                  = int(entry['nobs'])
                        APASSXMATCHBRCOLOUR   = str(entry['xmatch_apass_brcolour'])
                        USNOBXMATCHBRCOLOUR   = str(entry['xmatch_usnob_brcolour'])
                        ROLLINGMEANAPASSMAG   = float(entry['xmatch_apass_rollingmeanmag'])
                        ROLLINGSTDEVAPASSMAG  = float(entry['xmatch_apass_rollingstdevmag'])
                        ROLLINGMEANUSNOBMAG   = float(entry['xmatch_usnob_rollingmeanmag'])
                        ROLLINGSTDEVUSNOBMAG  = float(entry['xmatch_usnob_rollingstdevmag'])
                        APASSXMATCHDISTASEC   = str(entry['xmatch_apass_distasec'])
                        USNOBXMATCHDISTASEC   = str(entry['xmatch_usnob_distasec'])
                        APASSNUMTIMESSWITCHED = str(entry['xmatch_apass_ntimesswitched'])
                        USNOBNUMTIMESSWITCHED = str(entry['xmatch_usnob_ntimesswitched'])
                        self.insert(skycamref=SKYCAMREF, ra=RA, dec=DEC, raerr=RAERR, decerr=DECERR, apassref=APASSREF, usnobref=USNOBREF, 
                                    nobs=NOBS, apassxmatchbrcolour=APASSXMATCHBRCOLOUR, usnobxmatchbrcolour=USNOBXMATCHBRCOLOUR, 
                                    rollingmeanapassmag=ROLLINGMEANAPASSMAG, rollingstdevapassmag=ROLLINGSTDEVAPASSMAG, 
                                    rollingmeanusnobmag=ROLLINGMEANUSNOBMAG, rollingstdevusnobmag=ROLLINGSTDEVUSNOBMAG, 
                                    apassxmatchdistasec=APASSXMATCHDISTASEC, usnobxmatchdistasec=USNOBXMATCHDISTASEC, 
                                    apassnumtimesswitched=APASSNUMTIMESSWITCHED, usnobnumtimesswitched=USNOBNUMTIMESSWITCHED)
                    except ValueError: 
                        continue                           

class USNOBCatalogue(Catalogue):
    def __init__(self, err, logger):
        Catalogue.__init__(self)  
        self.NAME = "USNOB"
        self.RAERR = []
        self.DECERR = [] 
        self.R1MAG = []      
        self.B1MAG = []
        self.R2MAG = []      
        self.B2MAG = []            
        self.err = err
        self.logger = logger

    def insert(self, usnobref, ra, dec, raerr, decerr, r1mag, b1mag, r2mag, b2mag):
        '''
        insert USNOB object into catalogue
        '''
        self.REF.append(usnobref)
        self.RA.append(ra)    
        self.DEC.append(dec)
        self.RAERR.append(raerr)    
        self.DECERR.append(decerr)
        self.R1MAG.append(r1mag)    
        self.B1MAG.append(b1mag)
        self.R2MAG.append(r2mag)    
        self.B2MAG.append(b2mag)

    def query(self, pw_file, pw_file_id, raDeg, decDeg, searchRadius, limitingMag, maxNumSourcesXMatch, appendToCat=True):
        ''' 
        do SCS on USNOB catalogue
        '''
        try:
            ip, port, username, password = rpf(pw_file, pw_file_id)
            port = int(port)
        except IOError:
            self.err.setError(-17)
            self.err.handleError()       
        except TypeError:
            self.err.setError(-18)
            self.err.handleError()  
            
         # ws call outputs json
        ws_cat = wsc(ip, port, self.err, self.logger)
        ws_cat.SCS(self.NAME.lower(), raDeg, decDeg, searchRadius, 'rmag1', -1, limitingMag, 'distance', maxNumSourcesXMatch, 'json')
        
        # append to internal catalogue
        if ws_cat.text is not None:
            if appendToCat:        
                for entry in json.loads(ws_cat.text): 
                    try:
                        USNOBREF    = str(entry['usnobref'])
                        RA          = float(entry['ra'])
                        DEC         = float(entry['dec'])
                        RAERR       = float(entry['raerrasec'])
                        DECERR      = float(entry['decerrasec'])
                        R1MAG       = float(entry['rmag1'])
                        B1MAG       = float(entry['bmag1'])
                        R2MAG       = float(entry['rmag2'])
                        B2MAG       = float(entry['bmag2'])
                        self.insert(usnobref=USNOBREF, ra=RA, dec=DEC, raerr=RAERR, decerr=DECERR, r1mag=R1MAG, b1mag=B1MAG, r2mag=R2MAG, b2mag=B2MAG)
                    except ValueError: 
                        continue    
                    
class sExCatalogue(Catalogue):
    def __init__(self, err, logger):
        Catalogue.__init__(self) 
        self.NAME = "sEx"
        self.X_IMAGE = []
        self.Y_IMAGE = []
        self.FLUX_MAX = []
        self.FLUX_AUTO = []
        self.FLUXERR_AUTO = []
        self.MAG_AUTO = []
        self.MAGERR_AUTO = []
        self.BACKGROUND = []
        self.ISOAREA_WORLD = []
        self.FLAGS = []
        self.FWHM_WORLD = []
        self.ELONGATION = []
        self.ELLIPTICITY = []
        self.THETA_IMAGE = []
        self.err = err
        self.logger = logger

    def insert(self, ra, dec, x, y, fluxmax, fluxauto, fluxerrauto, magauto, magerrauto, background, isoareaworld, flags, fwhmworld, elongation, ellipticity, thetaimage):
        '''
        insert sExtractor source into catalogue.
        '''
        self.RA.append(ra)
        self.DEC.append(dec)
        self.X_IMAGE.append(x)
        self.Y_IMAGE.append(y)
        self.FLUX_MAX.append(fluxmax)
        self.FLUX_AUTO.append(fluxauto)
        self.FLUXERR_AUTO.append(fluxerrauto)
        self.MAG_AUTO.append(magauto)
        self.MAGERR_AUTO.append(magerrauto)
        self.BACKGROUND.append(background)
        self.ISOAREA_WORLD.append(isoareaworld)
        self.FLAGS.append(flags)
        self.FWHM_WORLD.append(fwhmworld)
        self.ELONGATION.append(elongation)
        self.ELLIPTICITY.append(ellipticity)
        self.THETA_IMAGE.append(thetaimage)

    def query(self, inFile, resPath, pathToConfFile, clean=True, ccdSizeX=0, ccdSizeY=0, fieldMargin=0, appendToCat=True, hard=False):
        '''
        init sExtractor using a specified config file.
        '''
        if not os.path.exists(pathToConfFile):
            self.err.setError(-6)
            self.err.handleError()
        self.logger.info("(sExCatalogue.query) Using config file " + pathToConfFile)

        # run sExtractor
        self.logger.info("(sExCatalogue.query) Running sExtractor")
        sEx = pysex(inFile, resPath, pathToConfFile, self.err, self.logger)
        sEx.run()

        # clean output if requested
        if clean:
            self._clean(sEx.catdata, ccdSizeX, ccdSizeY, fieldMargin)   # sEx.catdata is passed by reference

        # append to internal catalogue if requested 
        im = FITSFile(inFile, self.err) 
        im.openFITSFile()
        im.getHeaders(0)
        if appendToCat:
            for idx in range(sEx.catdata.nrows):
                ra, dec = self._xy2radec(im.headers, [sEx.catdata['X_IMAGE'][idx], sEx.catdata['Y_IMAGE'][idx]])
                self.insert(ra, dec, sEx.catdata['X_IMAGE'][idx], sEx.catdata['Y_IMAGE'][idx], sEx.catdata['FLUX_MAX'][idx], sEx.catdata['FLUX_AUTO'][idx], sEx.catdata['FLUXERR_AUTO'][idx], sEx.catdata['MAG_AUTO'][idx], sEx.catdata['MAGERR_AUTO'][idx], sEx.catdata['BACKGROUND'][idx], sEx.catdata['ISOAREA_WORLD'][idx], sEx.catdata['FLAGS'][idx], sEx.catdata['FWHM_WORLD'][idx], sEx.catdata['ELONGATION'][idx], sEx.catdata['ELLIPTICITY'][idx], sEx.catdata['THETA_IMAGE'][idx])

        im.closeFITSFile()

        # make a hard copy of the catalogue if requested
        if hard:
            sEx.write_cat(inFile + ".cat")

        return sEx.catdata

    def read(self, inFile):
        catdata = asciidata.open(inFile + ".cat")

        im = FITSFile(inFile, self.err) 
        im.openFITSFile()
        im.getHeaders(0)
        for idx in range(catdata.nrows):
            ra, dec = self._xy2radec(im.headers, [catdata['X_IMAGE'][idx], catdata['Y_IMAGE'][idx]])
            self.insert(ra, dec, catdata['X_IMAGE'][idx], catdata['Y_IMAGE'][idx], catdata['FLUX_MAX'][idx], catdata['FLUX_AUTO'][idx], catdata['FLUXERR_AUTO'][idx], catdata['MAG_AUTO'][idx], catdata['MAGERR_AUTO'][idx], catdata['BACKGROUND'][idx], catdata['ISOAREA_WORLD'][idx], catdata['FLAGS'][idx], catdata['FWHM_WORLD'][idx], catdata['ELONGATION'][idx], catdata['ELLIPTICITY'][idx], catdata['THETA_IMAGE'][idx])

        im.closeFITSFile()

    def _clean(self, catdata, ccdSizeX, ccdSizeY, fieldMargin):
        '''
        remove suspect sources from sExtractor output.
        '''
        # purge sources lying inside a margin from the CCD chip edge
        numRowsBeforePurge = catdata.nrows
        if numRowsBeforePurge == 0:
            return None

        catdata.sort('X_IMAGE')

        rowsToPurge = [i for i in range(catdata.nrows) if catdata['X_IMAGE'][i] <= fieldMargin]
        idxUpper = max(rowsToPurge) + 1 if len(rowsToPurge) > 0 else 0

        catdata.delete(0, idxUpper)
        self.logger.info("(sExCatalogue._clean) Purged " + str(numRowsBeforePurge - catdata.nrows) + " sources failing x low margin criteria")

        numRowsBeforePurge = catdata.nrows
        if numRowsBeforePurge == 0:
            return None
        catdata.sort('X_IMAGE', descending=1)

        rowsToPurge = [i for i in range(catdata.nrows) if catdata['X_IMAGE'][i] >= ccdSizeX-fieldMargin]
        idxUpper = max(rowsToPurge) + 1 if len(rowsToPurge) > 0 else 0

        catdata.delete(0, idxUpper)
        self.logger.info("(sExCatalogue._clean) Purged " + str(numRowsBeforePurge - catdata.nrows) + " sources failing x high margin criteria")

        numRowsBeforePurge = catdata.nrows
        if numRowsBeforePurge == 0:
            return None
        catdata.sort('Y_IMAGE')

        rowsToPurge = [i for i in range(catdata.nrows) if catdata['Y_IMAGE'][i] <= fieldMargin]
        idxUpper = max(rowsToPurge) + 1 if len(rowsToPurge) > 0 else 0

        catdata.delete(0, idxUpper)
        self.logger.info("(sExCatalogue._clean) Purged " + str(numRowsBeforePurge - catdata.nrows) + " sources failing y low margin criteria")

        numRowsBeforePurge = catdata.nrows
        if numRowsBeforePurge == 0:
            return None
        catdata.sort('Y_IMAGE', descending=1)

        rowsToPurge = [i for i in range(catdata.nrows) if catdata['Y_IMAGE'][i] >= ccdSizeY-fieldMargin]
        idxUpper = max(rowsToPurge) + 1 if len(rowsToPurge) > 0 else 0

        catdata.delete(0, idxUpper)
        self.logger.info("(sExCatalogue._clean) Purged " + str(numRowsBeforePurge - catdata.nrows) + " sources failing y high margin criteria")

        # purge sources with non-zero sExtractor flags
        numRowsBeforePurge = catdata.nrows
        if numRowsBeforePurge == 0:
            return None
        catdata.sort('FLAGS', ordered=1, descending=1)

        rowsToPurge = [i for i in range(catdata.nrows) if catdata['FLAGS'][i] is not 0]
        idxUpper = max(rowsToPurge) + 1 if len(rowsToPurge) > 0 else 0

        catdata.delete(0, idxUpper)
        self.logger.info("(sExCatalogue._clean) Purged " + str(numRowsBeforePurge - catdata.nrows) + " sources with non-zero sExtractor flag")

        if catdata.nrows == 0:
            return None

        catdata.sort('NUMBER')

    def _xy2radec(self, hdr, pix):
        '''
        convert from xy to RADEC using the WCS from a FITS header
        '''
        wcs = pywcs.WCS(hdr)
        radec = wcs.all_pix2sky([pix], 1)
        return radec.tolist()[0][0], radec.tolist()[0][1]                    
                    
                    
 
