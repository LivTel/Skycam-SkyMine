/*++++++++++++++
.IDENTIFICATION usnob1def.h
.LANGUAGE       C
.AUTHOR         Francois Ochsenbein [CDS]
.ENVIRONMENT    USNO-A2.0 Catalogue
.KEYWORDS       CDS Catalogue Server
.VERSION  1.0   06-Nov-2002
.VERSION  1.1   23-Apr-2005: Take care of 64-bit
.COMMENTS       Structures & Definitions concerning the USNO-B1.0 Catalog
		only for internal usage.
	The compacted record is made 0f 7 bytes = 56 bits with
	Field_index (3) GSC/ACT(1) Q(1) RA(11) SD(22) MB(9) MR(9)

	The first line of the file may be
	USNO-B1.0(17)   	128 chunks
	USNO-B1.0(18) ...  	near the poles -- a single chunck
	The first line contains also the offsets and values for
	pm, mag, xi-eta in the form    mag=0(2501) ...

	Data for 1 star are compressed in 17 bytes + photometry, containing
	-----------------
	status =  8 bits
	RA     = 20 bits (28 near the poles) -- unit=10mas
	SPD    = 16 bits -- unit=10mas
	e_RA   = 10 bits
	e_SD   = 10 bits
	flags  =  3 bits (_PM _SPK _YS4)
	Epoch  =  9 bits (0.1yr since 1950)
	fit_RA =  4 bits
	fit_SD =  4 bits
	pmRA   = 12 bits -- unit=2mas/yr, offset=-500 (i.e. 1arcsec/yr)
	pmSD   = 12 bits -- unit=2mas/yr, offset=-500 (i.e. 1arcsec/yr)
	muprob =  4 bits 
	e_pmRA = 10 bits
	e_pmSD = 10 bits
	-----------------
	and 2 to 5 photometry data. Each photometry data is made of 
	6 or 7 bytes with the lengths:
	-----------------------
	S/G+C,S= 11 bits        stargal*100 + calibration*10 + survey number
	field  =  4 or  6 bits
	mag    = 11 or 13 bits
	xi     = 11 or 13 bits
	eta    = 11 or 13 bits
	-----------------------

	The exact byte location are (17-byte length):
	+00 = Status byte with the following bits set
	      (Tycho)  0  (7-byte-ph)  (blue1)  (red1)  (blue2)  (red2)  (N)
	+01 = Ndet [NOTE: SHOULD BE IDENTICAL to the number of bits set to 1]
	      RA (4b)
	+02 = RA (8b)
	+03 = RA (8b)
	+04 = SPD(8b)
	+05 = SPD(8b)
	+06 = e_RA (8b)
	+07 = e_RA (2b), e_DE (6b)
	+08 = e_DE (4b), USNOB_PM + _SPK + _YS4, Epoch (1b)
	+09 = Epoch (8b)
	+10 = fit_RA (4b), fit_DE (4b)
	+11 = pm1 (8b)
	+12 = pm1 (4b), pm2 (4b)
	+13 = pm2 (8b)
	+14 = muprob (4b), e_pm1(4b)
	+15 = e_pm1(6b), e_pm2(2b)
	+16 = e_pm2(8b)
	  
	For Tycho-2 stars:
	- bytes +06 to +07 are TYC1
	- bytes +08 to +09 are TYC2
	- bytes +10        is  TYC3
	- bytes +14 to +16 are Seq<0 (1b), File Number (5b) Seq. (18b)

	The photometry is coded either on 6 or 7 bytes:
	------------------------------------------------
	+00 = stargal(4b), calib*10+survey(4b)
	+01 = calib*10+survey(3b), fld(4b), mag(1b)
	+02 = mag(8b)
	+03 = mag(2b), xi(6b)
	+04 = xi (5b), eta(3b)
	+05 = eta(8b)
	------------------------------------------------
	+00 = stargal(4b), calib*10+survey(4b)
	+01 = calib*10+survey(3b), fld(5b)
	+02 = fld(1b), mag(7b)
	+03 = mag(6b), xi(2b)
	+04 = xi (8b)
	+05 = xi (3b), eta(5b)
	+06 = eta(8b)
	------------------------------------------------

	The header consists in:
	1) an ascii line 
	   USNO-B1.0(17)  or  USNO-B1.0(18) Zxxxx  	terminated by \n
	   made of a multiple of 4 bytes
        2) An index table of 128*2 (FileLocation, ID)
	   offsets in the case of USNO-B1.0(17) only

	Data are then grouped in chunks corresponding to 2**20(10mas) i.e.
	about 3degrees -- a single chunck in the case of USNO-B1.0(18).
	A chunk is made of the following:
	a) A header of variable length containing:
	   +00 = length = 36+2*(Nf+Npm+Nmag+Nxi) (4bytes) 
			  [rounded to multiple of 4] in Sun binary
	   +04 = id_min RA_min SD_min   (3*4 bytes)
	   +16 = id_max RA_max SD_max   (3*4 bytes)
	   +28 = Nf  Npm  Nmag  Nxi  (4*2 bytes, number of terms)
	   +36 = 'Extras' short values (Nf+Npm+Nmag+Nxi)*2 bytes
	b) INDEX (offset_from_chunk, ID-min, RA_min) table about 1000/line
	   and a last+1 with a zero offset (the 'Accelerator')
        c) The values
---------------*/

#ifndef USNOB1DEF_def
#define USNOB1DEF_def	0
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


#define Dstep 	360000		/* Declination step in mas (0.1deg) */
#define Astep 	((1<<20)*10)	/* RA step in mas between chunks    */
#define Dacc	500		/* Interval in Accelerator	    */
#define MASK(b) ((1<<(b))-1)

/*===========================================================================
		Structures 
 *===========================================================================*/

static char header_text[] = "\
USNO-B1.0(%d) %s fld=%d(%d) pm=%d(%d) mag=%d(%d) xi=%d(%d)" ; 

#define Nchunks		125	/* Number of Chunks	*/
#define USNOB_ph7	0x40	/* Indicates a photometry coded on 7 bytes */

/* Values of Offsets stored for the values with 'extra' */
#define Ofld   0
#define Opm -500
#define Omag 700	/* Brighter limit = 7.00 */
#define Oxi -750

#define Nfld   0
#define Npm  (1-2*(Opm))
#define Nmag (2501-Omag)
#define Nxi  (1-2*(Oxi))

typedef struct {
    int len ;			/* Length of Chunk 	*/
    int pos, id;		/* Current identifier	*/
    int ppos;			/* pos of preceding rec	*/
    int RAz;			/* 0 ..123, leftmost RA	*/
    int4  id0, ra0, sd0, id1, ra1, sd1 ;
    short *Afpmx[4];		/* Addresses of extras  */
    int4 *index;		/* Index of (o,ID,RA)	*/
    int4 *endex;		/* End of above array	*/
} CHUNK;

/*===========================================================================
		Prototypes Declarations
 *===========================================================================*/
 
#endif
