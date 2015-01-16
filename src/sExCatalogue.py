'''
name:		sExCatalogue.py
author:		rmb

description: 	A sExtractor catalogue class
'''

import os

import asciidata
import pywcs

from errors import errors
from FITSFile import FITSFile
from pysex import pysex

class sExCatalogue():
    def __init__(self, err, logger):
        self.RA = []
        self.DEC = []
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
            self._clean(sEx.catdata, ccdSizeX, ccdSizeY, fieldMargin)	# sEx.catdata is passed by reference

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

