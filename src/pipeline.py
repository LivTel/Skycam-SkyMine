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
from pyspherematch import _great_circle_distance as gcd

class pipeline():
    def __init__(self, params, err, logger):
        self.params 		= params
        self.err		= err
        self.logger		= logger
        
        self.lastPointing       = []
        
        # the following catalogues are kept in the constructor so that they are not reinitialised every time 
        # pipeline.run() is invoked. this is important for sync operations
        self.RefCatAll          = {}                                                                  # reference catalogues to match against
        self.SkycamCat          = SkycamCatalogue(self.err, self.logger, self.params['schemaName'])   # required if we're amending the Skycam catalogue table (if --sdb is set)

    def run(self, images):
        '''
        run the sequence
        '''
        self.logger.info("(pipeline.run) Starting run")
        
        # init instances of catalogues and append to RefCatAll. 
        # this is done to avoid having to requery the same pointing
        if not self.RefCatAll:  # first we check if it's empty, this is important for sync runs
            for c in self.params['cat']:
                if c == "APASS":
                    self.RefCatAll[c] = APASSCatalogue(self.err, self.logger) 
                elif c == "USNOB":
                    self.RefCatAll[c] = USNOBCatalogue(self.err, self.logger)    

        doCatQuery = True     # this keeps track of whether we need to perform a new catalogue query
        valid_images = []
        for idx, f in enumerate(images):
            self.logger.info("(pipeline.run) processing file " + str(idx+1) + " of " + str(len(images)) + " (" + os.path.basename(f) + ")")
            im = FITSFile(f, self.err) 
            im.openFITSFile()
            im.getHeaders(0)     
            if self._hasValidWCS(im):                                                                                  # checks that we have a valid WCS
                if not self._hasPointingChanged(im):                                                                   # checks that pointing hasn't changed
                    sourceList = self._extractSources(f, im)                                                           # extract sources
                    ZPs = {}                                                                                           # we store ZP for each reference catalogue
                    ZP_COEFFS = {}                                                                                     # and also ZP coeffs for each reference catalogue
                    for c in self.params['cat']:
                        sources = self._XMatchSources(im, doCatQuery, cat=self.RefCatAll[c], sources=sourceList)       # multiple catalogue cross-matching 
                        if sources is not None:                                                                        # did we match anything?
                            magDifference, BRcolour, zp_coeffs, V = self._calibrateZP(sources, cat=c)                  # frame zeropoint calculation
                            zp_stdev = np.sqrt(V[1,1])                                                                 # variance is last element of covariance matrix
                            ZPs[c] = (zp_coeffs[1], zp_stdev)                                                          # for zero colour term, take intercept
                            ZP_COEFFS[c] = zp_coeffs
                            if self.params['makePlots']:
                                plotZPCalibration(magDifference, BRcolour, ZPs[c],                                     # plots
                                                  float(self.params['lowerColourLimit']), 
                                                  float(self.params['upperColourLimit']), 
                                                  self.logger, 
                                                  hard=True, 
                                                  outImageFilename=self.params['resPath'] + os.path.basename(f) + "." + c + ".calibration.png", 
                                                  outDataFilename=self.params['resPath'] + os.path.basename(f) + "." + c + ".data.calibration", 
                                                  )
                    if self.params['storeToDB']:
                        sources = self._XMatchSources(im, True, cat=self.SkycamCat, sources=sourceList)   # match sources with preexisting Skycam catalogue, always requery
                        self._storeToPostgresDatabase(f, sourceList, ZPs, ZP_COEFFS)                      # store to database
                    if not self.params['forceCatalogueQuery']:
                        doCatQuery = False
                    valid_images.append(f)
                else:                                                                                     # skip processing file if pointing has changed
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
        
        returns a list of source instances (w/ unpopulated reference catalogue fields).
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
          
        # parse sExtractor catalogue
        sExCat = sExCatalogue(self.err, self.logger)
        sExCat.read(in_filename)        
        
        sources = []
        # create a list of source instances from each sExtracted source
        # with Nonetype cross-match catalogue variables
        for i in range(len(sExCat.RA)):
            sources.append(source(in_filename, 
                                  sExCat.RA[i], 
                                  sExCat.DEC[i], 
                                  sExCat.X_IMAGE[i], 
                                  sExCat.Y_IMAGE[i], 
                                  sExCat.FLUX_AUTO[i], 
                                  sExCat.FLUXERR_AUTO[i], 
                                  sExCat.MAG_AUTO[i], 
                                  sExCat.MAGERR_AUTO[i], 
                                  sExCat.BACKGROUND[i], 
                                  sExCat.ISOAREA_WORLD[i], 
                                  sExCat.FLAGS[i], 
                                  sExCat.FWHM_WORLD[i], 
                                  sExCat.ELONGATION[i], 
                                  sExCat.ELLIPTICITY[i], 
                                  sExCat.THETA_IMAGE[i]
                                  )
            )              
          
        return sources
    
    def _XMatchSources(self, in_FITS_im, doCatQuery, cat, sources, checkColourIndex=True, checkNumMatchedSources=True):
        '''
        cross-match sources with catalogue(s).

        returns a list of source instances (w/ reference catalogue fields filled).
        '''
        self.logger.info("(pipeline._XMatchSources) Cross-matching sources with " + cat.NAME + " catalogue")
        
        # set cross-matching parameters
        matchingTolerance   = self.params['matchingTolerance']
        limitingMag         = self.params['limitingMag']
        maxNumSourcesXMatch = self.params['maxNumSourcesXMatch']
        searchRadius        = self.params['fieldSize']
        # requery catalogue and cross-match if pointing has changed
        if doCatQuery:
            self.logger.info("(pipeline._XMatchSources) No previous pointing information, user has forced always-do catalogue queries or pointing has changed since last image")
            self.logger.info("(pipeline._XMatchSources) Querying " + cat.NAME + " catalogue at " + in_FITS_im.headers['RA'] 
                             + " " + in_FITS_im.headers['DEC'] + " with a search radius of " 
                             + str(searchRadius + float(self.params['pointingDiffThresh'])) + ", " 
                             + str(searchRadius + float(self.params['pointingDiffThresh'])) + " deg")
                
            cat.query(self.params['path_pw_list'], 
                        self.params['catalogue_credentials_id'], 
                        hms_2_deg(in_FITS_im.headers['RA']), 
                        dms_2_deg(in_FITS_im.headers['DEC']), 
                        searchRadius + self.params['pointingDiffThresh'],
                        limitingMag,
                        maxNumSourcesXMatch
                        )
        else:
            self.logger.info("(pipeline._XMatchSources) Pointing has not changed since last image. Using data from previous query")

        # do cross-match
        if len(cat.RA) > 0:
            self.logger.info("(pipeline._XMatchSources) Cross-matching catalogues with a tolerance of " + str(matchingTolerance*3600) + " arcsec")
            matches = pysm.spherematch([s.sExCatRA for s in sources], [s.sExCatDEC for s in sources], cat.RA, cat.DEC, tol=matchingTolerance, nnearest=1)
                
            sourcesMatchedIndexes = matches[0]
            RefCatMatchedIndexes = matches[1]
        
            self.logger.info("(pipeline._XMatchSources) Cross-matched " + str(len(sourcesMatchedIndexes)) + " source(s)")
        else:
            self.err.setError(17)
            self.err.handleError()
            return None

        # if set, check number of matched sources is greater than the minimum required
        if checkNumMatchedSources:
            if len(sourcesMatchedIndexes) < int(self.params['minNumMatchedSources']):
                self.err.setError(12)
                self.err.handleError()
                return None

        # populate cross-matched catalogue variables for each source
        numRemovedSourcesColour = 0
        numUnmatchedSources = 0
        for source_idx in range(len(sources)):                                     # for every source in the source list...
            if source_idx in sourcesMatchedIndexes:                                # .. has it been cross-matched to the catalogue?
                thisMatchedIndex    = np.where(sourcesMatchedIndexes==source_idx)  # and if so, what index?
                thisSourcesIndex    = sourcesMatchedIndexes[thisMatchedIndex]      # set the corresponding sources index
                thisCatIndex        = RefCatMatchedIndexes[thisMatchedIndex]       # set the corresponding reference catalogue index
                if cat.NAME == "APASS":    
                    ## if set, check for sources lying outside of colour limits
                    if checkColourIndex:
                        BRColour = cat.BMAG[thisCatIndex] - cat.RMAG[thisCatIndex]
                        if BRColour < float(self.params['lowerColourLimit']) or BRColour > float(self.params['upperColourLimit']):
                            numRemovedSourcesColour = numRemovedSourcesColour + 1
                            numUnmatchedSources = numUnmatchedSources + 1
                            continue     
                    ## update source information with cross-matched catalogue details
                    sources[thisSourcesIndex].APASSCatREF=cat.REF[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatRA=cat.RA[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatDEC=cat.DEC[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatRAERR=cat.RAERR[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatDECERR=cat.DECERR[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatVMAG=cat.VMAG[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatBMAG=cat.BMAG[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatGMAG=cat.GMAG[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatRMAG=cat.RMAG[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatIMAG=cat.IMAG[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatVMAGERR=cat.VMAGERR[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatBMAGERR=cat.BMAGERR[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatGMAGERR=cat.GMAGERR[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatRMAGERR=cat.RMAGERR[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatIMAGERR=cat.IMAGERR[thisCatIndex]
                    sources[thisSourcesIndex].APASSCatNOBS=cat.NOBS[thisCatIndex]     
                    sources[thisSourcesIndex].APASSCatXMatchDist=gcd(cat.RA[thisCatIndex],
                                                                     cat.DEC[thisCatIndex],
                                                                     sources[thisSourcesIndex].sExCatRA,
                                                                     sources[thisSourcesIndex].sExCatDEC)*3600
                elif cat.NAME == "USNOB":
                    ## if set, check for sources lying outside of colour limits
                    if checkColourIndex:
                        BRColour = cat.B1MAG[thisCatIndex] - cat.R1MAG[thisCatIndex]
                        if BRColour < float(self.params['lowerColourLimit']) or BRColour > float(self.params['upperColourLimit']):
                            numRemovedSourcesColour = numRemovedSourcesColour + 1
                            numUnmatchedSources = numUnmatchedSources + 1
                            continue
                          
                    ## update source information with cross-matched catalogue details
                    sources[thisSourcesIndex].USNOBCatREF=cat.REF[thisCatIndex]
                    sources[thisSourcesIndex].USNOBCatRA=cat.RA[thisCatIndex]
                    sources[thisSourcesIndex].USNOBCatDEC=cat.DEC[thisCatIndex]
                    sources[thisSourcesIndex].USNOBCatRAERR=cat.RAERR[thisCatIndex]
                    sources[thisSourcesIndex].USNOBCatDECERR=cat.DECERR[thisCatIndex]
                    sources[thisSourcesIndex].USNOBCatR1MAG=cat.R1MAG[thisCatIndex]
                    sources[thisSourcesIndex].USNOBCatB1MAG=cat.B1MAG[thisCatIndex]
                    sources[thisSourcesIndex].USNOBCatR2MAG=cat.R2MAG[thisCatIndex]
                    sources[thisSourcesIndex].USNOBCatB2MAG=cat.B2MAG[thisCatIndex]  
                    sources[thisSourcesIndex].USNOBCatXMatchDist=gcd(cat.RA[thisCatIndex],
                                                                     cat.DEC[thisCatIndex],
                                                                     sources[thisSourcesIndex].sExCatRA,
                                                                     sources[thisSourcesIndex].sExCatDEC)*3600
                elif cat.NAME == "skycamz" or cat.NAME == "skycamt":
                    sources[thisSourcesIndex].SKYCAMCatREF=cat.REF[thisCatIndex]
                    sources[thisSourcesIndex].SKYCAMCatRA=cat.RA[thisCatIndex] 
                    sources[thisSourcesIndex].SKYCAMCatDEC=cat.DEC[thisCatIndex]
                    sources[thisSourcesIndex].SKYCAMCatRAERR=cat.RAERR[thisCatIndex]
                    sources[thisSourcesIndex].SKYCAMCatDECERR=cat.DECERR[thisCatIndex]
                    sources[thisSourcesIndex].SKYCAMCatAPASSREF=cat.APASSREF[thisCatIndex]
                    sources[thisSourcesIndex].SKYCAMCatUSNOBREF=cat.USNOBREF[thisCatIndex]
                    sources[thisSourcesIndex].SKYCAMCatNOBS=cat.NOBS[thisCatIndex]
                    sources[thisSourcesIndex].SKYCAMCatAPASSBRCOLOUR=cat.APASSXMATCHBRCOLOUR[thisCatIndex]
                    sources[thisSourcesIndex].SKYCAMCatUSNOBBRCOLOUR=cat.USNOBXMATCHBRCOLOUR[thisCatIndex]
                    sources[thisSourcesIndex].SKYCAMCatROLLINGMEANAPASSMAG=cat.ROLLINGMEANAPASSMAG[thisCatIndex]
                    sources[thisSourcesIndex].SKYCAMCatROLLINGSTDEVAPASSMAG=cat.ROLLINGSTDEVAPASSMAG[thisCatIndex]   
                    sources[thisSourcesIndex].SKYCAMCatROLLINGMEANUSNOBMAG=cat.ROLLINGMEANUSNOBMAG[thisCatIndex] 
                    sources[thisSourcesIndex].SKYCAMCatROLLINGSTDEVUSNOBMAG=cat.ROLLINGSTDEVUSNOBMAG[thisCatIndex]
                    sources[thisSourcesIndex].SKYCAMCatAPASSNUMTIMESSWITCHED=cat.APASSNUMTIMESSWITCHED[thisCatIndex] 
                    sources[thisSourcesIndex].SKYCAMCatUSNOBNUMTIMESSWITCHED=cat.USNOBNUMTIMESSWITCHED[thisCatIndex]
                else:
                    numUnmatchedSources = numUnmatchedSources + 1
            else:
                numUnmatchedSources = numUnmatchedSources + 1  
                
        self.logger.info("(pipeline._XMatchSources) Removed " + str(numRemovedSourcesColour) + " source(s) due to colour index constraint")     
        self.logger.info("(pipeline._XMatchSources) Couldn't find a match for " + str(numUnmatchedSources) + " source(s)")              
          
        if len(sources) - numUnmatchedSources == 0:
            self.err.setError(16)
            self.err.handleError()
            return None
            
        return sources   

    def _calibrateZP(self, sources, cat):
        '''
        find colour dependent magnitude ZPs.

        returns a list of calibration coefficients.
        '''
        magDifference = []
        BRcolour = []
        if cat == "APASS":
            matchedSources = [s for s in sources if s.APASSCatREF is not None]
            for i in matchedSources:
                BRcolour.append(i.APASSCatBMAG - i.APASSCatRMAG)
                magDifference.append(i.sExCatMagAuto - i.APASSCatRMAG)
        elif cat == "USNOB":
            matchedSources = [s for s in sources if s.USNOBCatREF is not None]
            for i in matchedSources:
                BRcolour.append(i.USNOBCatB2MAG - i.USNOBCatR2MAG)
                magDifference.append(i.sExCatMagAuto - i.USNOBCatR2MAG)          

        # perform linear best fit
        coeffs, V = np.polyfit(BRcolour, magDifference, 1, cov=True) 

        self.logger.info("(pipeline._calibrateSources) Coefficients of ZP calibration are [" + str(coeffs[0]) + ", " + str(coeffs[1]) + "]")

        return magDifference, BRcolour, coeffs, V

    def _storeToPostgresDatabase(self, f, sources, ZPs, ZP_COEFFS):
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
 
        ws_cat = wsc(ip, port, self.err, self.logger) 
        
        # check we haven't already processed this frame
        '''ws_cat.skycam_images_get_by_filename(self.params['schemaName'], os.path.basename(f))
        if ws_cat.status != 200:
            self.err.setError(15)
            self.err.handleError()
            return False  
        res = json.loads(ws_cat.text)
        img_count = int(res[0]['count'])'''
        img_count = 0
        if img_count > 0:
            self.err.setError(18)
            self.err.handleError()  
            return False
        else:
            im = FITSFile(f, self.err) 
            im.openFITSFile()
            im.getHeaders(0)
                
            ## *******************************
            ## **** skycam[tz?].catalogue ****
            ## *******************************           
            # we do a bit of data cleansing on the headers and replace forward slashes with unicode equivalent 
            # (otherwise REST interface breaks)
            keep = ['DATE-OBS', 'MJD', 'UTSTART', 'RA_CENT', 'DEC_CENT', 'RA_MIN', 'RA_MAX', 'DEC_MIN', 
                    'DEC_MAX', 'CCDSTEMP', 'CCDATEMP', 'AZDMD', 'AZIMUTH', 'ALTDMD', 'ALTITUDE', 'ROTSKYPA']
            values = {}
            for key, val in im.headers.iteritems():
                if key in keep:
                    try:
                        values[key.replace('-', '_')] = urllib.quote(val, safe='').strip()
                    except AttributeError:
                        values[key.replace('-', '_')] = val
            values['FILENAME'] = os.path.basename(f).strip()
            
            # add frame zeropoint fields at zero colour term
            for key, val in ZPs.iteritems():
                values["FRAME_ZP_" + key] = val[0]
                values["FRAME_ZP_STDEV_" + key] = val[1]
                
            # call web service to insert image
            ws_cat.skycam_images_insert(self.params['schemaName'], values, os.path.basename(f))
            if ws_cat.status != 200:
                self.err.setError(15)
                self.err.handleError()
                return False

            res = json.loads(ws_cat.text)
            img_id  = res['img_id']
            img_mjd = res['mjd']

            self.logger.info("(pipeline._storeToPostgresDatabase) Stored image details for " + str(os.path.basename(f)) + " with img_id of " + str(img_id) + " in images table")
                
            ## *******************************
            ## **** skycam[tz?].catalogue ****
            ## *******************************    
            numNewSkycamCatalogueSources         = 0
            numIncrementedSkycamCatalogueSources = 0
            for s in sources:
                # ------
                # UPSERT.
                # we let database ON CONFLICT clause deal with whether this is an update or insert
                # ------
                values = {}
                if s.SKYCAMCatREF == None:                                                       # this source doesn't exist in the catalogue
                    values['skycamref']                       = None
                    values['xmatch_apassref']                 = s.APASSCatREF
                    values['xmatch_apass_distasec']           = s.APASSCatXMatchDist
                    values['xmatch_usnobref']                 = s.USNOBCatREF
                    values['xmatch_usnob_distasec']           = s.USNOBCatXMatchDist
                    values['radeg']                           = s.sExCatRA
                    values['decdeg']                          = s.sExCatDEC
                    values['raerrasec']                       = 0                                 # we calculate an error when we have > 1 observation
                    values['decerrasec']                      = 0                                 # 
                    values['nobs']                            = 1   
                    values['xmatch_apass_brcolour']           = None
                    values['xmatch_apass_ntimesswitched']     = 0
                    values['xmatch_usnob_brcolour']           = None
                    values['xmatch_usnob_ntimesswitched']     = 0
                    
                    ## calculate magnitude from colour-dependent zp
                    ### APASS
                    if s.APASSCatREF is not None:                                                 # we can use the APASS colour terms
                        values['xmatch_apass_brcolour']       = s.APASSCatBMAG-s.APASSCatRMAG
                        zp = np.polyval(ZP_COEFFS['APASS'], values['xmatch_apass_brcolour'])
                    else:
                        zp = np.polyval(ZP_COEFFS['APASS'], 1.5)                                  # else we assign an average ZP using colour of 1.5
                    calibrated_mag = s.sExCatMagAuto-zp
                    values['xmatch_apass_rollingmeanmag']     = calibrated_mag
                    values['xmatch_apass_rollingstdevmag']    = 0                                 # we calculate an error when we have > 1 observation
                    
                    ### USNOB
                    if s.USNOBCatREF is not None:                                                 # we can use the USNOB colour terms
                        values['xmatch_usnob_brcolour']       = s.USNOBCatB1MAG-s.USNOBCatR1MAG
                        zp = np.polyval(ZP_COEFFS['USNOB'], values['xmatch_usnob_brcolour'])
                    else:
                        zp = np.polyval(ZP_COEFFS['USNOB'], 1.5)                                  # else we assign an average ZP using colour of 1.5
                    calibrated_mag = s.sExCatMagAuto-zp                   
                    values['xmatch_usnob_rollingmeanmag']     = calibrated_mag
                    values['xmatch_usnob_rollingstdevmag']    = 0                                 # we calculate an error when we have > 1 observation   
                    
                    numNewSkycamCatalogueSources              = numNewSkycamCatalogueSources + 1
                else:                                                                             # this source already exists in the catalogue
                    values['skycamref']                       = s.SKYCAMCatREF
                    if str(s.APASSCatREF) != str(s.SKYCAMCatAPASSREF):                            # found different APASS reference
                      values['xmatch_apass_ntimesswitched']   = int(s.SKYCAMCatAPASSNUMTIMESSWITCHED)+1
                    else:
                      values['xmatch_apass_ntimesswitched']   = s.SKYCAMCatAPASSNUMTIMESSWITCHED
                    if str(s.USNOBCatREF) != s.SKYCAMCatUSNOBREF:                                 # found different USNOB reference
                      values['xmatch_usnob_ntimesswitched']   = int(s.SKYCAMCatUSNOBNUMTIMESSWITCHED)+1
                    else:
                      values['xmatch_usnob_ntimesswitched']   = s.SKYCAMCatUSNOBNUMTIMESSWITCHED
                    values['xmatch_apassref']                 = s.APASSCatREF
                    values['xmatch_apass_distasec']           = s.APASSCatXMatchDist
                    values['xmatch_usnobref']                 = s.USNOBCatREF
                    values['xmatch_usnob_distasec']           = s.USNOBCatXMatchDist
                    values['radeg']       = calc_rolling_mean(s.SKYCAMCatRA, s.sExCatRA, s.SKYCAMCatNOBS+1)
                    values['raerrasec']   = calc_rolling_stdev(s.SKYCAMCatRAERR, s.sExCatRA*3600, s.SKYCAMCatRA*3600, values['radeg']*3600, s.SKYCAMCatNOBS+1)  
                    values['decdeg']      = calc_rolling_mean(s.SKYCAMCatDEC, s.sExCatDEC, s.SKYCAMCatNOBS+1)
                    values['decerrasec']  = calc_rolling_stdev(s.SKYCAMCatDECERR, s.sExCatDEC*3600, s.SKYCAMCatDEC*3600, values['decdeg']*3600, s.SKYCAMCatNOBS+1)                     
                    values['nobs']                            = s.SKYCAMCatNOBS+1
                    values['xmatch_apass_brcolour']           = None
                    values['xmatch_usnob_brcolour']           = None
                    
                    ## calculate magnitude from colour-dependent zp
                    ### APASS
                    if s.APASSCatREF is not None:                                                 # we can use the APASS colour terms
                        values['xmatch_apass_brcolour']       = s.APASSCatBMAG-s.APASSCatRMAG
                        zp = np.polyval(ZP_COEFFS['APASS'], values['xmatch_apass_brcolour'])
                    else:
                        zp = np.polyval(ZP_COEFFS['APASS'], 1.5)                                  # else we assign an average ZP using colour of 1.5
                    calibrated_mag = s.sExCatMagAuto-zp
                    values['xmatch_apass_rollingmeanmag']     = calc_rolling_mean(s.SKYCAMCatROLLINGMEANAPASSMAG, calibrated_mag, s.SKYCAMCatNOBS+1)
                    values['xmatch_apass_rollingstdevmag']    = calc_rolling_stdev(s.SKYCAMCatROLLINGSTDEVAPASSMAG, calibrated_mag, s.SKYCAMCatROLLINGMEANAPASSMAG, 
                                                                                   values['xmatch_apass_rollingmeanmag'], s.SKYCAMCatNOBS+1)
                    ### USNOB
                    if s.USNOBCatREF is not None:                                                 # we can use the USNOB colour terms
                        values['xmatch_usnob_brcolour']       = s.USNOBCatB1MAG-s.USNOBCatR1MAG
                        zp = np.polyval(ZP_COEFFS['USNOB'], values['xmatch_usnob_brcolour'])
                    else:
                        zp = np.polyval(ZP_COEFFS['USNOB'], 1.5)                                  # else we assign an average ZP using colour of 1.5
                    calibrated_mag = s.sExCatMagAuto-zp                   
                    values['xmatch_usnob_rollingmeanmag']     = calc_rolling_mean(s.SKYCAMCatROLLINGMEANUSNOBMAG, calibrated_mag, s.SKYCAMCatNOBS+1)
                    values['xmatch_usnob_rollingstdevmag']    = calc_rolling_stdev(s.SKYCAMCatROLLINGSTDEVUSNOBMAG, calibrated_mag, s.SKYCAMCatROLLINGMEANUSNOBMAG, 
                                                                                   values['xmatch_usnob_rollingmeanmag'], s.SKYCAMCatNOBS+1)  
                    numIncrementedSkycamCatalogueSources      = numIncrementedSkycamCatalogueSources + 1
                
                ## call web service to add catalogue source to buffer
                ws_cat.skycam_catalogue_add_to_buffer(self.params['schemaName'], values)
                if ws_cat.status != 200:
                    self.err.setError(15)
                    self.err.handleError()
                    return False                
            
            ## call web service to flush catalogue source buffer to database
            ws_cat.skycam_catalogue_flush_buffer_to_db(self.params['schemaName'])
            if ws_cat.status != 200:
                self.err.setError(15)
                self.err.handleError()
                return False
            self.logger.info("(pipeline._storeToPostgresDatabase) " + str(numNewSkycamCatalogueSources) + " new Skycam source(s) added to catalogue")
                
            im.closeFITSFile()    
