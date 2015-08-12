'''
name:		mine.py
author:		rmb

description: 	A class to mine skycam data to a database
'''
import logging
import os
import math

from database import database_postgresql
from errors import errors
from FITSFile import FITSFile

class postgresql_skycam_mine():
    def __init__(self, db_postgresql, schemaName, logger, err):
        self.db = db_postgresql
        self.schemaName = schemaName
        self.logger = logger
        self.err = err

    def setup(self):
        '''
        setup database schema with its corresponding tables, views, functions and indexes.
        '''
        self.db.create_schema(self.schemaName)
        self._makeTables()
        self._makeViewsAndFunctions()
        self._makeIndexes()

    def destroy(self):
        '''
        destroy database schema.
        '''
        self.db.drop_schema(self.schemaName)

    def insertImage(self, imagePath):
        '''
        insert a single image into the database.
        '''
        ## get headers from image file
        im = FITSFile(imagePath, self.err) 
	im.openFITSFile()
        im.getHeaders(0)
        img_date = im.headers["DATE-OBS"].strip()
        mjd = im.headers["MJD"].strip()
        utstart = im.headers["UTSTART"].strip()
        ra_cent = im.headers["RA_CENT"]
        dec_cent = im.headers["DEC_CENT"]
        ra_min = im.headers["RA_MIN"]
        ra_max = im.headers["RA_MAX"]
        dec_min = im.headers["DEC_MIN"]
        dec_max = im.headers["DEC_MAX"]
        ccdstemp = im.headers["CCDSTEMP"] 	# CCD setpoint
        ccdatemp = im.headers["CCDATEMP"] 	# CCD actual temperature
        azdmd = im.headers["AZDMD"]		# Azimuth demand
        azimuth = im.headers["AZIMUTH"] 	# Azimuth actual
        altdmd = im.headers["ALTDMD"]		# Azimuth demand
        altitude = im.headers["ALTITUDE"] 	# Azimuth actual
        rotskypa = im.headers["ROTSKYPA"]	# Position angle
        im.closeFITSFile()

        filename = os.path.basename(imagePath)

        cmd = "INSERT INTO " + self.schemaName + ".images(img_date, img_rundate, mjd, utstart, ra_cent, dec_cent, ra_min, ra_max, dec_min, dec_max, ccdstemp, ccdatemp, azdmd, azimuth, altdmd, altitude, rotskypa, filename) VALUES ('" + str(img_date) + "', NOW(), " + str(mjd) + ", '" + str(utstart) + "', " + str(ra_cent) + ", " + str(dec_cent) + ", " + str(ra_min) + ", " + str(ra_max) + ", " + str(dec_min) + ", " + str(dec_max) + ", " + str(ccdstemp) + ", " + str(ccdatemp) + ", " + str(azdmd) + ", " + str(azimuth) + ", " + str(altdmd) + ", " + str(altitude) + ", " + str(rotskypa) + ", '" + str(filename) + "')"
        res = self.db.execute(cmd)
        insertedRows = res.rowcount
        if insertedRows:
            self.logger.info("(postgresql_skycam_mine.insertImage) Stored image details for " + str(filename) + " in database")
            cmd = "SELECT img_id FROM " + self.schemaName + ".images WHERE filename = '" + str(filename) + "'"
            res = self.db.read(cmd).fetchall()
            return res[0][0]
        else:
            self.err.setError(10)
            self.err.handleError()
            return None

    def insertMatchedUSNOBObjects(self, cat):
        '''
        insert the contents of a USNOBCatalogue instance into the .matchedUSNOBObjects table.
        '''
        count = 0
        for i in range(len(cat.REF)):
            # unpack object data
            ref = cat.REF[i]
            ra = cat.RA[i]
            dec = cat.DEC[i]
            epoch = cat.EPOCH[i]
            r2_mag = cat.R2MAG[i]  
            b2_mag = cat.B2MAG[i]  
            # establish if USNOB object already exists in the table
            cmd = "SELECT count(*) FROM " + self.schemaName + ".matchedUSNOBObjects WHERE usnoref_int = " + str(ref.replace("-", ""))
            res = self.db.read(cmd).fetchall()
            if res[0][0] == 0:	# it doesn't	
                cmd = "INSERT INTO " + self.schemaName + ".matchedUSNOBObjects(usnoref, usnoref_int, ra, dec, epoch, b2_mag, r2_mag, pos) VALUES ('" + str(ref) + "', " + str(ref.replace("-", "")) + ", " + str(ra) + ", " + str(dec) + ", " + str(epoch) + ", " + str(b2_mag) + ", " + str(r2_mag) + ", spoint(" + str(math.radians(ra)) + ", " + str(math.radians(dec)) + ") )"
                res = self.db.execute(cmd)
                count = count + 1 
        self.logger.info("(postgresql_skycam_mine.insertMatchedUSNOBObjects) Stored " + str(count) + " new matched USNOB objects into database")
        
    def insertMatchedAPASSObjects(self, cat):
        '''
        insert the contents of an APASSCatalogue instance into the .matchedAPASSObjects table.
        '''
        count = 0
        for i in range(len(cat.REF)):
            # unpack object data
            ref = cat.REF[i]
            ra = cat.RA[i]
            dec = cat.DEC[i]
            raerr = cat.RAERR[i]
            decerr = cat.DECERR[i]
            vmag = cat.VMAG[i]
            bmag = cat.BMAG[i]          
            gmag = cat.GMAG[i]
            rmag = cat.RMAG[i] 
            imag = cat.IMAG[i]    
            vmagerr = cat.VMAGERR[i]
            bmagerr = cat.BMAGERR[i]
            gmagerr = cat.GMAGERR[i]
            rmagerr = cat.RMAGERR[i]
            imagerr = cat.IMAGERR[i] 
            # establish if APASS object already exists in the table
            cmd = "SELECT count(*) FROM " + self.schemaName + ".matchedAPASSObjects WHERE apassref = " + str(ref)
            res = self.db.read(cmd).fetchall()
            if res[0][0] == 0:  # it doesn't    
                cmd = "INSERT INTO " + self.schemaName + ".matchedAPASSObjects(apassref, ra, dec, ra_err, dec_err, v_mag, b_mag, g_mag, r_mag, i_mag, v_mag_err, b_mag_err, g_mag_err, r_mag_err, i_mag_err, pos) VALUES ('" + str(ref) + "', " + str(ra) + ", " + str(dec) + ", " + str(raerr) + ", " + str(decerr) + ", " + str(vmag) + ", " + str(bmag) + ", " + str(gmag) + ", " + str(rmag) + ", " + str(imag) + ", " + str(vmagerr) + ", " + str(bmagerr) + ", " + str(gmagerr) + ", " + str(rmagerr) + ", " + str(imagerr) + ", spoint(" + str(math.radians(ra)) + ", " + str(math.radians(dec)) + ") )"
                res = self.db.execute(cmd)
                count = count + 1 
        self.logger.info("(postgresql_skycam_mine.insertMatchedAPASSObjects) Stored " + str(count) + " new matched APASS objects into database")        

    def insertSources(self, imagePath, img_id, sources):
        '''
        bulk insert a list of source objects into the .sources table by first iteratively concatenating the data into a single values clause.
        '''
        ## get headers from image file
        im = FITSFile(imagePath, self.err) 
	im.openFITSFile()
        im.getHeaders(0)
        mjd = im.headers["MJD"].strip()
        im.closeFITSFile()
        valuesClause = ""
        count = 0
        for src in sources: 
            if src.USNOBCatREF is None: 
                ref = "NULL"
            else:
                ref = "'" + str(src.USNOBCatREF) + "'"
            ra = float(src.sExCatRA)
            dec = float(src.sExCatDEC)
            x = float(src.sExCatx)
            y = float(src.sExCaty)
            fluxAuto = float(src.sExCatFluxAuto)
            fluxErrAuto = float(src.sExCatFluxErrAuto)
            magAuto = float(src.sExCatMagAuto)
            magErrAuto = float(src.sExCatMagErrAuto) 
            background = float(src.sExCatBackground)
            isoareaWorld = float(src.sExCatIsoareaWorld)
            SEFlags = float(src.sExCatSEFlags)
            FWHM = float(src.sExCatFWHM)
            elongation = float(src.sExCatElongation)
            ellipticity = float(src.sExCatEllipticity)
            thetaImage = float(src.sExCatThetaImage)

            valuesClause += "(" + str(img_id) + ", " + str(mjd) + ", " + str(ra) + ", " + str(dec) + ", " + str(x) + ", " + str(y) + ", " + str(fluxAuto) + ", " + str(fluxErrAuto) + ", " + str(magAuto) + ", " + str(magErrAuto) + ", " + str(background) + ", " + str(isoareaWorld) + ", " + str(SEFlags) + ", " + str(FWHM) + ", " + str(elongation) + ", " + str(ellipticity) + ", " + str(thetaImage) + ", " + str(ref) + ", " + str(ref).replace("-", "") + ", spoint(" + str(math.radians(ra)) + ", " + str(math.radians(dec)) + ") )"
            valuesClause += ", "
            count = count + 1
        # insert sources into database if clause is non-empty
        if valuesClause:
            valuesClause = valuesClause.rstrip(", ")
            cmd = "INSERT INTO " + self.schemaName + ".sources(img_id, mjd, ra, dec, x_pix, y_pix, flux, flux_err, inst_mag, inst_mag_err, background, isoarea_world, seflags, fwhm, elongation, ellipticity, theta_image, usnoref, usnoref_int, pos) VALUES " + valuesClause
            res = self.db.execute(cmd)
            self.logger.info("(postgresql_skycam_mine.insertSources) Stored " + str(count) + " new sources into database")

    def deleteImageByFilename(self, imageFilename):
        '''
        delete image from .images table given an image filename.
        '''
        # get observation id from image filename
        query = "SELECT img_id FROM " + self.schemaName + ".images WHERE filename = '" + str(imageFilename) + "'"
        res = self.db.read(query).fetchall()
        imgID = res[0][0] 
        # delete rows from .images table
        query = "DELETE FROM " + self.schemaName + ".images WHERE img_id = " + str(imgID)
        deletedRows = self.db.execute(query).rowcount
        if deletedRows:
            self.logger.info("(postgresql_skycam_mine.deleteImageByFilename) Deleted image " + str(imageFilename) + " from .images table")

    def deleteSourcesByFilename(self, imageFilename):
        '''
        delete sources from .sources table given an image filename.
        '''
        # get observation id from image filename
        query = "SELECT img_id FROM " + self.schemaName + ".images WHERE filename = '" + str(imageFilename) + "'"
        res = self.db.read(query).fetchall()
        imgID = res[0][0] 
        # delete rows from .sources table
        query = "DELETE FROM " + self.schemaName + ".sources WHERE img_id = " + str(imgID)
        deletedRows = self.db.execute(query).rowcount
        if deletedRows:
            self.logger.info("(postgresql_skycam_mine.deleteSourcesByFilename) Deleted sources from image '" + str(imageFilename) + "' from .sources table")

    ###
    ### setup() WRAPPERS
    ###
    def _makeTables(self):
        '''
        internal function to create tables
        '''
        cmd = "CREATE TABLE " + self.schemaName + ".images ( \
                 img_id bigserial unique primary key, \
                 img_date timestamp NOT NULL, \
                 img_rundate timestamp NOT NULL, \
                 mjd double precision NOT NULL, \
                 utstart time NOT NULL, \
                 ra_cent double precision NOT NULL, \
                 dec_cent double precision NOT NULL, \
                 ra_min double precision NOT NULL, \
                 ra_max double precision NOT NULL, \
                 dec_min double precision NOT NULL, \
                 dec_max double precision NOT NULL, \
                 ccdstemp double precision NOT NULL, \
                 ccdatemp double precision NOT NULL, \
                 azdmd double precision NOT NULL, \
                 azimuth double precision NOT NULL, \
                 altdmd double precision NOT NULL, \
                 altitude double precision NOT NULL, \
                 rotskypa double precision NOT NULL, \
                 filename char(35) NOT NULL \
                 );"
        self.db.execute(cmd)

        cmd = "CREATE TABLE " + self.schemaName + ".matchedUSNOBObjects ( \
                 usnoref char(25) unique primary key, \
                 usnoref_int bigserial unique NOT NULL, \
                 ra double precision NOT NULL, \
                 dec double precision NOT NULL, \
                 epoch double precision NOT NULL, \
                 b2_mag double precision NOT NULL, \
                 r2_mag double precision NOT NULL, \
                 pos spoint NOT NULL \
                 );"
        self.db.execute(cmd)
        
        cmd = "CREATE TABLE " + self.schemaName + ".matchedAPASSObjects ( \
                 apassref bigserial unique primary key, \
                 ra double precision NOT NULL, \
                 dec double precision NOT NULL, \
                 ra_err double precision NOT NULL, \
                 dec_err double precision NOT NULL, \
                 v_mag double precision NOT NULL, \
                 b_mag double precision NOT NULL, \
                 g_mag double precision NOT NULL, \
                 r_mag double precision NOT NULL, \
                 i_mag double precision NOT NULL, \
                 v_mag_err double precision NOT NULL, \
                 b_mag_err double precision NOT NULL, \
                 g_mag_err double precision NOT NULL, \
                 r_mag_err double precision NOT NULL, \
                 i_mag_err double precision NOT NULL, \
                 pos spoint NOT NULL \
                 );"
        self.db.execute(cmd)        

        cmd = "CREATE TABLE " + self.schemaName + ".sources ( \
                 src_id bigserial unique primary key, \
                 img_id bigserial NOT NULL references " + self.schemaName + ".images(img_id), \
                 mjd double precision NOT NULL, \
                 ra double precision NOT NULL, \
                 dec double precision NOT NULL, \
                 x_pix double precision NOT NULL, \
                 y_pix double precision NOT NULL, \
                 flux double precision NOT NULL, \
                 flux_err double precision NOT NULL, \
                 inst_mag double precision NOT NULL, \
                 inst_mag_err double precision NOT NULL, \
                 background double precision NOT NULL, \
                 isoarea_world double precision NOT NULL, \
                 seflags smallint NOT NULL, \
                 fwhm double precision NOT NULL, \
                 elongation double precision NOT NULL, \
                 ellipticity double precision NOT NULL, \
                 theta_image double precision NOT NULL, \
                 usnoref char(25) NULL references " + self.schemaName + ".matchedUSNOBObjects(usnoref), \
                 usnoref_int bigint NULL references " + self.schemaName + ".matchedUSNOBObjects(usnoref_int), \
                 apassref bigint NULL references " + self.schemaName + ".matchedAPASSObjects(apassref), \
                 pos spoint NOT NULL \
                 );"
        self.db.execute(cmd)

    def _makeViewsAndFunctions(self):
        '''
        internal function to create views and functions.
        '''
        self._makeView_countMatchedUSNOBSources() 
        self._makeFunction_getNumberOfObservationsByUSNOBRef()

    def _makeIndexes(self):
        '''
        internal function to create indexes.
        '''
        self.db.create_index(self.schemaName + ".images", "img_date", "idx_images_img_date")
        self.db.create_index(self.schemaName + ".images", "mjd", "idx_images_mjd")
        self.db.create_index(self.schemaName + ".sources", "mjd", "idx_sources_mjd")
        self.db.create_index(self.schemaName + ".sources", "inst_mag", "idx_sources_inst_mag")
        self.db.create_index(self.schemaName + ".sources", "pos", "idx_sources_pos", spatial=True)
        self.db.create_index(self.schemaName + ".matchedUSNOBObjects", "usnoref_int", "idx_matchedUSNOBObjects_usnoref_int")
        self.db.create_index(self.schemaName + ".matchedUSNOBObjects", "pos", "idx_matchedUSNOBObjects_pos", spatial=True)
        self.db.create_index(self.schemaName + ".matchedAPASSObjects", "apassref", "idx_matchedAPASSObjects_apassref")
        self.db.create_index(self.schemaName + ".matchedAPASSObjects", "pos", "idx_matchedAPASSObjects_pos", spatial=True)        

    ###
    ### VIEWS AND FUNCTIONS
    ###
    def _makeView_countMatchedUSNOBSources(self):
        cmd = "CREATE VIEW " + self.schemaName + ".countUniqueMatchedSourcesToUSNOB AS \
                   SELECT usnoref, count(*) as num FROM " + self.schemaName + ".sources GROUP BY usnoref"
        self.db.execute(cmd) 
        
    def _makeView_countMatchedAPASSSources(self):
        cmd = "CREATE VIEW " + self.schemaName + ".countUniqueMatchedSourcesToAPASS AS \
                   SELECT apassref, count(*) as num FROM " + self.schemaName + ".sources GROUP BY apassref"
        self.db.execute(cmd)         

    def _makeFunction_getNumberOfObservationsByUSNOBRef(self):
        cmd = "CREATE FUNCTION " + self.schemaName + ".getNumberOfObservationsUSNOB(param1 varchar) RETURNS integer AS $$ \
                   BEGIN \
                       RETURN \"SELECT num FROM " + self.schemaName + ".countUniqueMatchedSourcesToUSNOB WHERE usnoref = '$1'\"; \
                   END; \
                   $$ LANGUAGE plpgsql;"
        self.db.execute(cmd) 
        
    def _makeFunction_getNumberOfObservationsByUSNOBRef(self):
        cmd = "CREATE FUNCTION " + self.schemaName + ".getNumberOfObservationsAPASS(param1 varchar) RETURNS integer AS $$ \
                   BEGIN \
                       RETURN \"SELECT num FROM " + self.schemaName + ".countUniqueMatchedSourcesToAPASS WHERE usnoref = '$1'\"; \
                   END; \
                   $$ LANGUAGE plpgsql;"
        self.db.execute(cmd)         

    ###
    ### DEBUG DUMP FUNCTIONS
    ###
    def dumpTableSampleRecord(self):
        '''
        a useful debug function to dump a sample record from all tables.
        '''
        print "\n SAMPLE RECORDS "
        print "\n ---------------"
        print " |sources table|"
        print " ---------------\n"
        cmd = "SELECT column_name FROM information_schema.columns WHERE table_schema = '" + self.schemaName + "' AND table_name='sources'"
        res1 = self.db.read(cmd).fetchall()
        cmd = "SELECT * FROM " + self.schemaName + ".sources LIMIT 1"
        res2 = self.db.read(cmd).fetchall()
        if len(res2) > 0:
            for idx, i in enumerate(res1):
                print " ", i[0], ":", res2[0][idx]
        else:
            print "  TABLE EMPTY"
        print "\n --------------"
        print " |images table|"
        print " --------------\n"
        cmd = "SELECT column_name FROM information_schema.columns WHERE table_schema = '" + self.schemaName + "' AND table_name='images'"
        res1 = self.db.read(cmd).fetchall()
        cmd = "SELECT * FROM " + self.schemaName + ".images LIMIT 1"
        res2 = self.db.read(cmd).fetchall()
        if len(res2) > 0:
            for idx, i in enumerate(res1):
                print " ", i[0], ":", res2[0][idx]
        else:
            print "  TABLE EMPTY"
        print "\n ---------------------------"
        print " |matchedUSNOBObjects table|"
        print " ---------------------------\n"
        cmd = "SELECT column_name FROM information_schema.columns WHERE table_schema = '" + self.schemaName + "' AND table_name='matchedusnobobjects'"
        res1 = self.db.read(cmd).fetchall()
        cmd = "SELECT * FROM " + self.schemaName + ".matchedusnobobjects LIMIT 1"
        res2 = self.db.read(cmd).fetchall()
        if len(res2) > 0:
            for idx, i in enumerate(res1):
                 print " ", i[0], ":", res2[0][idx]
        else:
            print "  TABLE EMPTY"
        print "\n ---------------------------"
        print " |matchedAPASSObjects table|"
        print " ---------------------------\n"
        cmd = "SELECT column_name FROM information_schema.columns WHERE table_schema = '" + self.schemaName + "' AND table_name='matchedapassobjects'"
        res1 = self.db.read(cmd).fetchall()
        cmd = "SELECT * FROM " + self.schemaName + ".matchedapassobjects LIMIT 1"
        res2 = self.db.read(cmd).fetchall()
        if len(res2) > 0:
            for idx, i in enumerate(res1):
                 print " ", i[0], ":", res2[0][idx]
        else:
            print "  TABLE EMPTY"
        print 

    def dumpTableRowCount(self):
        '''
        a useful debug function to dump the number of rows in each table.
        '''
        cmd = "SELECT count(*) FROM " + self.schemaName + ".sources as count;"
        res = self.db.read(cmd)
        for i in res.fetchall():
            self.logger.info("(postgresql_skycam_mine.dumpTableRowCount) " + self.schemaName + ".sources table now has " + str(i[0]) + " entries")

        cmd = "SELECT count(*) FROM " + self.schemaName + ".images as count;"
        res = self.db.read(cmd)
        for i in res.fetchall():
            self.logger.info("(postgresql_skycam_mine.dumpTableRowCount) " + self.schemaName + ".images table now has " + str(i[0]) + " entries")

        cmd = "SELECT count(*) FROM " + self.schemaName + ".matchedUSNOBObjects as count;"
        res = self.db.read(cmd)
        for i in res.fetchall():
            self.logger.info("(postgresql_skycam_mine.dumpTableRowCount) " + self.schemaName + ".matchedUSNOBObjects table now has " + str(i[0]) + " entries")
            
        cmd = "SELECT count(*) FROM " + self.schemaName + ".matchedAPASSObjects as count;"
        res = self.db.read(cmd)
        for i in res.fetchall():
            self.logger.info("(postgresql_skycam_mine.dumpTableRowCount) " + self.schemaName + ".matchedAPASSbjects table now has " + str(i[0]) + " entries")            

