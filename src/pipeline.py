'''
name:		pipeline.py
author:		rmb

description: 	A class containing the calibration and analysis routines for Skycam data.
'''
import logging
import tempfile
import subprocess
import os
import urllib

import numpy as np
import scipy.stats as stats

from errors import errors
from FITSFile import FITSFile
from catalogue import *
from source import source
from util import *
from database import database_postgresql
from plot import plotZPCalibration, plotMollweide
from ws import ws_catalogue as wsc

class pipeline():
    def __init__(self, params, err, logger):
        self.params 		= params
        self.err		= err
        self.logger		= logger
        
        self.lastPointing       = []
        self.RefCatAll          = []

    def run(self, images):
        '''
        run the sequence
        '''
        self.logger.info("(pipeline.run) Starting run")

        doCatQuery = True                                                                                                  # this keeps track of whether we need to perform a new catalogue query
        valid_images = []
        for idx, f in enumerate(images):
            self.logger.info("(pipeline.run) processing file " + str(idx+1) + " of " + str(len(images)) + " (" + os.path.basename(f) + ")")
            im = FITSFile(f, self.err) 
            im.openFITSFile()
            im.getHeaders(0)     
            if self._hasValidWCS(im):                                                                                       # checks that we have a valid WCS
                if not self._hasPointingChanged(im):                                                                        # checks that pointing hasn't changed
                    self._extractSources(f, im)                                                                             # extract sources
                    matchedSources, unmatchedSources = self._XMatchSources(f, im, doCatQuery, cat=self.params['cat'])       # catalogue cross matching 
                    if matchedSources is not None and unmatchedSources is not None:
                        magDifference, BRcolour, ZP = self._calibrateZP(matchedSources, cat=self.params['cat'])             # zeropoint calculation
                        if self.params['storeToDB']:
                            self._storeToPostgresDatabase(matchedSources, unmatchedSources, cat=self.params['cat'])      # database storage
                        if self.params['makePlots']:
                            plotZPCalibration(magDifference, BRcolour, ZP,                                                  # plots
                                              float(self.params['lowerColourLimit']), 
                                              float(self.params['upperColourLimit']), 
                                              self.logger, 
                                              hard=True, 
                                              outImageFilename=self.params['resPath'] + os.path.basename(f) + ".calibration.png", 
                                              outDataFilename=self.params['resPath'] + os.path.basename(f) + ".data.calibration", 
                                              )
                    doCatQuery = False
                    valid_images.append(f)
                else:                                                                                                       # we skip processing the file if the pointing has changed
                    doCatQuery = True
                self.lastPointing = self._getPointing(im)
            im.closeFITSFile()

        if len(valid_images) == 0:
            self.err.setError(14)
            self.err.handleError()    
        else:
            if self.params['makePlots']:            
                plotMollweide(valid_images, 
                              self.err, 
                              self.logger, 
                              bins=[30,20], 
                              hard=True, 
                              outImageFilename=self.params['resPath'] + "mollweide.png", 
                              outDataFilename=self.params['resPath'] + "data.mollweide"
                              )

        self.logger.info("(pipeline.run) Finished run")
        
    def _hasValidWCS(self, in_FITS_im):
        validWCSKeys = {"CRVAL1", "CRVAL2", "CRPIX1", "CRPIX2", "CD1_1", "CD1_2", "CD2_1", "CD2_2", "RA_CENT", "DEC_CENT", "ROTSKYPA"}
        hasValidWCS = True
        for key in validWCSKeys:
            if key not in in_FITS_im.headers:
                hasValidWCS = False
                self.err.setError(1)
                self.err.handleError()
                return False  
        return True
        
    def _getPointing(self, in_FITS_im):
        return [in_FITS_im.headers["RA_CENT"], in_FITS_im.headers["DEC_CENT"]]
        
    def _hasPointingChanged(self, in_FITS_im):
        pointingChanged = False
        if not self.lastPointing:   # special case (if it's the first file in the list)
            pass
        else:
            thisPointing = self._getPointing(in_FITS_im)
            if find_pointing_angle_diff(thisPointing, self.lastPointing) > float(self.params['pointingDiffThresh']):
                self.err.setError(3)
                self.err.handleError() 
                pointingChanged = True  
        return pointingChanged 

    def _extractSources(self, in_filename, in_FITS_im):
        '''
        run sExtractor on images and check source output.
        '''
        sExCat = sExCatalogue(self.err, self.logger)
        catdata = sExCat.query(in_filename,
                               self.params['resPath'], 
                               self.params['sExConfFile'], 
                               ccdSizeX=int(self.params['CCDSizeX']), 
                               ccdSizeY=int(self.params['CCDSizeY']), 
                               fieldMargin=int(self.params['fieldMargin']), 
                               appendToCat=False, 
                               hard=True
                               )
 
        # ...and check the output
        ## check number of catalogue sources != 0 (i.e. empty catalogue returned)
        if catdata is None:
            self.err.setError(9)
            self.err.handleError()
            return False
    
        ## check number of catalogue sources
        numExtSources = catdata.nrows
        self.logger.info("(pipeline._extractSources) " + str(numExtSources) + " legit sources in image (" + str(int(self.params['minSources'])) + ")")
        if numExtSources < int(self.params['minSources']):
            self.err.setError(4)
            self.err.handleError()
            return False 

        ## check maximum elongation of sources
        elongation = round(max(catdata["ELONGATION"].tonumpy()), 2)
        self.logger.info("(pipeline._extractSources) Max elongation in image is " + str(elongation) + " (" + str(self.params['maxElongation']) + ")")
        if elongation > float(self.params['maxElongation']):
            self.err.setError(5)
            self.err.handleError()
            return False 

        ## check excess kurtosis of object angle   
        exKurtosis = round(stats.kurtosis(catdata["THETA_IMAGE"].tonumpy()), 2)
        self.logger.info("(pipeline._extractSources) Kurtosis of object angle is " + str(exKurtosis) + " (" + str(float(self.params['maxExKurtosis'])) + ")")
        if exKurtosis > float(self.params['maxExKurtosis']):
            self.err.setError(6)
            self.err.handleError() 
            return False 

        ## combined check of kurtosis and elongation
        sourcesCombCheck = 0
        for idx in range(catdata.nrows):
            if catdata['ELONGATION'][idx] > float(self.params['maxCombElongation']) and catdata['KURTOSIS'][idx] > float(self.params['maxCombExKurtosis']):
              sourcesCombCheck += 1
        self.logger.info("(pipeline._extractSources) Number of objects failing combined elongation/kurtosis constraint is " + str(sourcesCombCheck) 
                         + " (" + str(float(self.params['maxSourcesCombCheck'])) + ")")
        if sourcesCombCheck > float(self.params['maxSourcesCombCheck']):
            self.err.setError(7)
            self.err.handleError() 
            return False 

        ## check maximum flux   
        flux = max(catdata['FLUX_MAX'].tonumpy())
        self.logger.info("(pipeline._extractSources) Maximum flux in catalogue is " + str(flux) + " (" + str(self.params['maxFlux']) + ")")
        if flux > float(self.params['maxFlux']):
            self.err.setError(8)
            self.err.handleError()
            return False 
          
        return True
      
    def _XMatchSources(self, in_filename, in_FITS_im, doCatQuery, cat, checkColourIndex=True, checkNumMatchedSources=True):
        '''
        cross match sources with catalogue.

        returns two objects containing lists of source instances (unmatchedSources, matchedSources).
        '''
        matchedSources = []
        unmatchedSources = []
        if not self.RefCatAll:
            if cat == "APASS":
                self.RefCatAll = APASSCatalogue(self.err, self.logger) 
            elif cat == "USNOB":
                self.RefCatAll = USNOBCatalogue(self.err, self.logger)  

        self.logger.info("(pipeline._XMatchSources) Attempting to cross match sources with catalogue")

        matchingTolerance = self.params['matchingTolerance']
        limitingMag = self.params['limitingMag']
        maxNumSourcesXMatch = self.params['maxNumSourcesXMatch']
        searchRadius = self.params['fieldSize']

        # establish if we need to query/requery the database
        ## do we have information of this pointing defined aready?
        
        thisPointing = self._getPointing(in_FITS_im)
        ## ..check that the pointing hasn't changed
        if doCatQuery:
            self.logger.info("(pipeline._XMatchSources) No previous pointing information or pointing has changed since last image.")
            if cat == "APASS":
                self.logger.info("(pipeline._XMatchSources) Querying APASS catalogue at " + in_FITS_im.headers['RA'] + " " 
                                 + in_FITS_im.headers['DEC'] + " with a search radius of " 
                                 + str(searchRadius + float(self.params['pointingDiffThresh'])) + ", " 
                                 + str(searchRadius + float(self.params['pointingDiffThresh'])) + " deg")
            elif cat == "USNOB":
                self.logger.info("(pipeline._XMatchSources) Querying USNOB catalogue at " + in_FITS_im.headers['RA'] 
                                 + " " + in_FITS_im.headers['DEC'] + " with a search radius of " 
                                 + str(searchRadius + float(self.params['pointingDiffThresh'])) + ", " 
                                 + str(searchRadius + float(self.params['pointingDiffThresh'])) + " deg")
                
            self.RefCatAll.query(self.params['path_pw_list'], 
                        self.params['catalogue_credentials_id'], 
                        hms_2_deg(in_FITS_im.headers['RA']), 
                        dms_2_deg(in_FITS_im.headers['DEC']), 
                        searchRadius + self.params['pointingDiffThresh'],
                        limitingMag,
                        maxNumSourcesXMatch
                        )
        else:
            self.logger.info("(pipeline._XMatchSources) Pointing has not changed since last image. Using data from previous query")

        # parse Sextractor catalogue
        sExCat = sExCatalogue(self.err, self.logger)
        sExCat.read(in_filename)

        # do cross match
        self.logger.info("(pipeline._XMatchSources) Cross matching catalogues with a tolerance of " + str(matchingTolerance*3600) + " arcsec")
        matches = pysm.spherematch(sExCat.RA, sExCat.DEC, self.RefCatAll.RA, self.RefCatAll.DEC, tol=matchingTolerance, nnearest=1)
                
        sExCatMatchedIndexes = matches[0]
        RefCatMatchedIndexes = matches[1]

        # find indexes of unmatched sources
        sExCatAllIndexes = np.arange(0, len(sExCat.RA), 1)
        sExCatUnmatchedIndexes = list(set(sExCatAllIndexes) - set(sExCatMatchedIndexes))
        self.logger.info("(pipeline._XMatchSources) Cross matched " + str(len(sExCatMatchedIndexes)) + " source(s)")

        # if set, check number of matched sources is greater than the minimum required
        if checkNumMatchedSources:
            if len(sExCatMatchedIndexes) < int(self.params['minNumMatchedSources']):
                self.err.setError(12)
                self.err.handleError()
                return None, None

        # create a list of matched sources
        numRemovedSourcesColour = 0
        if cat == "APASS":
            for idx in range(len(sExCatMatchedIndexes)):
                # if set, check for sources lying outside of colour limits
                if checkColourIndex:
                    BRColour = self.RefCatAll.BMAG[RefCatMatchedIndexes[idx]] - self.RefCatAll.RMAG[RefCatMatchedIndexes[idx]]
                    if BRColour < float(self.params['lowerColourLimit']) or BRColour > float(self.params['upperColourLimit']):
                        numRemovedSourcesColour = numRemovedSourcesColour + 1
                        continue
                matchedSources.append(source(in_filename, 
                                             sExCat.RA[sExCatMatchedIndexes[idx]], 
                                             sExCat.DEC[sExCatMatchedIndexes[idx]], 
                                             sExCat.X_IMAGE[sExCatMatchedIndexes[idx]], 
                                             sExCat.Y_IMAGE[sExCatMatchedIndexes[idx]], 
                                             sExCat.FLUX_AUTO[sExCatMatchedIndexes[idx]], 
                                             sExCat.FLUXERR_AUTO[sExCatMatchedIndexes[idx]], 
                                             sExCat.MAG_AUTO[sExCatMatchedIndexes[idx]], 
                                             sExCat.MAGERR_AUTO[sExCatMatchedIndexes[idx]], 
                                             sExCat.BACKGROUND[sExCatMatchedIndexes[idx]], 
                                             sExCat.ISOAREA_WORLD[sExCatMatchedIndexes[idx]], 
                                             sExCat.FLAGS[sExCatMatchedIndexes[idx]], 
                                             sExCat.FWHM_WORLD[sExCatMatchedIndexes[idx]], 
                                             sExCat.ELONGATION[sExCatMatchedIndexes[idx]], 
                                             sExCat.ELLIPTICITY[sExCatMatchedIndexes[idx]], 
                                             sExCat.THETA_IMAGE[sExCatMatchedIndexes[idx]], 
                                             APASSCatREF=self.RefCatAll.REF[RefCatMatchedIndexes[idx]], 
                                             APASSCatRA=self.RefCatAll.RA[RefCatMatchedIndexes[idx]], 
                                             APASSCatDEC=self.RefCatAll.DEC[RefCatMatchedIndexes[idx]], 
                                             APASSCatRAERR=self.RefCatAll.RAERR[RefCatMatchedIndexes[idx]], 
                                             APASSCatDECERR=self.RefCatAll.DECERR[RefCatMatchedIndexes[idx]], 
                                             APASSCatVMAG=self.RefCatAll.VMAG[RefCatMatchedIndexes[idx]], 
                                             APASSCatBMAG=self.RefCatAll.BMAG[RefCatMatchedIndexes[idx]], 
                                             APASSCatGMAG=self.RefCatAll.GMAG[RefCatMatchedIndexes[idx]], 
                                             APASSCatRMAG=self.RefCatAll.RMAG[RefCatMatchedIndexes[idx]], 
                                             APASSCatIMAG=self.RefCatAll.IMAG[RefCatMatchedIndexes[idx]], 
                                             APASSCatVMAGERR=self.RefCatAll.VMAGERR[RefCatMatchedIndexes[idx]], 
                                             APASSCatBMAGERR=self.RefCatAll.BMAGERR[RefCatMatchedIndexes[idx]],
                                             APASSCatGMAGERR=self.RefCatAll.GMAGERR[RefCatMatchedIndexes[idx]], 
                                             APASSCatRMAGERR=self.RefCatAll.RMAGERR[RefCatMatchedIndexes[idx]], 
                                             APASSCatIMAGERR=self.RefCatAll.IMAGERR[RefCatMatchedIndexes[idx]],
                                             APASSCatNOBS=self.RefCatAll.NOBS[RefCatMatchedIndexes[idx]])
                ) 
        elif cat == "USNOB":
            for idx in range(len(sExCatMatchedIndexes)):
                # if set, check for sources lying outside of colour limits
                if checkColourIndex:
                    BRColour = self.RefCatAll.B2MAG[RefCatMatchedIndexes[idx]] - self.RefCatAll.R2MAG[RefCatMatchedIndexes[idx]]
                    if BRColour < float(self.params['lowerColourLimit']) or BRColour > float(self.params['upperColourLimit']):
                        numRemovedSourcesColour = numRemovedSourcesColour + 1
                        continue                  
                matchedSources.append(source(in_filename, 
                                             sExCat.RA[sExCatMatchedIndexes[idx]], 
                                             sExCat.DEC[sExCatMatchedIndexes[idx]], 
                                             sExCat.X_IMAGE[sExCatMatchedIndexes[idx]], 
                                             sExCat.Y_IMAGE[sExCatMatchedIndexes[idx]], 
                                             sExCat.FLUX_AUTO[sExCatMatchedIndexes[idx]], 
                                             sExCat.FLUXERR_AUTO[sExCatMatchedIndexes[idx]], 
                                             sExCat.MAG_AUTO[sExCatMatchedIndexes[idx]], 
                                             sExCat.MAGERR_AUTO[sExCatMatchedIndexes[idx]], 
                                             sExCat.BACKGROUND[sExCatMatchedIndexes[idx]], 
                                             sExCat.ISOAREA_WORLD[sExCatMatchedIndexes[idx]], 
                                             sExCat.FLAGS[sExCatMatchedIndexes[idx]], 
                                             sExCat.FWHM_WORLD[sExCatMatchedIndexes[idx]],
                                             sExCat.ELONGATION[sExCatMatchedIndexes[idx]], 
                                             sExCat.ELLIPTICITY[sExCatMatchedIndexes[idx]], 
                                             sExCat.THETA_IMAGE[sExCatMatchedIndexes[idx]], 
                                             USNOBCatREF=self.RefCatAll.REF[RefCatMatchedIndexes[idx]], 
                                             USNOBCatRA=self.RefCatAll.RA[RefCatMatchedIndexes[idx]], 
                                             USNOBCatDEC=self.RefCatAll.DEC[RefCatMatchedIndexes[idx]], 
                                             USNOBCatRAERR=self.RefCatAll.RAERR[RefCatMatchedIndexes[idx]], 
                                             USNOBCatDECERR=self.RefCatAll.DECERR[RefCatMatchedIndexes[idx]],  
                                             USNOBCatR1MAG=self.RefCatAll.R1MAG[RefCatMatchedIndexes[idx]], 
                                             USNOBCatB1MAG=self.RefCatAll.B1MAG[RefCatMatchedIndexes[idx]],
                                             USNOBCatR2MAG=self.RefCatAll.R2MAG[RefCatMatchedIndexes[idx]], 
                                             USNOBCatB2MAG=self.RefCatAll.B2MAG[RefCatMatchedIndexes[idx]])
                )        
        self.logger.info("(pipeline._XMatchSources) Removed " + str(numRemovedSourcesColour) + " source(s) due to colour index constraint")     
                  
        # create a list of unmatched sources
        for idx in range(len(sExCatUnmatchedIndexes)):
            unmatchedSources.append(source(in_filename, sExCat.RA[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.DEC[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.X_IMAGE[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.Y_IMAGE[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.FLUX_AUTO[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.FLUXERR_AUTO[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.MAG_AUTO[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.MAGERR_AUTO[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.BACKGROUND[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.ISOAREA_WORLD[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.FLAGS[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.FWHM_WORLD[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.ELONGATION[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.ELLIPTICITY[sExCatUnmatchedIndexes[idx]], 
                                           sExCat.THETA_IMAGE[sExCatUnmatchedIndexes[idx]])
            )        
        self.logger.info("(pipeline._XMatchSources) Couldn't find a match for " + str(len(sExCatUnmatchedIndexes)) + " source(s)")              
          
        if len(matchedSources) == 0:
            self.err.setError(-9)
            self.err.handleError()
                    
        return matchedSources, unmatchedSources      

    def _calibrateZP(self, matchedSources, cat):
        '''
        find colour dependent magnitude ZPs.

        returns a list of calibration coefficients.
        '''
        magDifference = []
        BRcolour = []
        if cat == "APASS":
            for i in matchedSources:
                BRcolour.append(i.APASSCatBMAG - i.APASSCatRMAG)
                magDifference.append(i.sExCatMagAuto - i.APASSCatRMAG)
        elif cat == "USNOB":
            for i in matchedSources:
                BRcolour.append(i.USNOBCatB2MAG - i.USNOBCatR2MAG)
                magDifference.append(i.sExCatMagAuto - i.USNOBCatR2MAG)          

        # perform linear best fit
        m, c = np.polyfit(BRcolour, magDifference, 1) 

        self.logger.info("(pipeline._calibrateSources) Coefficients of ZP calibration are [" + str(c) + ", " + str(m) + "]")

        return magDifference, BRcolour, (c, m)

    def _storeToPostgresDatabase(self, matchedSources, unmatchedSources, cat):
        '''
        store skycam image and extracted source information
        '''
        try:
            ip, port, username, password = rpf(self.params['path_pw_list'], self.params['skycam_cat_db_credentials_id'])
            port = int(port)
        except IOError:
            self.err.setError(-19)
            self.err.handleError()       
        except TypeError:
            self.err.setError(-20)
            self.err.handleError() 
            
        # create unique set of filenames from matchedSources list
        images = set()
        for source in matchedSources:
            images.add(source.filename)
   
        # process images by filename
        for i in images:
            
            ws_cat = wsc(ip, port, self.err, self.logger) 
            
            im = FITSFile(i, self.err) 
	    im.openFITSFile()
            im.getHeaders(0)
            
            ## ****************
            ## **** images ****
            ## ****************           
            # we do a bit of data cleansing on the headers and replace forward slashes with unicode equivalent 
            # (otherwise REST interface breaks)
            keep = ['DATE-OBS', 'MJD', 'UTSTART', 'RA_CENT', 'DEC_CENT', 'RA_MIN', 'RA_MAX', 'DEC_MIN', 
                    'DEC_MAX', 'CCDSTEMP', 'CCDATEMP', 'AZDMD', 'AZIMUTH', 'ALTDMD', 'ALTITUDE', 'ROTSKYPA']
            headers = {}
            for key, val in im.headers.iteritems():
                if key in keep:
                    try:
                        headers[key.replace('-', '_')] = urllib.quote(val, safe='').strip()
                    except AttributeError:
                        headers[key.replace('-', '_')] = val
            headers['FILENAME'] = os.path.basename(i).strip()
        
            ws_cat.skycam_insert_image(self.params['schemaName'], headers, os.path.basename(i))     # insert
            if ws_cat.status != 200:
                self.err.setError(15)
                self.err.handleError()
                continue 
            res = json.loads(ws_cat.text)
            img_id  = res['img_id']
            img_mjd = res['mjd']

            self.logger.info("(pipeline._storeToPostgresDatabase) Stored image details for " + str(os.path.basename(i)) + " with img_id of " + str(img_id) + " in images table")
            
            ## *****************
            ## **** sources ****
            ## *****************  
            
            ### create list of matched and unmatched sources taken from this image
            im_unmatchedSources = list(source for source in unmatchedSources if source.filename == i)
            im_matchedSources = list(source for source in matchedSources if source.filename == i)
            
            for src in im_unmatchedSources + im_matchedSources:
                s = {}
                s['mjd']            = img_mjd
                s['img_id']         = img_id
                if src.USNOBCatREF is None: 
                    s['usnobref']   = "NULL"
                else:
                    s['usnobref']   = str(src.USNOBCatREF)
                if src.APASSCatREF is None: 
                    s['apassref']   = "NULL"
                else:
                    s['apassref']   = str(src.APASSCatREF)
                s['ra']             = float(src.sExCatRA)
                s['dec']            = float(src.sExCatDEC)
                s['x']              = float(src.sExCatx)
                s['y']              = float(src.sExCaty)
                s['fluxAuto']       = float(src.sExCatFluxAuto)
                s['fluxErrAuto']    = float(src.sExCatFluxErrAuto)
                s['magAuto']        = float(src.sExCatMagAuto)
                s['magErrAuto']     = float(src.sExCatMagErrAuto) 
                s['background']     = float(src.sExCatBackground)
                s['isoareaWorld']   = float(src.sExCatIsoareaWorld)
                s['SEFlags']        = float(src.sExCatSEFlags)
                s['FWHM']           = float(src.sExCatFWHM)
                s['elongation']     = float(src.sExCatElongation)
                s['ellipticity']    = float(src.sExCatEllipticity)
                s['thetaImage']     = float(src.sExCatThetaImage)
                
                ws_cat.skycam_sources_add_to_buffer(self.params['schemaName'], s)       # add to buffer
                if ws_cat.status != 200:
                    self.err.setError(15)
                    self.err.handleError()
                    continue 
                
            ws_cat.skycam_sources_flush_buffer_to_db(self.params['schemaName'])         # insert
            if ws_cat.status != 200:
                self.err.setError(15)
                self.err.handleError()
                continue 
            
            self.logger.info("(pipeline._storeToPostgresDatabase) Stored source details for " + str(os.path.basename(i)) + " with img_id of " + str(img_id) + " in sources table")
                
            im.closeFITSFile() 
            
            

