'''
name:		catalogue.py
author:		rmb

description: 	Catalogue class
'''
import subprocess
import os

import asciidata
import pywcs

from errors import errors
from FITSFile import FITSFile
from pysex import pysex
from database import database_postgresql
from util import read_password_file as rpf

class Catalogue():
    def __init__(self):  
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
        self.err = err
        self.logger = logger
        
    def insert(self, apassref, ra, dec, raerr, decerr, vmag, bmag, gmag, rmag, imag, vmagerr, bmagerr, gmagerr, rmagerr, imagerr):
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

    def query(self, pw_file, pw_file_id, apass_db_name, raDeg, decDeg, searchRadius, limitingMag, appendToCat=True):
        ''' 
        query APASS database for objects satisfying specific criteria
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
            
        APASSDB = database_postgresql(ip, port, username, password, apass_db_name, self.err)
        APASSDB.connect()
        
        res = APASSDB.read("SELECT id, radeg, decdeg, raerrasec, decerrasec, vmag, bmag, gmag, rmag, imag, verr, berr, gerr, rerr, ierr FROM stars \
                           WHERE (coords @ scircle '<(" + str(raDeg) + "d," + str(decDeg) + "d)," + str(searchRadius) + "d>' = true) and (bmag <= " 
                           + str(limitingMag) + ") and (rmag <= " + str(limitingMag) + ")")
        
        if appendToCat:        
            for row in res.fetchall(): 
                try:
                    APASSREF    = str(row[0])
                    RA          = float(row[1])
                    DEC         = float(row[2])
                    RAERR       = float(row[3])
                    DECERR      = float(row[4])
                    VMAG        = float(row[5])
                    BMAG        = float(row[6])
                    GMAG        = float(row[7])
                    RMAG        = float(row[8])
                    IMAG        = float(row[9])
                    VMAGERR     = float(row[10])
                    BMAGERR     = float(row[11])
                    GMAGERR     = float(row[12])
                    RMAGERR     = float(row[13])
                    IMAGERR     = float(row[14])
                    self.insert(apassref=APASSREF, ra=RA, dec=DEC, raerr=RAERR, decerr=DECERR, vmag=VMAG, bmag=BMAG, gmag=GMAG, rmag=RMAG, imag=IMAG, 
                                vmagerr=VMAGERR, bmagerr=BMAGERR, gmagerr=GMAGERR, rmagerr=RMAGERR, imagerr=IMAGERR)
                except ValueError: 
                    continue                

class USNOBCatalogue(Catalogue):
    def __init__(self, err, logger):
        Catalogue.__init__(self) 
        self.EPOCH = []
        self.R2MAG = []      
        self.B2MAG = []            
        self.err = err
        self.logger = logger

    def insert(self, usnobref, ra, dec, epoch, r2mag, b2mag):
        '''
        insert usnob object into catalogue
        '''
        self.REF.append(usnobref)
        self.RA.append(ra)    
        self.DEC.append(dec)
        self.EPOCH.append(epoch)
        self.R2MAG.append(r2mag)    
        self.B2MAG.append(b2mag)

    def query(self, filePath, binPath, catUSNOBPath, raDeg, decDeg, searchRadius, limitingMag, appendToCat=True):
        ''' 
        query USNOB1 database for objects satisfying specific criteria
        '''
        def slices(s, *args):
            position = 0
            for length in args:
                yield s[position:position + length]
                position += length

        with open(filePath, "w") as outFile:
            subprocess.call([binPath + "query_usnob", "-r", str(searchRadius), "-c", str(raDeg), str(decDeg), "-lmb1", "-1," + str(limitingMag), "-lmb2", "-1," + str(limitingMag), "-lmr1", "-1," + str(limitingMag), "-lmr2", "-1," + str(limitingMag), "-m", "100000", "-R", catUSNOBPath.rstrip('/')], stdout=outFile)

        with open(filePath, "r") as inFile:
            for line in inFile:
                parsed = list(slices(line, 12, 1, 12, 1, 10, 10, 1, 3, 1, 3, 1, 6, 1, 6, 1, 6, 1, 1, 1, 3, 1, 3, 1, 1, 1, 1, 1, 1, 1, 4, 1, 5, 1, 1, 1, 5, 1, 2, 1, 13, 1, 5, 1, 1, 1, 5, 1, 2, 1, 13, 1, 5, 1, 1, 1, 5, 1, 2, 1, 13, 1, 5, 1, 1, 1, 5, 1, 2, 1, 13, 1, 5, 1, 1, 1, 5, 1, 2, 1, 13, 1, 4, 7))
                USNOBREF = parsed[0]
                RA = parsed[4]
                DEC = parsed[5] 
                EPOCH = parsed[11] 
                BMAG1 = parsed[31]
                RMAG1 = parsed[41]
                BMAG2 = parsed[51]
                RMAG2 = parsed[61]

                # check input is numeric (float) to truncate start/end lines
                if appendToCat:
                  try:
                      self.insert(usnobref=str(USNOBREF), ra=float(RA), dec=float(DEC), epoch=float(EPOCH), r2mag=float(RMAG2), b2mag=float(BMAG2))
                  except ValueError: 
                      continue

class sExCatalogue(Catalogue):
    def __init__(self, err, logger):
        Catalogue.__init__(self) 
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
                    
                    
 
