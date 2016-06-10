'''
name:		source.py
author:		rmb

description: 	A class to hold source information
'''

class source():
    def __init__(self, filename, sExCatRA, sExCatDEC, sExCatx, sExCaty, sExCatFluxAuto, sExCatFluxErrAuto, sExCatMagAuto, 
                 sExCatMagErrAuto, sExCatBackground, sExCatIsoareaWorld, sExCatSEFlags, sExCatFWHM, sExCatElongation, sExCatEllipticity, 
                 sExCatThetaImage, USNOBCatREF = None, USNOBCatXMatchDist=None, USNOBCatRA=None, USNOBCatDEC=None, USNOBCatRAERR=None, USNOBCatDECERR=None, 
                 USNOBCatR1MAG=None, USNOBCatB1MAG=None, USNOBCatR2MAG=None, USNOBCatB2MAG=None, APASSCatREF = None, 
                 APASSCatXMatchDist=None, APASSCatRA=None, APASSCatDEC=None, APASSCatRAERR=None, APASSCatDECERR=None, APASSCatVMAG=None, 
                 APASSCatBMAG=None, APASSCatGMAG=None, APASSCatRMAG=None, APASSCatIMAG=None, APASSCatVMAGERR=None, APASSCatBMAGERR=None, 
                 APASSCatGMAGERR=None, APASSCatRMAGERR=None, APASSCatIMAGERR=None, APASSCatNOBS=None, SKYCAMCatREF=None, SKYCAMCatRA=None,
                 SKYCAMCatDEC=None, SKYCAMCatRAERR=None, SKYCAMCatDECERR=None, SKYCAMCatFIRSTOBSDATE=None, SKYCAMCatLASTOBSDATE=None, 
                 SKYCAMCatAPASSREF=None, SKYCAMCatUSNOBREF=None,
                 SKYCAMCatNOBS=None, SKYCAMCatAPASSBRCOLOUR=None, SKYCAMCatUSNOBBRCOLOUR=None, SKYCAMCatROLLINGMEANAPASSMAG=None, 
                 SKYCAMCatROLLINGSTDEVAPASSMAG=None, SKYCAMCatROLLINGMEANUSNOBMAG=None, SKYCAMCatROLLINGSTDEVUSNOBMAG=None, 
                 SKYCAMCatAPASSXMATCHDISTASEC=None, SKYCAMCatUSNOBXMATCHDISTASEC=None, SKYCAMCatAPASSNUMTIMESSWITCHED=None, 
                 SKYCAMCatUSNOBNUMTIMESSWITCHED=None):
        self.filename = filename
        self.APASSCatREF = APASSCatREF
        self.APASSCatXMatchDist = APASSCatXMatchDist
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
        self.APASSCatNOBS = APASSCatNOBS
        self.USNOBCatREF = USNOBCatREF
        self.USNOBCatXMatchDist = USNOBCatXMatchDist        
        self.USNOBCatRA = USNOBCatRA
        self.USNOBCatDEC = USNOBCatDEC
        self.USNOBCatRAERR = USNOBCatRAERR
        self.USNOBCatDECERR = USNOBCatDECERR  
        self.USNOBCatR1MAG = USNOBCatR1MAG
        self.USNOBCatB1MAG = USNOBCatB1MAG
        self.USNOBCatR2MAG = USNOBCatR2MAG
        self.USNOBCatB2MAG = USNOBCatB2MAG
        self.SKYCAMCatREF = SKYCAMCatREF
        self.SKYCAMCatRA = SKYCAMCatRA
        self.SKYCAMCatDEC = SKYCAMCatDEC
        self.SKYCAMCatRAERR = SKYCAMCatRAERR
        self.SKYCAMCatDECERR = SKYCAMCatDECERR
        self.SKYCAMCatFIRSTOBSDATE = SKYCAMCatFIRSTOBSDATE
        self.SKYCAMCatLASTOBSDATE = SKYCAMCatLASTOBSDATE
        self.SKYCAMCatAPASSREF = SKYCAMCatAPASSREF
        self.SKYCAMCatUSNOBREF = SKYCAMCatUSNOBREF
        self.SKYCAMCatNOBS = SKYCAMCatNOBS
        self.SKYCAMCatAPASSBRCOLOUR = SKYCAMCatAPASSBRCOLOUR
        self.SKYCAMCatUSNOBBRCOLOUR = SKYCAMCatUSNOBBRCOLOUR
        self.SKYCAMCatROLLINGMEANAPASSMAG = SKYCAMCatROLLINGMEANAPASSMAG
        self.SKYCAMCatROLLINGSTDEVAPASSMAG = SKYCAMCatROLLINGSTDEVAPASSMAG
        self.SKYCAMCatROLLINGMEANUSNOBMAG = SKYCAMCatROLLINGMEANUSNOBMAG
        self.SKYCAMCatROLLINGSTDEVUSNOBMAG = SKYCAMCatROLLINGSTDEVUSNOBMAG
        self.SKYCAMCatAPASSXMATCHDISTASEC = SKYCAMCatAPASSXMATCHDISTASEC
        self.SKYCAMCatUSNOBXMATCHDISTASEC = SKYCAMCatUSNOBXMATCHDISTASEC
        self.SKYCAMCatAPASSNUMTIMESSWITCHED = SKYCAMCatAPASSNUMTIMESSWITCHED
        self.SKYCAMCatUSNOBNUMTIMESSWITCHED = SKYCAMCatUSNOBNUMTIMESSWITCHED
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
