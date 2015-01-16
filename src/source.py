'''
name:		source.py
author:		rmb

description: 	A class to hold source information
'''

class source():
    def __init__(self, filename, sExCatRA, sExCatDEC, sExCatx, sExCaty, sExCatFluxAuto, sExCatFluxErrAuto, sExCatMagAuto, sExCatMagErrAuto, sExCatBackground, sExCatIsoareaWorld, sExCatSEFlags, sExCatFWHM, sExCatElongation, sExCatEllipticity, sExCatThetaImage, USNOBCatREF = None, USNOBCatRA=None, USNOBCatDEC=None, USNOBCatEPOCH=None, USNOBCatR2MAG=None, USNOBCatB2MAG=None):
        self.filename = filename
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

