'''
name:		USNOBCatalogue.py
author:		rmb

description: 	A USNOB catalogue class
'''
import subprocess

class USNOBCatalogue():
    def __init__(self, err, logger):
        self.USNOBREF = []
        self.RA = []
        self.DEC = []
        self.EPOCH = []
        self.R2MAG = []
        self.B2MAG = []
        self.err = err
        self.logger = logger

    def insert(self, usnobref, ra, dec, epoch, r2mag, b2mag):
        '''
        insert usnob object into catalogue
        '''
        self.USNOBREF.append(usnobref)
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
                try:
                     if appendToCat:
                         self.insert(usnobref=str(USNOBREF), ra=float(RA), dec=float(DEC), epoch=float(EPOCH), r2mag=float(RMAG2), b2mag=float(BMAG2))
                except ValueError: 
                     continue
 
