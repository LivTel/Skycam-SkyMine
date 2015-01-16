/*++++++++++++++
.IDENTIFICATION usnob1.h
.LANGUAGE       C
.AUTHOR         Francois Ochsenbein [CDS]
.ENVIRONMENT    USNO-B1.0 Catalogue
.KEYWORDS       CDS Catalogue Server
.VERSION  1.0   06-Nov-2002
.VERSION  1.1   23-Apr-2005: Take care of 64-bit
.COMMENTS       Structures & Definitions concerning the USNO-B1 Catalog
---------------*/

#ifndef USNOB1_DEF
#define USNOB1_DEF	0
#ifndef _ARG
#ifdef __STDC__
#define _ARG(A)	A    /* ANSI */
#else
#define _ARG(A)	()  /* non-ANSI */
#define const
#endif
#endif

/* Version 1.1: verify 64-bit machine */
#ifndef int4
#define int4 int
#endif  /* int4 */

/*===========================================================================
		Structures 
 *===========================================================================*/

/* Photometry in a band */
typedef struct {
    char stargal;		/* Star/Gal class 0-11	*/
    char survey;		/* Encoded survey 0-9	*/
    short field;		/* Survey Field Number	*/
    short xi, eta;		/* Residuals in 10mas	*/
    char calib;			/* Source of Phot.Calib	*/ 
    char pb_stargal;		/* '*' when stargal bad	*/
} USNOphot;

typedef struct {
    char  flags ;		/* Flags about this object ---	*/
#define USNOB_TYC	0x80		/* Indicates a TYC2	*/
#define USNOB_TS1	0x10		/* Supplement_1 of TYC2	*/
#define USNOB_TS2	0x20		/* Supplement_2 of TYC2	*/
#define USNOB_PM 	0x08		/* Proper Motion Flag	*/
#define USNOB_YS4	0x04		/* YS4 Correlation Flag	*/
#define USNOB_SPK	0x02		/* Diffraction Spike	*/
    char  ndet ;		/* Number of detections		*/
    short zone ;		/* Original zone number	0-1799	*/
    int4 id, ra, sd ;		/* RA and S. Polar Dist. mas	*/
    short e_ra, e_sd;		/* sd Position RA/Dec, mas	*/
    short epoch;		/* Epoch expressed in  0.1yr	*/
    char fit_ra, fit_sd;	/* Fit sigma in 0.1arcsec	*/
    short pmra, pmsd;		/* Proper Motions in mas/yr	*/
    short e_pmra, e_pmsd;	/* sd Proper Motions in mas/yr	*/
    int4 rho, theta ;		/* Distance from center (mas)	*/
    int4 xy[2] ;		/* Values of proj. x,y  (mas) 	*/
    short pmtot;		/* Total Proper Motion		*/
    short mag[5];		/* Magnitudes O E J F N in cmag	*/
				/* ----------------------------	*/
    char muprob;		/* Total pm probability in 0.1	*/
    char spare;
    USNOphot phot[5];		/* Details for B1 R1 B2 R2 N	*/
    /* int index[5];		-- Lookback indexes to pm scans	*/
				/* ----------------------------	*/
} USNOBrec ;

/* In case flags is 0x80, it's a TYCHO-2 data in USNO-B 	*/
typedef struct {
    char  flags ;		/* 0x80 bit is set, always	*/
    char  ndet ;		/* Number of detections (=0)	*/
    short zone ;		/* Original zone number	0-1799	*/
    int4 id, ra, sd ;		/* RA and S. Polar Dist. mas	*/
    short e_ra, e_sd;		/* sd Position RA/Dec, mas (=0)	*/
    short epoch;		/* Epoch expressed (=20000)	*/
    char fit_ra, fit_sd;	/* Fit sigma in 0.1arcsec	*/
    short pmra, pmsd;		/* Proper Motions in mas/yr	*/
    short e_pmra, e_pmsd;	/* sd Proper Motions in mas/yr	*/
    int4 rho, theta ;		/* Distance from center (mas)	*/
    int4 xy[2] ;		/* Values of proj. x,y  (mas) 	*/
    short pmtot;		/* Total Proper Motion		*/
    short mag[5];		/* Computed mag O E J F N, cmag	*/
				/* ----------------------------	*/
    short TYC1, TYC2; 		/* TYCHO-2 Number		*/
    char TYC3;	
    char fileno;		/* 0-19 , 20=Supp1, 21=Supp2	*/
    int4 recno;			/* Record number in original TYC*/
				/* ----------------------------	*/
} USNOBtyc  ;

#define NULLxy	(-999999999)	/* Non-computed values for xy	*/

/*===========================================================================
		Prototypes Declarations
 *===========================================================================*/
 
int   usnob1_init   _ARG((char *USNOB1root)) ;
char *usnob2a       _ARG((USNOBrec *pr, int opt)) ;
		/* Option: 1 in sexa, 2=ID, 4=Epoch */
char *usnob_head   _ARG((int opt)) ;
int4  usnob_seek   _ARG((int4 ra, int4 sd)) ; 	/* Position in 10mas */
int4  usnob_search _ARG((int4 ra[2], int4 sd[2], int (*digest_routine)())) ;
int   usnob_set    _ARG((int zone, int4 id)) ;
int   usnob_get    _ARG((int zone, int4 id, USNOBrec *rec)) ;
int   usnob_zopen  _ARG((int zone));
int   usnob_read   _ARG((USNOBrec *rec)) ;
int   usnob_stop   _ARG((int stop_option));
int   usnob_close  _ARG((void));
#endif
