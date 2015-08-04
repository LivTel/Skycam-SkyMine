'''
name:		pipeline.py
author:		rmb

description: 	A script containing the calibration and analysis pipelines.
'''
import logging
import tempfile
import subprocess
import os

import numpy as np
import scipy.stats as stats
from errors import errors
from FITSFile import FITSFile
from catalogue import *
from sExCatalogue import *
from source import *
from util import *
from database import database_postgresql
from mine import postgresql_skycam_mine
from plots import plotCalibration, plotMollweide

class pipeline():
    def __init__(self, images, params, err, logger):
        self.images 		= images
        self.params 		= params
        self.err		= err
        self.logger		= logger

    def run(self):
        '''
        run the sequence
        '''
        self.logger.info("(pipeline.run) Starting run")
        images = self.images

        # extract
        images = self._extractSources(images)

        # catalogue matching and ZP calibration
        if 'USNOB' in self.params['cat']:
            matchedSources, unmatchedSources = self._matchSources_USNOB1(images)  
            calibrationCoeffs = self._calibrateSources_USNOB1(matchedSources);
        if 'APASS' in self.params['cat']:
            matchedSources, unmatchedSources = self._matchSources_APASS(images) 
            calibrationCoeffs = self._calibrateSources_APASS(matchedSources);
            
        # store to db
        if self.params['storeToDB']:
            self._storeToPostgresSQLDatabase(matchedSources, unmatchedSources)

        # plot
        if self.params['makePlots']:
                plotCalibration(matchedSources, calibrationCoeffs, float(self.params['lowerColourLimit']), float(self.params['upperColourLimit']), self.logger, hard=True, outImageFilename=self.params['resPath'] + "calibration.png", outDataFilename=self.params['resPath'] + "data.calibration", USNOB=False)
                plotMollweide(images, self.err, self.logger, bins=[30,20], hard=True, outImageFilename=self.params['resPath'] + "mollweide.png", outDataFilename=self.params['resPath'] + "data.mollweide")

        self.logger.info("(pipeline.run) Finished run")

    def _extractSources(self, images, checkValidWCS=True, checkPointingChange=True):
        '''
        perform some image integrity checks (if set), run sExtractor on images and check source output.
        '''
        validWCSKeys = {"CRVAL1", "CRVAL2", "CRPIX1", "CRPIX2", "CD1_1", "CD1_2", "CD2_1", "CD2_2", "RA_CENT", "DEC_CENT", "ROTSKYPA"}
        lastPointing = []
        newImages = []
        for idx, f in enumerate(images):
            im = FITSFile(f, self.err) 
	    im.openFITSFile()
            im.getHeaders(0)

            # if set, check the image has valid WCS-related headers
            if checkValidWCS:
                hasValidWCS = True
	        for key in validWCSKeys:
	            if not im.headers.has_key(key):
                        hasValidWCS = False
                        self.err.setError(1)
                        self.err.handleError()
                        break
                if not hasValidWCS:
                    continue

            # if set, check the pointing hasn't changed from the last image
            if checkPointingChange:
                pointingChanged = False
                if not lastPointing:	# special case (if it's the first file in the list)
                    try:
                        lastPointing = [im.headers["RA_CENT"], im.headers["DEC_CENT"]]
                        self.err.setError(2)
                        self.err.handleError()
                        pointingChanged = True
                    except KeyError:
                        self.err.setError(-5)
                        self.err.handleError()
                else:
                    try:
                        thisPointing = [im.headers["RA_CENT"], im.headers["DEC_CENT"]]
                    except KeyError:
                        self.err.setError(-5)
                        self.err.handleError()

                    if find_pointing_angle_diff(thisPointing, lastPointing) > float(self.params['pointingDiffThresh']):
                        self.err.setError(3)
                        self.err.handleError() 
                        pointingChanged = True  

                    lastPointing = thisPointing
   
                if pointingChanged:
                    continue 

            # run sExtractor...
            sExCat = sExCatalogue(self.err, self.logger)
            catdata = sExCat.query(f, self.params['resPath'], self.params['sExConfFile'], ccdSizeX=int(self.params['CCDSizeX']), ccdSizeY=int(self.params['CCDSizeY']), fieldMargin=int(self.params['fieldMargin']), appendToCat=False, hard=True)
 
            # ...and check the output
            ## check number of catalogue sources != 0 (i.e. empty catalogue returned)
            if catdata is None:
                self.err.setError(9)
                self.err.handleError()
                im.closeFITSFile()
                continue
    
            ## check number of catalogue sources
            numExtSources = max(catdata["NUMBER"].tonumpy())
            self.logger.info("(pipeline._extractSources) " + str(numExtSources) + " legit sources in image (" + str(int(self.params['minSources'])) + ")")
            if numExtSources < int(self.params['minSources']):
                self.err.setError(4)
                self.err.handleError()
                im.closeFITSFile()
                continue 

            ## check maximum elongation of sources
            elongation = round(max(catdata["ELONGATION"].tonumpy()), 2)
            self.logger.info("(pipeline._extractSources) Max elongation in image is " + str(elongation) + " (" + str(self.params['maxElongation']) + ")")
            if elongation > float(self.params['maxElongation']):
                self.err.setError(5)
                self.err.handleError()
                im.closeFITSFile()
                continue 

            ## check excess kurtosis of object angle   
            exKurtosis = round(stats.kurtosis(catdata["THETA_IMAGE"].tonumpy()), 2)
            self.logger.info("(pipeline._extractSources) Kurtosis of object angle is " + str(exKurtosis) + " (" + str(float(self.params['maxExKurtosis'])) + ")")
            if exKurtosis > float(self.params['maxExKurtosis']):
                self.err.setError(6)
                self.err.handleError() 
                im.closeFITSFile()
                continue 

            ## combined check of kurtosis and elongation
            sourcesCombCheck = 0
            for idx in range(catdata.nrows):
                if catdata['ELONGATION'][idx] > float(self.params['maxCombElongation']) and catdata['KURTOSIS'][idx] > float(self.params['maxCombExKurtosis']):
                  sourcesCombCheck += 1
 
            self.logger.info("(pipeline._extractSources) Number of objects failing combined elongation/kurtosis constraint is " + str(sourcesCombCheck) + " (" + str(float(self.params['maxSourcesCombCheck'])) + ")")
            if sourcesCombCheck > float(self.params['maxSourcesCombCheck']):
                self.err.setError(7)
                self.err.handleError() 
                im.closeFITSFile()
                continue 

            ## check maximum flux   
            flux = max(catdata['FLUX_MAX'].tonumpy())
            self.logger.info("(pipeline._extractSources) Maximum flux in catalogue is " + str(flux) + " (" + str(self.params['maxFlux']) + ")")
            if flux > float(self.params['maxFlux']):
                self.err.setError(8)
                self.err.handleError()
                im.closeFITSFile()
                continue 

            im.closeFITSFile()

            # all tests passed OK
            newImages.append(f)

        # exit if the number of images required for calibration doesn't meet the threshold 
        if len(newImages) < int(self.params['numCalibrationImages']):
            self.err.setError(-8)
            self.err.handleError()            

        self.logger.info("(pipeline._extractSources) Purged " + str(len(images) - len(newImages)) + " images due to extracted source constraints")

        if len(newImages) is 0:
            self.err.setError(-10)
            self.err.handleError()

        return newImages
      
    def _matchSources_APASS(self, images, checkColourIndex=True, checkNumMatchedSources=True):
        '''
        match sources to APASS catalogue.

        returns two objects containing lists of source instances (unmatchedSources, matchedSources).
        '''
        lastPointing = []
        matchedSources = []
        unmatchedSources = []
        APASSCatAll = APASSCatalogue(self.err, self.logger) 
        for idx, f in enumerate(images):
            self.logger.info("(pipeline._matchSources_APASS) Processing image " + f)

            im = FITSFile(f, self.err) 
            im.openFITSFile()
            im.getHeaders(0)

            matchingTolerance = self.params['matchingTolerance']
            limitingMag = self.params['limitingMag']

            searchRadius = self.params['fieldSize']

            # establish if we need to query the APASS database
            ## is this the first image?
            if idx == 0:
                try:
                    self.logger.info("(pipeline._matchSources_APASS) Querying APASS catalogue at " + im.headers['RA'] + " " + im.headers['DEC'] + " with a search radius of " + str(searchRadius + float(self.params['pointingDiffThresh'])) + ", " + str(searchRadius + float(self.params['pointingDiffThresh'])) + " deg")
                    APASSCatAll.query(self.params['path_pw_list'], self.params['apass_db_credentials_id'], self.params['apass_db_name'], hms_2_deg(im.headers['RA']), dms_2_deg(im.headers['DEC']), searchRadius + self.params['pointingDiffThresh'], limitingMag)
                    lastPointing = [im.headers["RA_CENT"], im.headers["DEC_CENT"]]
                except KeyError:
                    self.err.setError(-5)
                    self.err.handleError()
            ## if not..
            else:
                try:
                    thisPointing = [im.headers["RA_CENT"], im.headers["DEC_CENT"]]
                except KeyError:
                    self.err.setError(-5)
                    self.err.handleError()

                ## ..check that the pointing hasn't changed
                if find_pointing_angle_diff(thisPointing, lastPointing) > float(self.params['pointingDiffThresh']):
                    self.logger.info("(pipeline._matchSources_APASS) Pointing has changed since last image.")
                    self.logger.info("(pipeline._matchSources_APASS) Querying APASS catalogue at " + im.headers['RA'] + " " + im.headers['DEC'] + " with a search radius of " + str(searchRadius + float(self.params['pointingDiffThresh'])) + ", " + str(searchRadius + float(self.params['pointingDiffThresh'])) + " deg")
                    APASSCatAll.query(self.params['path_pw_list'], self.params['apass_db_credentials_id'], self.params['apass_db_name'], hms_2_deg(im.headers['RA']), dms_2_deg(im.headers['DEC']), searchRadius + self.params['pointingDiffThresh'], limitingMag)
                else:
                    self.logger.info("(pipeline._matchSources_APASS) Pointing has NOT changed since last image. Using data from previous APASS query")

                lastPointing = thisPointing

            # parse Sextractor catalogue
            sExCat = sExCatalogue(self.err, self.logger)
            sExCat.read(f)

            self.logger.info("(pipeline._matchSources_APASS) Cross matching catalogues with a tolerance of " + str(matchingTolerance*3600) + " arcsec")
            matches = pysm.spherematch(sExCat.RA, sExCat.DEC, APASSCatAll.RA, APASSCatAll.DEC, tol=matchingTolerance, nnearest=1)

            sExCatMatchedIndexes = matches[0]
            APASSMatchedIndexes = matches[1]

            # find indexes of unmatched sources
            sExCatAllIndexes = np.arange(0, len(sExCat.RA), 1)
            sExCatUnmatchedIndexes = list(set(sExCatAllIndexes) - set(sExCatMatchedIndexes))
            self.logger.info("(pipeline._matchSources_APASS) Cross matched " + str(len(sExCatMatchedIndexes)) + " source(s)")

            # if set, check number of matched sources is greater than the minimum required
            if checkNumMatchedSources:
                if len(sExCatMatchedIndexes) < int(self.params['minNumMatchedSources']):
                    self.err.setError(12)
                    self.err.handleError()
                    continue

            # create a list of matched sources
            for idx in range(len(sExCatMatchedIndexes)):
               matchedSources.append(source(f, sExCat.RA[sExCatMatchedIndexes[idx]], sExCat.DEC[sExCatMatchedIndexes[idx]], 
                                            sExCat.X_IMAGE[sExCatMatchedIndexes[idx]], sExCat.Y_IMAGE[sExCatMatchedIndexes[idx]], 
                                            sExCat.FLUX_AUTO[sExCatMatchedIndexes[idx]], sExCat.FLUXERR_AUTO[sExCatMatchedIndexes[idx]], 
                                            sExCat.MAG_AUTO[sExCatMatchedIndexes[idx]], sExCat.MAGERR_AUTO[sExCatMatchedIndexes[idx]], 
                                            sExCat.BACKGROUND[sExCatMatchedIndexes[idx]], sExCat.ISOAREA_WORLD[sExCatMatchedIndexes[idx]], 
                                            sExCat.FLAGS[sExCatMatchedIndexes[idx]], sExCat.FWHM_WORLD[sExCatMatchedIndexes[idx]], 
                                            sExCat.ELONGATION[sExCatMatchedIndexes[idx]], sExCat.ELLIPTICITY[sExCatMatchedIndexes[idx]], 
                                            sExCat.THETA_IMAGE[sExCatMatchedIndexes[idx]], APASSCatREF=APASSCatAll.APASSREF[APASSMatchedIndexes[idx]], 
                                            APASSCatRA=APASSCatAll.RA[APASSMatchedIndexes[idx]], APASSCatDEC=APASSCatAll.DEC[APASSMatchedIndexes[idx]], 
                                            APASSCatRAERR=APASSCatAll.RAERR[APASSMatchedIndexes[idx]], APASSCatDECERR=APASSCatAll.DECERR[APASSMatchedIndexes[idx]], 
                                            APASSCatVMAG=APASSCatAll.VMAG[APASSMatchedIndexes[idx]], APASSCatBMAG=APASSCatAll.BMAG[APASSMatchedIndexes[idx]], 
                                            APASSCatGMAG=APASSCatAll.GMAG[APASSMatchedIndexes[idx]], APASSCatRMAG=APASSCatAll.RMAG[APASSMatchedIndexes[idx]], 
                                            APASSCatIMAG=APASSCatAll.IMAG[APASSMatchedIndexes[idx]], APASSCatVMAGERR=APASSCatAll.VMAGERR[APASSMatchedIndexes[idx]], 
                                            APASSCatBMAGERR=APASSCatAll.BMAGERR[APASSMatchedIndexes[idx]], APASSCatGMAGERR=APASSCatAll.GMAGERR[APASSMatchedIndexes[idx]], 
                                            APASSCatRMAGERR=APASSCatAll.RMAGERR[APASSMatchedIndexes[idx]], APASSCatIMAGERR=APASSCatAll.IMAGERR[APASSMatchedIndexes[idx]])) # always want to append to source list

            # create a list of unmatched sources
            for idx in range(len(sExCatUnmatchedIndexes)):
                unmatchedSources.append(source(f, sExCat.RA[sExCatUnmatchedIndexes[idx]], sExCat.DEC[sExCatUnmatchedIndexes[idx]], sExCat.X_IMAGE[sExCatUnmatchedIndexes[idx]], 
                                               sExCat.Y_IMAGE[sExCatUnmatchedIndexes[idx]], sExCat.FLUX_AUTO[sExCatUnmatchedIndexes[idx]], sExCat.FLUXERR_AUTO[sExCatUnmatchedIndexes[idx]], 
                                               sExCat.MAG_AUTO[sExCatUnmatchedIndexes[idx]], sExCat.MAGERR_AUTO[sExCatUnmatchedIndexes[idx]], sExCat.BACKGROUND[sExCatUnmatchedIndexes[idx]], 
                                               sExCat.ISOAREA_WORLD[sExCatUnmatchedIndexes[idx]], sExCat.FLAGS[sExCatUnmatchedIndexes[idx]], sExCat.FWHM_WORLD[sExCatUnmatchedIndexes[idx]], 
                                               sExCat.ELONGATION[sExCatUnmatchedIndexes[idx]], sExCat.ELLIPTICITY[sExCatUnmatchedIndexes[idx]], sExCat.THETA_IMAGE[sExCatUnmatchedIndexes[idx]])) # always want to append to source list

            self.logger.info("(pipeline._matchSources_APASS) Couldn't find a match for " + str(len(sExCatUnmatchedIndexes)) + " source(s)")          

            # if set, remove sources with too high a colour index
            if checkColourIndex:
                numSourcesBefore = len(matchedSources)
                for idx, i in enumerate(matchedSources):
                    BRColour = i.APASSCatBMAG - i.APASSCatRMAG
                    if BRColour < float(self.params['lowerColourLimit']) or BRColour > float(self.params['upperColourLimit']):
                        del matchedSources[idx]
                self.logger.info("(pipeline._matchSources_APASS) Removed " + str(numSourcesBefore - len(matchedSources)) + " source(s) due to colour index constraint")       

            im.closeFITSFile()

        if len(matchedSources) == 0:
            self.err.setError(-9)
            self.err.handleError()
                    
        return matchedSources, unmatchedSources      

    def _matchSources_USNOB1(self, images, checkColourIndex=True, checkNumMatchedSources=True):
        '''
        match sources to USNOB1 catalogue.

        returns two objects containing lists of source instances (unmatchedSources, matchedSources).
        '''
        lastPointing = []
        matchedSources = []
        unmatchedSources = []
        USNOBCatAll = USNOBCatalogue(self.err, self.logger) 
        for idx, f in enumerate(images):
            self.logger.info("(pipeline._matchSources_USNOB1) Processing image " + f)

            im = FITSFile(f, self.err) 
	    im.openFITSFile()
            im.getHeaders(0)

            matchingTolerance = self.params['matchingTolerance']
            limitingMag = self.params['limitingMag']

            searchRadius = self.params['fieldSize']

            # establish if we need to query the USNOB1 database
            ## is this the first image?
            if idx == 0:
                try:
                    self.logger.info("(pipeline._matchSources_USNOB1) Querying USNO-B catalogue at " + im.headers['RA'] + " " + im.headers['DEC'] + " with a search radius of " + str(searchRadius + float(self.params['pointingDiffThresh'])) + ", " + str(searchRadius + float(self.params['pointingDiffThresh'])) + " deg")
                    USNOBCatAll.query(self.params['resPath'] + os.path.basename(f) + ".usnob", self.params['binPath'], self.params['catUSNOBPath'], im.headers['RA'], im.headers['DEC'], (searchRadius + self.params['pointingDiffThresh'])*60, limitingMag)
                    lastPointing = [im.headers["RA_CENT"], im.headers["DEC_CENT"]]
                except KeyError:
                    self.err.setError(-5)
                    self.err.handleError()
            ## if not..
            else:
                try:
                    thisPointing = [im.headers["RA_CENT"], im.headers["DEC_CENT"]]
                except KeyError:
                    self.err.setError(-5)
                    self.err.handleError()

                ## ..check that the pointing hasn't changed
                if find_pointing_angle_diff(thisPointing, lastPointing) > float(self.params['pointingDiffThresh']):
                    self.logger.info("(pipeline._matchSources_USNOB1) Pointing has changed since last image.")
                    self.logger.info("(pipeline._matchSources_USNOB1) Querying USNO-B catalogue at " + im.headers['RA'] + " " + im.headers['DEC'] + " with a search radius of " + str(searchRadius + float(self.params['pointingDiffThresh'])) + ", " + str(searchRadius + float(self.params['pointingDiffThresh'])) + " deg")
                    USNOBCatAll.query(self.params['resPath'] + os.path.basename(f) + ".usnob", self.params['binPath'], self.params['catUSNOBPath'], im.headers['RA'], im.headers['DEC'], (searchRadius + self.params['pointingDiffThresh'])*60, limitingMag)
                else:
                    self.logger.info("(pipeline._matchSources_USNOB1) Pointing has NOT changed since last image. Using data from previous USNO-B query")

                lastPointing = thisPointing

            # parse Sextractor catalogue
            sExCat = sExCatalogue(self.err, self.logger)
            sExCat.read(f)

            self.logger.info("(pipeline._matchSources_USNOB1) Cross matching catalogues with a tolerance of " + str(matchingTolerance*3600) + " arcsec")
            matches = pysm.spherematch(sExCat.RA, sExCat.DEC, USNOBCatAll.RA, USNOBCatAll.DEC, tol=matchingTolerance, nnearest=1)

            sExCatMatchedIndexes = matches[0]
            USNOBMatchedIndexes = matches[1]

            # find indexes of unmatched sources
            sExCatAllIndexes = np.arange(0, len(sExCat.RA), 1)
            sExCatUnmatchedIndexes = list(set(sExCatAllIndexes) - set(sExCatMatchedIndexes))
            self.logger.info("(pipeline._matchSources_USNOB1) Cross matched " + str(len(sExCatMatchedIndexes)) + " source(s)")

            # if set, check number of matched sources is greater than the minimum required
            if checkNumMatchedSources:
                if len(sExCatMatchedIndexes) < int(self.params['minNumMatchedSources']):
                    self.err.setError(12)
                    self.err.handleError()
                    continue

            # create a list of matched sources
            for idx in range(len(sExCatMatchedIndexes)):
               matchedSources.append(source(f, sExCat.RA[sExCatMatchedIndexes[idx]], sExCat.DEC[sExCatMatchedIndexes[idx]], sExCat.X_IMAGE[sExCatMatchedIndexes[idx]], sExCat.Y_IMAGE[sExCatMatchedIndexes[idx]], sExCat.FLUX_AUTO[sExCatMatchedIndexes[idx]], sExCat.FLUXERR_AUTO[sExCatMatchedIndexes[idx]], sExCat.MAG_AUTO[sExCatMatchedIndexes[idx]], sExCat.MAGERR_AUTO[sExCatMatchedIndexes[idx]], sExCat.BACKGROUND[sExCatMatchedIndexes[idx]], sExCat.ISOAREA_WORLD[sExCatMatchedIndexes[idx]], sExCat.FLAGS[sExCatMatchedIndexes[idx]], sExCat.FWHM_WORLD[sExCatMatchedIndexes[idx]], sExCat.ELONGATION[sExCatMatchedIndexes[idx]], sExCat.ELLIPTICITY[sExCatMatchedIndexes[idx]], sExCat.THETA_IMAGE[sExCatMatchedIndexes[idx]], USNOBCatREF=USNOBCatAll.USNOBREF[USNOBMatchedIndexes[idx]], USNOBCatRA=USNOBCatAll.RA[USNOBMatchedIndexes[idx]], USNOBCatDEC=USNOBCatAll.DEC[USNOBMatchedIndexes[idx]], USNOBCatEPOCH=USNOBCatAll.EPOCH[USNOBMatchedIndexes[idx]], USNOBCatR2MAG=USNOBCatAll.R2MAG[USNOBMatchedIndexes[idx]], USNOBCatB2MAG=USNOBCatAll.B2MAG[USNOBMatchedIndexes[idx]])) # always want to append to source list

            # create a list of unmatched sources
            for idx in range(len(sExCatUnmatchedIndexes)):
                unmatchedSources.append(source(f, sExCat.RA[sExCatUnmatchedIndexes[idx]], sExCat.DEC[sExCatUnmatchedIndexes[idx]], sExCat.X_IMAGE[sExCatUnmatchedIndexes[idx]], sExCat.Y_IMAGE[sExCatUnmatchedIndexes[idx]], sExCat.FLUX_AUTO[sExCatUnmatchedIndexes[idx]], sExCat.FLUXERR_AUTO[sExCatUnmatchedIndexes[idx]], sExCat.MAG_AUTO[sExCatUnmatchedIndexes[idx]], sExCat.MAGERR_AUTO[sExCatUnmatchedIndexes[idx]], sExCat.BACKGROUND[sExCatUnmatchedIndexes[idx]], sExCat.ISOAREA_WORLD[sExCatUnmatchedIndexes[idx]], sExCat.FLAGS[sExCatUnmatchedIndexes[idx]], sExCat.FWHM_WORLD[sExCatUnmatchedIndexes[idx]], sExCat.ELONGATION[sExCatUnmatchedIndexes[idx]], sExCat.ELLIPTICITY[sExCatUnmatchedIndexes[idx]], sExCat.THETA_IMAGE[sExCatUnmatchedIndexes[idx]])) # always want to append to source list

            self.logger.info("(pipeline._matchSources_USNOB1) Couldn't find a match for " + str(len(sExCatUnmatchedIndexes)) + " source(s)")          

            # if set, remove sources with too high a colour index
            if checkColourIndex:
                numSourcesBefore = len(matchedSources)
                for idx, i in enumerate(matchedSources):
                    BRColour = i.USNOBCatB2MAG - i.USNOBCatR2MAG
                    if BRColour < float(self.params['lowerColourLimit']) or BRColour > float(self.params['upperColourLimit']):
                        del matchedSources[idx]
                self.logger.info("(pipeline._matchSources_USNOB1) Removed " + str(numSourcesBefore - len(matchedSources)) + " source(s) due to colour index constraint")       

            im.closeFITSFile()

        if len(matchedSources) == 0:
            self.err.setError(-9)
            self.err.handleError()
                    
        return matchedSources, unmatchedSources

    def _calibrateSources_USNOB1(self, matchedSources):
        '''
        (USNOB1) find colour dependent magnitude ZPs.

        returns a list of calibration coefficients.
        '''
        magDifference = []
        BRcolour = []
        for i in matchedSources:
            BRcolour.append(i.USNOBCatB2MAG - i.USNOBCatR2MAG)
            magDifference.append(i.sExCatMagAuto - i.USNOBCatR2MAG)

        # perform linear best fit
        m, c = np.polyfit(BRcolour, magDifference, 1) 

        self.logger.info("(pipeline._calibrateSources) Coefficients of calibration are [" + str(c) + ", " + str(m) + "]")

        return [c, m]
      
    def _calibrateSources_APASS(self, matchedSources):
        '''
        (APASS) find colour dependent magnitude ZPs.

        returns a list of calibration coefficients.
        '''
        magDifference = []
        BRcolour = []
        for i in matchedSources:
            BRcolour.append(i.APASSCatBMAG - i.APASSCatRMAG)
            magDifference.append(i.sExCatMagAuto - i.APASSCatRMAG)

        # perform linear best fit
        m, c = np.polyfit(BRcolour, magDifference, 1) 

        self.logger.info("(pipeline._calibrateSources) Coefficients of calibration are [" + str(c) + ", " + str(m) + "]")

        return [c, m]      

    def _storeToPostgresSQLDatabase(self, matchedSources, unmatchedSources):
        '''
        send information to database.
        '''
    	# set up database connection
   	skycamDB = database_postgresql(self.params['dbHost'], self.params['dbPort'], self.params['dbUser'], self.params['dbPass'], self.params['dbName'], self.err)
    	skycamDB.connect()

   	 # set up mine (& create schema if necessary)
    	schemaName = self.params['schemaName']
    	mine = postgresql_skycam_mine(skycamDB, schemaName, self.logger, self.err)

        if self.params['destroyMine']:
            mine.destroy()

    	if not skycamDB.check_schema_exists(schemaName):
            mine.setup()

        # create unique set of filenames from matchedSources list
        imageFilenames = set()
        for source in matchedSources:
            imageFilenames.add(source.filename)

        # process images by filename
        for i in imageFilenames:
            ## CLOBBERING. NOTE: entries into matchedUSNOBTable are not removed
            ### establish if entry exists for this filename
            query = "SELECT count(*) FROM " + schemaName + ".images WHERE filename = '" + str(os.path.basename(i)) + "'"
            res = skycamDB.read(query).fetchone()
            rowCount = res[0] 
            if (rowCount > 0):	# found entry
                ### delete records from database if clobber flag is set, otherwise continue to next image
                if self.params['clobberDB']:
                    mine.deleteSourcesByFilename(os.path.basename(i))
                    mine.deleteImageByFilename(os.path.basename(i))
                else:
		### otherwise skip this image
                    self.logger.info("(pipeline._storeToPostgresSQLDatabase) Ignoring image " + str(os.path.basename(i)))
                    continue

            filename = os.path.basename(i)

            ## create list of matched and unmatched sources taken from this image
            im_unmatchedSources = list(source for source in unmatchedSources if source.filename == i)
            im_matchedSources = list(source for source in matchedSources if source.filename == i)

            ## create list of unique USNOB targets from matched sources list
            existing_refs = []
            USNOBCatUnique = USNOBCatalogue(self.err, self.logger)
            for src in im_matchedSources:
                if src.USNOBCatREF not in existing_refs:
                    existing_refs.append(src.USNOBCatREF)
                    USNOBCatUnique.insert(usnobref=src.USNOBCatREF, ra=src.USNOBCatRA, dec=src.USNOBCatDEC, epoch=src.USNOBCatEPOCH, r2mag=src.USNOBCatR2MAG, b2mag=src.USNOBCatB2MAG) 

            ## insert image, matchedUSNOBObjects and sources into mine
	    img_id = mine.insertImage(i)
            if img_id is not None:
                mine.insertMatchedUSNOBObjects(USNOBCatUnique)
                mine.insertSources(i, img_id, im_matchedSources)
                mine.insertSources(i, img_id, im_unmatchedSources)

        mine.dumpTableRowCount()	# DEBUG
        mine.dumpTableSampleRecord()	# DEBUG
 
