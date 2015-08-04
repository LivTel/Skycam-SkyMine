'''
name:		source.py
author:		rmb

description: 	A class to hold source information
'''

class source():
    def __init__(self, filename, sExCatRA, sExCatDEC, sExCatx, sExCaty, sExCatFluxAuto, sExCatFluxErrAuto, sExCatMagAuto, 
                 sExCatMagErrAuto, sExCatBackground, sExCatIsoareaWorld, sExCatSEFlags, sExCatFWHM, sExCatElongation, sExCatEllipticity, 
                 sExCatThetaImage, USNOBCatREF = None, USNOBCatRA=None, USNOBCatDEC=None, USNOBCatEPOCH=None, USNOBCatR2MAG=None, 
                 USNOBCatB2MAG=None, APASSCatREF = None, APASSCatRA = None, APASSCatDEC = None, APASSCatRAERR = None, APASSCatDECERR = None, 
                 APASSCatVMAG = None, APASSCatBMAG = None, APASSCatGMAG = None, APASSCatRMAG = None, APASSCatIMAG = None, APASSCatVMAGERR = None, 
                 APASSCatBMAGERR = None, APASSCatGMAGERR = None, APASSCatRMAGERR = None, APASSCatIMAGERR = None):
        self.filename = filename
        self.APASSCatREF = APASSCatREF
        self.APASSCatRA = APASSCatRA
        self.APASSCatDEC = APASSCatDEC
        self.APASSCatRAERR = APASSCatRAERR
        self.APASSCatDECERR = APASSCatDECERR 
        self.APASSCatVMAG = APASSCatVMAG
        self.APASSCatBMAG = APASSCatBMAG    
        self.APASSCatGMAG = APASSCatGMAG
        self.APASSCatRMAG = APASSCatRMAG
        self.APASSCatIMAG =  APASSCatIMAG  
        self.APASSCatVMAGERR = APASSCatVMAGERR 
        self.APASSCatBMAGERR = APASSCatBMAGERR
        self.APASSCatGMAGERR = APASSCatGMAGERR
        self.APASSCatRMAGERR = APASSCatRMAGERR
        self.APASSCatIMAGERR = APASSCatIMAGERR
        self.USNOBCatREF = USNOBCatREF
        self.USNOBCatRA = USNOBCatRA
        self.USNOBCatDEC = USNOBCatDEC
        self.USNOBCatEPOCH = USNOBCatEPOCH
        self.USNOBCatR2MAG = USNOBCatR2MAG
        self.USNOBCatB2MAG = USNOBCatB2MAG
        self.sExCatRA = sExCatRA
        self.sExCatDEC = sExCatDEC
        self.sExCatx = sExCatx
        self.sExCaty = sExCaty
        self.sExCatFluxAuto = sExCatFluxAuto
        self.sExCatFluxErrAuto = sExCatFluxErrAuto
        self.sExCatMagAuto = sExCatMagAuto
        self.sExCatMagErrAuto = sExCatMagErrAuto
        self.sExCatBackground = sExCatBackground
        self.sExCatIsoareaWorld = sExCatIsoareaWorld
        self.sExCatSEFlags = sExCatSEFlags
        self.sExCatFWHM = sExCatFWHM
        self.sExCatElongation = sExCatElongation
        self.sExCatEllipticity = sExCatEllipticity
        self.sExCatThetaImage = sExCatThetaImage
