/*++++++++++++++
.IDENTIFICATION usnob1.c
.LANGUAGE       C
.AUTHOR         Francois Ochsenbein [CDS]
.ENVIRONMENT    USNO-B1.0 Catalogue
.KEYWORDS       CDS Catalogue Server
.VERSION  1.0   16-Nov-2002
.VERSION  1.1   04-Dec-2002: Arrange the values with a binary tree
.VERSION  1.2   08-Dec-2002: Use tree with 3 nodes
.VERSION  1.3   15-Jan-2003: Accept just RA/Dec limits. Accept soft link
.VERSION  1.4   28-Jan-2003: Accept RELATIVE soft links
.VERSION  1.5   13-Sep-2003: Verify RA/Dec in correct range
.VERSION  1.6   31-Jan-2004: A few errors...
.VERSION  1.7   23-Apr-2005: Take care of 64-bit
.VERSION  1.8   15-Nov-2005: more possibilities in center
.VERSION  1.9   28-Mar-2006: Limits on magnitudes
.VERSION  1.91  18-Feb-2007: Bug fix; Jname
.VERSION  1.92  24-Apr-2007: Option -E: remove proper motion
.VERSION  1.93  31-Jul-2007: Option -ea -eb -ep
.VERSION  1.94  08-Dec-2007: alarm
.VERSION  1.95  30-Aug-2009: Title
.VERSION  1.96  25-Jan-2012: too large radius also written on stdout
.VERSION  1.97  20-Jun-2013: accept USNO-B ID without dash
.COMMENTS       Access to USNO-B1.0 catalogue
	Remember that the environment variable USNOBroot provides
	the root of USNOB compressed catalogue; its default is
	derived from the program name IF the program resides in a .../bin
	or .../src directory. 
	If everything fails, the absolute default of USNOBroot is /USNOB.
---------------*/

#define VERSION "1.97"

#include <usnob1.h>	/* Structure definitions */
#ifndef ROOTdir
#define ROOTdir "/cats/USNO_B1"
#endif
#ifndef TIMEOUT
#define TIMEOUT 3600
#endif

#define RADIUS		(7.5/60.)	/* Default target radius */

#ifndef COMPUTE_EpPOS	/* 0 by +/-  1 by Matrix  2 by Cartesian */
#define COMPUTE_EpPOS	0
#endif

#include <stdio.h>
#include <stdlib.h>	/* Malloc   */
#include <unistd.h>	/* isatty   */
#include <string.h>
#include <ctype.h>
#include <time.h>
#include <math.h>
#include <sys/stat.h>

#define ITEMS(a)	(int)(sizeof(a)/sizeof(a[0]))
#define MIN(a,b)	((a)<(b) ? (a) : (b))
#define MAX(a,b)	((a)>(b) ? (a) : (b))
#define issign(c)	(((c)=='+')||((c)=='-'))
#define inan4		0x80000000		/* NaN in Integer */

#define  sind(x)	sin((x)*(M_PI/180.))
#define  cosd(x)	cos((x)*(M_PI/180.))
#define  tand(x)	tan((x)*(M_PI/180.))
#define asind(x)	(180./M_PI)*asin(x)
#define atand(x)	(180./M_PI)*atan(x)
#define atan2d(x,y)	(180./M_PI)*atan2(x,y)
#define adeg(x)		((x)*3600*1000)	/* Degree into mas */

static char *theProg;

/* Options for USNOB queries.......	*/
int usnob_options = 0 ;

static time_t started;

/* Linked records, to sort them...	*/
typedef struct linked_USNOB {
    struct linked_USNOB *lt ;
    struct linked_USNOB *eq ;
    struct linked_USNOB *gt ;
    USNOBrec rec ;
} LUSNOB ;
static int4 compare_calls;
static int mrec = 100 ;
static int irec, truncated ;
static int input_id ;		/* ID(1) Zone (2)  */
static char *prompt[] = {
   "Center", 		/* input_id=0 */
   "USNOB-ID", 		/* input_id=1 */
   "Jname",		/* input_id=2 */
   "RA+Dec Limits",	/* input_id=3 */
   "USNOB Zone",	/* input_id=4 */
} ;
static char whole_usnob ;	/* -whole option   */
LUSNOB *last, *arec, *root;

/*  Definitions related to Center of Field */
static double radius = 0 ;
static double boxy[2] ;
static double localR[3][3] ;	/* Matrix, [0] = dir.cos. of center */
static double du2max = -1 ;
static char optE;

/* Other options */
static int opted = 6 ; 	/* Default edit Decimal, Epoch, ID */

/* Definitions of the record fields */
struct s_fields {
    char name[4] ;	/* letter */
    char matching;	/* 0=exact 1=1letter, 2=2letters   */
    char selected ;
    short order ;
    double factor ;
    int4 lim[2] ;
};
static struct s_fields thefields[] =  {
    {"r",0,0,0,3.6e6},			/* MUST BE #0 */
    {"i",0,0,0,1.},			/* MUST BE #1 */
    {"x",0,0,0,(180./M_PI)*3.6e6},	/* MUST BE #2 */
    {"y",0,0,0,(180./M_PI)*3.6e6},	/* MUST BE #3 */
    {"a",0,0,0,3.6e6},			/* Must be #4 */
    {"d",0,0,0,3.6e6},			/* Must be #5 */
    {"p",0,0,0,1.},	/* pmt	#6	*/
    {"e",0,0,0,10.},	/* Mean Epoch	*/
    {"mb1",0,0,0,100.},	/* Mag.	blue 1  */
    {"mb2",0,0,0,100.},	/* Mag.	blue 2  */
    {"mr1",0,0,0,100.},	/* Mag.	red  1  */
    {"mr2",0,0,0,100.},	/* Mag.	red  2  */
    {"mi",0,0,0,100.},	/* Mag.	infrared*/
    {"o",0,0,0,1.},	/* Nobs	(ndet)	*/
    {"cb1",0,0,0,1.},	/* Class cb #14 */
    {"cb2",0,0,0,1.},	/* Class cb1... */
    {"cr1",0,0,0,1.},	/* Class cb1... */
    {"cr2",0,0,0,1.},	/* Class cb1... */
    {"ci",0,0,0,1.},	/* Class cb1... */
    {"t",0,0,0,USNOB_TYC},	/* Tycho-2 Star	*/
    {""}
} ;
#define FIELDS_m   8
#define FIELDS_mb  8
#define FIELDS_mr 10
#define FIELDS_c  14
#define FIELDS_cb 14
#define FIELDS_cr 16
static struct s_fields *compare_fields[32] ;
static struct s_fields *check_fields[32] ;
static int4 matched ;	/* Matching records 	      	*/
static int  stopid;	/* 1 = Stop after last ID read 	*/
static char pmm_title[] = "\
#======== USNO-B1.0 server (2002-11, V%s) ======== CDS, Strasbourg ========\n\
";

static char optEmsg[] = "\
#---------Position recomputed to Epoch.";
static char usage[] = "\
Usage: usnob1 [-HELP] [-R root_name] [-E] [-r[s] [min,]radius] [-b[s] x[,y]]\n\
              [-e edit_opt] [-f input_file] [-l! min,max] [-m max_records]\n\
	      [-c center | -i ID | -z zone | Jname | -whole] [-s !] \n\
";
 
static char help[] = "\
  -HELP: display column explanations\n\
     -E: Compute the position of mean Epoch (apply the proper motion back)\n\
     -R: Root (directory) name where the USNOB files are located ($USNOBroot)\n\
     -b: target box in arcmin ;    -bs = target box in arcsec\n\
     -r: target radius in arcmin ; -rs = target radius in arcsec\n\
     -c: target center in decimal or sexagesimal (default in stdin)\n\
     -e: s=Sexa; m=mas; i=ID; x=edit x,y; b=basic; p=pos.only; default=i\n\
     -f: specifies an input file (default stdin)\n\
    -id: query from an USNOB1 number (ZZZZ-NNNNNNN) [the dash may be omitted]\n\
     -m: max number of stars to retrieve\n\
    -l!: Set the limits (range) on one of the parameters (below)\n\
    -s!: Sort the result by the parameter ! (list below)\n\
 -zxxxx: search on a zone (between 0000 and 1799)\n\
  Jname: search sources matching an 'IAU'-name (JHHMM...+DD...)\n\
 -whole: search on the whole sky\n\
====The abbreviations of the parameters (symbolized !)are:\n\
      a=Alpha   c=anyClass d=Delta     e=Epoch    i=USNOB1   m=anyMag o=Nobs\n\
      p=pmotion r=distance s=sigmaPos  x=proj.E   y=proj.N   z=Zone\n\
'c' and 'm' may be follwed by the color b r,  b1 b2 r1 r2 i  or  O J E F N\n\
";

static char HELP[] = "\
Access to USNO-B1.0 Catalog at CDS\n\
=============================================================================\n\
\n\
The fields have the following meaning:\n\
\n\
USNO-B1.0 = Sequential number in original catalogue, as ZZZZ-NNNNNNN, \n\
            where ZZZZ is the zone number from 0000 to 1799\n\
Tycho-2   = Name in the 'Tycho-2 Catalog' (Hog et al., 2000, Cat. <I/259>)\n\
            Fir Tycho-2 stars, all parameters are derived from Tycho-2\n\
RA,Dec    = Position (Alpha, Delta) at Epoch and Equinox J2000\n\
sRA,sDE   = Mean Error on (RAcos(DE)) and (DE) at mean Epoch\n\
Epoch     = Mean Epoch of the observations\n\
pmRA,pmDE = relative proper motions, in arcsec/yr, of the object\n\
P         = probability, in units of 0.1, of the proper motion value\n\
spA,spD   = mean error on proper motions pmRA and pmDE resp.\n\
Fit       = fit value, on RA and DE, in units of 0.1arcsec\n\
N         = Number of detections, in the range 2 to 5\n\
MsY       = flags M=Motion confirmed in another catalog, \n\
                  s=object in diffraction spike\n\
                  Y=object in YS4 (in preparation)\n\
-----------------------------------------------------------------------------\n\
2 to 5 photometries are given in blue (O or J), red (E or F), and near-IR (N)\n\
For each photometry, the following parametres are given:\n\
Xmag  = magnitude derived from the photograohic material (accuracy: 0.3mag)\n\
C     = calibration 0 to 9, 0=bright photometric standard on plate, \n\
         1=faint photometric standard on plate, 2=one plate away, etc.\n\
Surv. = Survey number and field number as S-FFFC:\n\
        0- and 1- are POSS-I, 2-, 3- and 7- are POSS-II, 4- is SERC-J,\n\
        5- is ESO-R, 6- is AAO-R, 8- and 9- are SERC-I.\n\
cl    = classification star/galaxy, where 0 is non-stellar and 11 is stellar\n\
        ++++ WARNING, this value may be unreliable ++++\n\
xi,eta= distance of photocentre from the mean position of all images\n\
-----------------------------------------------------------------------------\n\
r(\")     = distance from specified center, in arc seconds.\n\
x,y(\")   = position from center toward East (x) and North (y)\n\
=============================================================================\n\
For details concerning USNO-B1.0, see  http://www.nofs.navy.mil/data/fchpix/\n\
=============================================================================\n\
"; 

/*==================================================================
		Find the USNOBroot parameter
 *==================================================================*/
static void set_root(char *pgm)
/*++++++++++++++++
.PURPOSE  Define the USNOBroot
.RETURNS  
.REMARKS  Take care of soft links...
-----------------*/
#if 0	/* V1.5: Try to find from program */
{
  struct stat buf;
  char name[1024];
  char *a, *p ;
  int i, r;
    if (!pgm) return;
    if (lstat(pgm, &buf)) return ;	/* Error */
    for (i=0; S_ISLNK(buf.st_mode); i++) {
	if (usnob_options&1) fprintf(stderr, "....Pgm %s ->", pgm) ;
	if (i>20) return;		/* Give up */
	i = readlink(pgm, name, sizeof(name)) ;
	if (i<=0) return; 		/* Give up */
	if (i >= sizeof(name)-1) return;
	name[i] = 0 ;
	if (name[0] != '/') {		/* RELATIVE NAME */
	    for (r=strlen(pgm)-1; (r>=0) && (pgm[r] != '/'); r--) ;
	    ++r;
	    if ((i+r) >= sizeof(name)-1) {
		fprintf(stderr, "****Too int4 filename %s(..)%s\n", pgm, name);
		return;
	    }
	    for (a=name+strlen(name); a>=name; a--) a[r] = a[0];
	    while(--r >= 0) name[r] = pgm[r];
	}
	pgm = name ;
	if (usnob_options&1) fprintf(stderr, " %s\n", pgm) ;
        if (lstat(pgm, &buf)) return ;	/* Error */
    }

    a = malloc(12+strlen(pgm)) ;
    sprintf(a, "USNOBroot=%s", pgm) ;
    for (p = a + strlen(a) -1 ; (p>a) && (*p != '/'); p--) ;
    if (p>a) for (--p; (p>a) && (*p != '/'); p--) ;
    if ((strncmp(p, "/bin/", 5) == 0) 
      ||(strncmp(p, "/src/", 5) == 0)) {
        *p = 0;
        putenv(a) ;
    }
    else free(a) ;
}
#else	/* V1.6: Take it from ROOTdir */
{
  char *a;
    a = malloc(12+strlen(ROOTdir));
    sprintf(a, "USNOBroot=%s", ROOTdir);
    putenv(a);
}
#endif


/*==================================================================
		Get the parameters
 *==================================================================*/

static struct s_fields *dup_field(struct s_fields *field)
/*++++++++++++++++
.PURPOSE  Clone a field
.RETURNS  The copy
-----------------*/
{
  struct s_fields *f;
    f = (struct s_fields *)malloc(sizeof(struct s_fields));
    memcpy(f, field, sizeof(struct s_fields)) ;
    return(f);
}

static struct s_fields *get_field(struct s_fields *fields, char *name)
/*++++++++++++++++
.PURPOSE  Interpret the meaning of a parameter
.RETURNS  The relevant field / NULL
-----------------*/
{
  static char *equiv[] = { "Ob1", "Er1", "Jb2", "Fr2", "Ni", "Ii", "Rr", "Bb", 
      (char *)0};
  char **a, letter, *p;
  struct s_fields *f;
    p = name;
    for (f=fields; f->name[0]; f++) {
	if (f->name[0] != *p) continue;
	if (f->name[1] == 0) return(f) ;
	if (p[1] == 0) return(f) ;
	letter = *p;
	for (a=equiv; *a; a++) { if (p[1] == **a) break; }
	if (*a) p = *a;
	if (f->name[1] != p[1]) { 
	    if (*a) p = name;
	    continue;
	}
	if (p[2] == 0) return(f);
	if (f->name[2] == p[2]) return(f);
	if (*a) p = name;
    }
    return((struct s_fields *)0) ;
}

/*============================================================================*/
static void tr_ou(double o[2], double u[3])
/*++++++++++++++++
.PURPOSE  Compute direction cosines
.RETURNS  ---
-----------------*/
{
    u[0] = u[1] = cosd(o[1]) ;
    u[0] *= cosd(o[0]) ;
    u[1] *= sind(o[0]) ;
    u[2] = sind(o[1]) ;
}

static int tr_uo(double u[3], double o[2])
/*++++++++++++++++
.PURPOSE  Compute RA+Dec from direction cosines
.RETURNS  1 / 0 (x=y=z=0)
-----------------*/
{
  double r2;            /* sqrt(x*x+y*y) */
    r2 = u[0]*u[0] + u[1]*u[1]; o[0] = 0.e0;
    if (r2  == 0.e0) {          /* in case of poles */
        o[0] = 999.; o[1] = 99.;
        if (u[2] == 0.e0)  return(0);
        o[1] = ( u[2]>0.e0 ? 90.e0 : -90.e0);
        o[0] = 0.;
        return(1);
    }
    o[1] = atand  ( u[2] / sqrt(r2));
    o[0]  = atan2d (u[1] , u[0] );
    if (o[0] < 0.e0) o[0] += 360.e0;
    return (1);
}

static void tr_oR ( o , R ) 
/*++++++++++++++++
.PURPOSE  Creates the rotation matrix R[3][3] defined as
	 R[0] (first row) = unit vector towards Zenith
	 R[1] (second row) = unit vector towards East
	 R[2] (third row) = unit vector towards North
.RETURNS ---
-----------------*/
  double o[2]; 		/* IN: original angles */
  double R[3][3];	/* OUT: rotation matrix */
{
    R[2][2] =  cosd(o[1]);
    R[0][2] =  sind(o[1]);
    R[1][1] =  cosd(o[0]);
    R[1][0] =  -sind(o[0]);
    R[1][2] =  0.e0;
    R[0][0] =  R[2][2] * R[1][1];  
    R[0][1] = -R[2][2] * R[1][0];
    R[2][0] = -R[0][2] * R[1][1];
    R[2][1] =  R[0][2] * R[1][0];
}

static void tr_uu( u1 , u2 , R ) 
/*++++++++++++++++
.PURPOSE  Rotates the unit vector u1 to u2, as  (u2) = (R) * (u1)
.RETURNS  ---
-----------------*/
  double u1[3]; 	/* IN: Unit vector */
  double u2[3]; 	/* OUT: Resulting unit vector after rotation */
  double R[3][3];	/* IN: rotation matrix (e.g. created by tr_oR)*/
{
  register int i;
  double u_stack[3];	/* allows same address for input/output      */
    for (i=0; i<3; i++) 
	u_stack[i] = R[i][0]*u1[0] +R[i][1]*u1[1] +  R[i][2]*u1[2] ;
    u2[0] = u_stack[0]; 	/* copies to output */
    u2[1] = u_stack[1]; 	/* copies to output */
    u2[2] = u_stack[2]; 	/* copies to output */
}

static void tr_uu1( u1 , u2 , R ) 
/*++++++++++++++++
.PURPOSE  Rotates the unit vector u1 to u2, as  (u2) = (R)^-1^ * (u1)
.RETURNS  ---
-----------------*/
  double u1[3]; 	/* IN: Unit vector */
  double u2[3]; 	/* OUT: Resulting unit vector after rotation */
  double R[3][3];	/* IN: rotation matrix (e.g. created by tr_oR)*/
{
  register int i;
  double u_stack[3];	/* allows same address for input/output      */
    for (i=0; i<3; i++) 
	u_stack[i] = R[0][i]*u1[0] +R[1][i]*u1[1] +  R[2][i]*u1[2] ;
    u2[0] = u_stack[0]; 	/* copies to output */
    u2[1] = u_stack[1]; 	/* copies to output */
    u2[2] = u_stack[2]; 	/* copies to output */
}

/*===========================================================================*/

static int match_unum (char *string, double *value, int *ndec)
/*++++++++++++++++
.PURPOSE  Analyze the incoming and get unsigned number (no E notation)
.RETURNS  How many bytes matched
.REMARKS  Initial blanks return 0. On return, ndec = number of decimals
	  -1 (no decimal point, i.e. integer value)
	  Value not changed if no match (returned number = 0)
-----------------*/
{
  char *p, *adot;
    for (p=string; isdigit(*p); p++) ;
    adot = p+1;
    if (*p == '.') for (++p; isdigit(*p); p++) ;
    if (*p == 'e') for (p+=2; isdigit(*p); p++) ;
    if (p > string) *value = atof(string) ;
    *ndec = p - adot;
    return(p-string);
}

static int match_num (char *string, double *value)
/*++++++++++++++++
.PURPOSE  Analyze the incoming and get signed number (accept 'e' notation)
.RETURNS  How many bytes matched
-----------------*/
{
  char *p, *s; int ndec;
    for (s=string; *s == ' '; s++) ;
    p = s ; 
    if ((*p == '+') || (*p == '-')) p++ ;
    p += match_unum(p, value, &ndec) ;
    if (*s == '-') *value = -*value ;
    return(p-string);
}

static int get_lim (char *arg, double values[2])
/*++++++++++++++++
.PURPOSE  Find out the limits (2 numbers separated by ,)
.RETURNS  0 / 1 / 2 / 3
.REMARKS  Accept p=min,max=min+max ==> sqrt(min1^2+min2^2) / 
	and accept --- for null
-----------------*/
{
  int found, round, n ;
  double val ;
  char *p ;

    found = 0 ; 
    round = 0 ;
    values[0] = values[1] = inan4;
    p = arg;
    /* Accept --- or null or nothing as NULL */
    while ((*p == ' ') || (*p == '-')) p++;
    if ((*p == 0) || (tolower(*p) == 'n'))	/* Accept NULLs */
        return(3);
    else p = arg;
  NextRound:
    round ^= 1;
    n = match_num(p, &val) ;
    if (n) {
        found |= 1, p += n ;
	if (round) values[0] = val ;
	else       values[0] = sqrt(values[0]*values[0] + val*val) ;
    }

    if (ispunct(*p)) {
	p++ ; 		/* Skip the ',' */
	found |= 2;	/* Marker found */
	n = match_num(p, &val) ;
	if (n == 0)	/* Default is MAX */
	    val = 0x7fffffff;
	p += n;
	if (round) values[1] = val;
	else       values[1] = sqrt(values[1]*values[1] + val*val) ;
    }
    if (*p && round) goto NextRound;
    return(found) ;
}

static int get_usnob (char *string, int4 id[2])
/*++++++++++++++++
.PURPOSE  Interpret a string for USNOB1 Numbers (zone-number)
.RETURNS  Number of bytes matched
.REMARKS  Accept ZONE-*
-----------------*/
{
  double v ; char *p ; int ndec;

    for(p=string; isdigit(*p); p++) ;
    if (!*p) {  /* Only digits: an ID Zone*10^7+ID (V1.93) */
        p -= 7;
        if(p<string) p=string;
    }
    else ++p;
    /* Get the Zone number */
    for (id[0]=0; isdigit(*string) && (string<p); string++)
        id[0] = (id[0]*10) + (*string&0xf);
    p += match_unum(p, &v, &ndec); id[1] = v ;
    if (*p) id[1]=0;	/* Assume a regexp */
    return(p-string) ;
}

static int get_Jname (char *arg, int4 *mas, int4 *Jprec)
/*++++++++++++++++
.PURPOSE  Interpret a string for a Jname
		or as a set run-camcol-field-obj
.RETURNS  Number of bytes matched / -1 for error
.REMARKS  Value of last decimal saved in Jprec
	Note: Jprec[1] < 0 for South
-----------------*/
{
  static int step1[] = {	/* Factors to convert to ms */
    36000000,			/* #0		*/
    3600000, 360000,		/* HH or DD DDd */
    60000, 6000,		/* HHMM  HHMMm  */
    1000, 100,			/* HHMMSS[s]	*/
    10, 1			/* HHMMSSss[s]	*/
  };
  char apart[12], sign, dpart[11], *p;
  int a, d, i, ms;

    p = arg;
    if (toupper(*p) == 'J') p++;
    for (i=a=0; (i<10) && p[i]; i++) {
	if (p[i] == '.') {
	    if (a==6) continue;
	    fprintf(stderr, "#***Bad Jname(RA) : %s\n", arg);
	    return(-1);
	}
	if (isdigit(p[i])) apart[a++] = p[i];
	else break;
    }
    apart[a] = 0;
    sign = p[i++];
    if ((sign != '+') && (sign != '-')) {
	fprintf(stderr, "#***Bad Jname(sgn): %s\n", arg);
	return(-1);
    }
    p += i;
    for (d=i=0; (i<10) && p[i]; i++) {
	if (p[i] == '.') {
	    if (d==6) continue;
	    fprintf(stderr, "#***Bad Jname(Dec): %s\n", arg);
	    return(-1);
	}
	if (isdigit(p[i])) dpart[d++] = p[i];
	else break;
    }
    dpart[d] = 0;
    if ((a<4)||(d<2)) {
	fprintf(stderr, "#***Bad Jname(...): %s\n", arg);
	return(-1);
    }

    /* Convert to 1/1000s */
    step1[2] = a == 3 ? 360000 : 600000;
    step1[4] = a == 5 ?   6000 :  10000;
    for (i=ms=0; apart[i]; i++) ms += (apart[i]-'0')*step1[i];
    Jprec[0] = step1[a-1]*15;
    mas[0] = ms*15;

    step1[2] = d == 3 ? 360000 : 600000;
    step1[4] = d == 5 ?   6000 :  10000;
    for (i=ms=0; dpart[i]; i++) ms += (dpart[i]-'0')*step1[i];
    Jprec[1] = step1[d-1];
    if (sign == '-') { 
	mas[1] = adeg(90) - ms;
	Jprec[1] = -Jprec[1];
    }
    else {
	mas[1] =  adeg(90) + ms;
    }

    return(p-arg);
}

static int get_center (char *string, double center[2])
/*++++++++++++++++
.PURPOSE  Interpret a string for RA + DEC
.RETURNS  Number of bytes matched
.REMARKS  Value 999. if not found. Accept jhhmm...
-----------------*/
{
  double v, factor ;
  char *p, *s, *w[6];
  int ndec, nw;

    factor = 1;
    center[0] = center[1] = 999.;
    p = string ; while (*p == ' ') p++ ;	/* Skip leading blanks */
    if (toupper(*p) == 'J') {			/* Accept JHHMM+ddmm   */
      int4 mas[2], Jprec[2]; int bytes;
        bytes = get_Jname(p, mas, Jprec);
	if (bytes < 0) return(bytes);
	bytes += (p-string);
	/* Mean value of truncation effect = 45/100 */
	mas[0] += (45*Jprec[0])/100;
	mas[1] += (45*Jprec[1])/100;
	mas[1] -= adeg(90);			/* 0 at Equator */
	center[0] = mas[0]; center[1] = mas[1];
	center[0] /= 3.6e6; center[1] /= 3.6e6;
	return(bytes);
    }
    p += match_unum(p, center, &ndec);		/* Get first number */
    if (*p == ' ') {	/* Blanks embedded. Could be sexagesimal... */
        while (*p == ' ') p++ ;
	if (ndec<0) {
	    /* We count the number of words. 
	       Is a sign is embedded, the delimiter RA/Dec is clear.
	       Otherwise, we introduce a '+' sign at the relevant position.
	    */
	    for (nw = 1, s = p-1; *s; s++) {
	        if ((*s == '+') || (*s == '-')) break;
		if (*s == ' ') {
		    for (++s; *s == ' '; s++) ;
		    if (*s) w[nw++] = --s;
		    if (nw >= 6) break;
		}
	    }
	    if (!*s) {		/* No sign found. Introduce it. */
		nw -= (nw/2);	/* move backwards ... */
		s = w[nw];
		if (*s == ' ') *s = '+';
	    }
	}
    }
    /* As soon as we find a decimal point, we can't be in RA any more */
    while (ndec < 0) {
	if (*p == ',') {	/* For those HEASARC guys ! */
	    p++;
	    break;
	}
	if (*p == ':') p++;
	if (!isdigit(*p)) break;
        factor /= 60.;
	if (factor < 1./3600.) break;
        p += match_unum(p, &v, &ndec);
	while (*p == ' ') p++ ;
	center[0] += factor*v;
    }
    if (factor != 1.) center[0] *= 15;	/* sexagesimal was found */
    while (*p == ' ') p++;
    s = p ;	/* Normally, the sign */
    if ((*s == '+') || (*s == '-')) p++ ;
    factor = 1;
    for (ndec = -1; ndec < 0; factor /= 60.) {
	if (*p == ':') p++ ;
	if (!isdigit(*p)) break;
	p += match_unum(p, &v, &ndec);
	while (*p == ' ') p++ ;
	if (factor == 1.) center[1] = v;
	else center[1] += factor*v ;
    }
    if (*s == '-') center[1] = -center[1] ;

    return(p-string) ;
}

/*==================================================================
		Check routine (return 0 = don't keep, 1 = keep)
 *==================================================================*/

static int matching_color(char *col, USNOBrec *rec)
/*++++++++++++++++
.PURPOSE  Match the color 0=b1, 1=b2, etc...
.RETURNS  0..4 => the required index
-----------------*/
{
  int i, c;
    if (!col[0]) {
	for (i=0; i<5 && (rec->mag[i]>=9999); i++) ;
	if (i<5) return(i);
	return(0);
    }
    c = tolower(col[0]);
    if (c == 'r') i = 1;
    else if (c == 'b') i = 0;
    else return(4);
    if (col[1])		/* Which color (b1 b2) is specified */
	return(i|((col[1]-'1')<<1));
    if (rec->mag[i]>=9999) i += 2;
    return(i);
}

static int remove_pm(USNOBrec *rec)
/*++++++++++++++++
.PURPOSE  Match the color 0=b1, 1=b2, etc...
.RETURNS  0 (no proper motion) / 1
.REMARKS  Use matrix
   dx    -sin(a) -sin(d)cos(a)
   dy  =  cos(a) -sin(d)sin(a)  .  mu1.t
   dz       0    +cos(d)           mu2.t
-----------------*/
{
  double R[3][3], u[3], v[3], o[2], t;
  int ra, sd;
    if ((rec->pmra | rec->pmsd) == 0) 	/* Zero proper motion 	*/
	return(0);
    t = (rec->epoch - 20000)/10.; 
    if (t == 0) return(0);		/* E.g. for Tycho-2 	*/
    o[0] = rec->ra; o[1] = rec->sd - adeg(90);
    o[0] /= 3.6e6; o[1] /= 3.6e6;
    v[1] = rec->pmra*t/3.6e6;
    v[2] = rec->pmsd*t/3.6e6;
#if COMPUTE_EpPOS == 0
    if (fabs(o[1]) > 84) {		/* Close to Pole */
	v[0] = 1;
        v[1] *= (M_PI/180.);
        v[2] *= (M_PI/180.);
        tr_oR(o, R);
        tr_uu1(v, u, R);
        tr_uo(u, o);
    }
    else {
	o[0] += v[1]/cosd(o[1]);
	if (o[0] <    0.) o[0] += 360.;
	if (o[0] >= 360.) o[0] -= 360.;
	o[1] += v[2];
    }
#else
# if COMPUTE_EpPOS == 1		/* Use Full Matrix expression  	*/
    v[0] = 1; 
    v[1] *= (M_PI/180.);
    v[2] *= (M_PI/180.);
    tr_oR(o, R);
    tr_uu1(v, u, R);
# else				/* Compute Cartesian diffarence	*/
    tr_ou(o,u);
    R[0][1] = -sind(o[0]);
    R[1][1] =  cosd(o[0]);
    R[2][1] =  0;
    R[0][2] =  sind(o[1]);
    R[1][2] =  R[0][2]*R[0][1];
    R[2][2] =  cosd(o[1]);
    R[0][2]*= -R[1][1];
    u[0] += R[0][1]*v[1] + R[0][2]*v[2];
    u[1] += R[1][1]*v[1] + R[1][2]*v[2];
    u[2] +=                R[2][2]*v[2];
# endif
    tr_uo(u, o);
#endif
    /* Convert to mas */
    ra = adeg(o[0]); sd = adeg(o[1]) + adeg(90);
#if 0	/* How large is the change ?? */
    fprintf(stderr, "....Change for %4d-%07d (%+05.1fyr) %6d %6d\n", 
      rec->zone, rec->id, t, ra-rec->ra, sd-rec->sd);
#endif
    rec->ra = ra; rec->sd = sd;
    return(1);
}

static int check(USNOBrec *rec)
/*++++++++++++++++
.PURPOSE  Verify the various constraints
.RETURNS  1 (OK) / 0 (does not fit)
-----------------*/
{
  struct s_fields **f;
  double o[2], u[3], du, dr2 ;
  int i, flag ;

    /* Verify first the Position */
    flag = 0 ;
    rec->xy[0] = rec->xy[1] = NULLxy ;
    if (du2max >= 0) {
    	o[0] = rec->ra / 3.6e6 ;
    	o[1] = rec->sd / 3.6e6  - 90. ;
    	tr_ou(o, u); flag |= 1 ;
    	du = u[0] - localR[0][0] ; dr2  = du * du ;
    	du = u[1] - localR[0][1] ; dr2 += du * du ;
    	du = u[2] - localR[0][2] ; dr2 += du * du ;
    	if (dr2 > du2max) return(0) ;
    	rec->rho = thefields[0].factor * 2.*asind(0.5*sqrt(dr2)) ;
	if (opted&8) {	/* Compute x,y */
      	    tr_uu(u, u, localR) ;
      	    rec->xy[0] = thefields[2].factor*u[1]/u[0] ;
      	    rec->xy[1] = thefields[3].factor*u[2]/u[0] ;
      	    flag |= 2 ;
	}
    }
    else rec->rho = -1 ;

    /* printf("#id=%4d,%8d, rho=%8d, mags=%4d,%4d,%4d\n", 
	rec->zone,rec->id,rec->rho, rec->mB, rec->mR, rec->ci) ;
    */

    for (f=check_fields ; *f; f++) switch((*f)->name[0]) {
      case_xy:
      	if (!flag) {
    	    o[0] = rec->ra / 3.6e6 ;
    	    o[1] = rec->sd / 3.6e6  - 90. ;
    	    tr_ou(o, u); flag |= 1 ;
      	}
      	if (!(flag&2)) {
      	    tr_uu(u, u, localR) ;
      	    rec->xy[0] = thefields[2].factor*u[1]/u[0] ;
      	    rec->xy[1] = thefields[3].factor*u[2]/u[0] ;
      	    flag |= 2 ;
      	}
	if (rec->xy[i] < (*f)->lim[0]) return(0) ;
	if (rec->xy[i] > (*f)->lim[1]) return(0) ;
      	break ;
      case 'x': i = 0 ; goto case_xy ;
      case 'y': i = 1 ; goto case_xy ;
      case 'a': 
	if ((*f)->lim[0] <= (*f)->lim[1]) {
	    if (rec->ra < (*f)->lim[0]) return(0) ;
	    if (rec->ra > (*f)->lim[1]) return(0) ;
	}
	else {
	    if ((rec->ra < (*f)->lim[0]) &&
	        (rec->ra > (*f)->lim[1])) return(0) ;
	}
	continue ;
      case 'm':
	i = matching_color((*f)->name+1, rec);
	if (rec->mag[i] < (*f)->lim[0]) return(0) ;
	if (rec->mag[i] > (*f)->lim[1]) return(0) ;
	continue ;
      case 'c':
	if (rec->flags&USNOB_TYC) return(0);
	i = matching_color((*f)->name+1, rec);
	if (i>=5) return(0);
	if (rec->phot[i].field == 0) return(0);
	if (rec->phot[i].stargal < (*f)->lim[0]) return(0);
	if (rec->phot[i].stargal > (*f)->lim[1]) return(0);
	continue ;
      case 'd':
	if (rec->sd < (*f)->lim[0]) return(0) ;
	if (rec->sd > (*f)->lim[1]) return(0) ;
	continue ;
      case 'e':
	if (rec->epoch < (*f)->lim[0]) return(0) ;
	if (rec->epoch > (*f)->lim[1]) return(0) ;
	continue ;
      case 'i':		/* lim[0] = Zone, lim[1] = ID */
        if (rec->zone != (*f)->lim[0]) return(stopid) ;
	if ((*f)->lim[1] == 0)	/* Whole Zone */
	    continue;
        if (rec->id    < (*f)->lim[1]) return(0) ;
        if (rec->id    > (*f)->lim[1]) return(stopid) ;
	continue ;
      case 'o':
	if (rec->ndet  < (*f)->lim[0]) return(0);
	if (rec->ndet  > (*f)->lim[1]) return(0);
	continue ;
      case 't':
	if ((rec->flags&USNOB_TYC) != (*f)->lim[0]) return(0);
      case 'p':
	if (rec->pmtot < 0) {
	    u[0] = rec->pmra ;
	    u[1] = rec->pmsd ;
	    rec->pmtot = 0.5 + sqrt(u[0]*u[0] + u[1]*u[1]) ;
	}
	if (rec->pmtot < (*f)->lim[0]) return(0) ;
	if (rec->pmtot > (*f)->lim[1]) return(0) ;
	continue ;
      case 'r':
	if (rec->rho < (*f)->lim[0]) return(0) ;
	if (rec->rho > (*f)->lim[1]) return(0) ;
	continue ;
    }
    return(1) ;
}

/*==================================================================
		Comparison routines
 *==================================================================*/

static int compare(USNOBrec *a, USNOBrec *b)
/*++++++++++++++++
.PURPOSE  Compare two records according to the sort options
.RETURNS  Difference (a-b)
-----------------*/
{
  struct s_fields **af, *f;
  double u[3] ;
  int i, j;
  int diff = 0;
    compare_calls++;
    for (af=compare_fields ; (diff==0) && *af; af++) {
	f = *af;
	switch(f->name[0]) {
          case 'x':
	    diff = a->xy[0] - b->xy[0];		break;
          case 'y':
	    diff = a->xy[1] - b->xy[1];		break;
          case 'a': 
	    diff = a->ra - b->ra;		break;
          case 'c':		/* Class star/gal */
	    i = matching_color(f->name+1, a);
	    j = matching_color(f->name+1, b);
	    diff = a->phot[i].stargal - b->phot[j].stargal;
	    break;
          case 'i':
	    diff = a->id - b->id;		break;
          case 'o':		/* #Obs */
	    diff = a->ndet - b->ndet;		break;
          case 'd':
	    diff = a->sd - b->sd;		break;
          case 'm':
	    i = matching_color(f->name+1, a);
	    j = matching_color(f->name+1, b);
	    diff = a->mag[i] - b->mag[j];	break;
          case 'p':
	    if (a->pmtot < 0) {
	        u[0] = a->pmra ; u[1] = a->pmsd ;
	        a->pmtot = 0.5 + sqrt(u[0]*u[0] + u[1]*u[1]) ;
	    }
	    if (b->pmtot < 0) {
	        u[0] = b->pmra ; u[1] = b->pmsd ;
	        b->pmtot = 0.5 + sqrt(u[0]*u[0] + u[1]*u[1]) ;
	    }
	    diff = a->pmtot - b->pmtot;		break;
          case 'e':
	    diff = a->epoch - b->epoch;		break;
          case 'r':
	    diff = a->rho - b->rho;		break;
	}
	if (f->order<0) diff = -diff;
    }
    return(diff) ;
}

/*==================================================================
		Sorting the Records
 *==================================================================*/

static int add_rec(USNOBrec *new)
/*++++++++++++++++
.PURPOSE  Add a new record, link it.
.RETURNS  0 (not kept) / 1
-----------------*/
{
  LUSNOB *node, *prev, *n;
  int4 comp1;
  int diff = 0;

    comp1 = compare_calls; 

    /* (0) Check if the new record has any use... */
    n = (LUSNOB *)0;		/* n -> last */
    if (irec == mrec) {
	if (!last) for (last=root; last->gt; last=last->gt) n = last;
	diff = compare(new, &(last->rec));
	if (diff >= 0) { truncated++; return(0); }
    }

    /* (1) Find where in the list we've to insert the new record */
    node = root;
    prev = (LUSNOB *)0;
    while(node) {
	diff = compare(new, &(node->rec));
	prev = node;
	if (diff == 0) break; 
	node = diff < 0 ? node->lt : node->gt ;
    }

    /* (2) If max attained, put the new in place of last */
    if (irec == mrec) {
	truncated++ ;
	node = last ;		/* Where to store new record 	*/
	if (last->eq) {		/* Several last records...      */
	    node = last->eq;
	    last->eq = node->eq ;
	}
	else {			/* n->gt must give LAST record	*/
	    if (!n) for (last=root; last->gt; last=last->gt) n = last;
	    if (!n) {		/* Happens when root == last !	*/
		root = root->lt;
		last = root;
	    }
	    else {		/* The last is now given by n	*/
		if (prev == last) {	/* new attached to last */
		    prev = n;		/* Added V1.91......... */
		    diff = compare(new, &(prev->rec));
		}
		last = n;
		last->gt = node->lt;
	    }
	}
	while(last->gt) last = last->gt;
    }
    else node = arec + irec++ ;

    /* (3) Insert the new record, and set the links */
    *(&(node->rec)) = *new ;
    node->lt = node->gt = node->eq = (LUSNOB *)0;
    if (!prev) { root = node; last = (LUSNOB *)0; }
    else {
	if (diff < 0) prev->lt = node;
	else if (diff > 0) {	/* I may have prev == last ...	*/
	    prev->gt = node;
	    if (last) while(last->gt) last = last->gt;
	}
	else { node->eq = prev->eq; prev->eq = node; }
    }
    
#if 0
    fprintf(stderr, "....Adding#%d: comparisons=%ld\n", 
	irec, compare_calls-comp1);
#endif

    return(1) ;
}

static void print_nodes(LUSNOB *node)
/*++++++++++++++++
.PURPOSE  Print all nodes in order
.RETURNS  ---
.REMARKS  Recursivity = simplicity !!
-----------------*/
{
  LUSNOB *n;
    if (!node) return;
    if (node->lt) print_nodes(node->lt);
    for (n=node; n; n=n->eq)
	puts(usnob2a(&(n->rec), opted));
    if (node->gt) print_nodes(node->gt);
}

/*==================================================================
		Search in a Circle
 *==================================================================*/

static int digest(USNOBrec *rec) 
/*++++++++++++++++
.PURPOSE  Digest routine: check and display if necessary
.RETURNS  0
-----------------*/
{
  int st ;
    /* --- Apply the Position Transformation if needed */
    if (optE) remove_pm(rec);

    st = check(rec) ;
    if (st <= 0) return(st) ;
    matched += 1 ;
    if (compare_fields[0]) 
    	add_rec(rec)  ;
    else {
	if (irec >= mrec) { truncated++; matched = 0; return(-1) ; }
	irec++ ; 
    	puts(usnob2a(rec, opted));
	if (ferror(stdout)) {
	    perror("#***Error digest(USNO_B1)");
	    exit(1);
	}
    }
    return(0) ;
}

int4 usnob_loop()
/*++++++++++++++++
.PURPOSE  Loop on read & test of USNOB records
.RETURNS  Number of tested records.
-----------------*/
{
  int4 tested = 0 ;
  USNOBrec rec ;
    while(1) {
        if (usnob_read(&rec) <= 0) break ;
	tested++;
	if (digest(&rec) < 0) break ;
    }
    return(tested) ;
}

int4 usnob_pos(int4 gra[2], int4 gsd[2])
/*++++++++++++++++
.PURPOSE  Launch Search on USNOB stars from limits in RA + DE
.RETURNS  Number of tested records.
.REMARKS  Merge with specified RA / DE limits
-----------------*/
{
  int4 ra[2], sd[2], sra[4], tra[4], tested ;
  int i, j ;

    tested = 0 ;
    if ((!thefields[5].selected) && (!thefields[4].selected))
       return(usnob_search(gra, gsd, digest)) ;

    if (gsd) sd[0] = gsd[0], sd[1] = gsd[1] ; 
    else     sd[0] = 0,      sd[1] = adeg(180) ;
    if (thefields[5].selected) {	/* Limits in DE */
	sd[0] = MAX(sd[0], thefields[5].lim[0]) ;
	sd[1] = MIN(sd[1], thefields[5].lim[1]) ;
	if (sd[0] > sd[1]) return(0);	/* Mismatch Dec */
    }

    sra[0] = tra[0] = 0;
    sra[1] = tra[1] = adeg(360)-1 ;	/* Selected RA	*/
    sra[2] = tra[2] = sra[3] = tra[3] = -1 ;
    if (gra) {
	tra[0] = gra[0];
	if (gra[0] <= gra[1]) 
	     tra[1] = gra[1] ;
	else tra[3] = gra[1], tra[2] = 0 ;
    }

    if (thefields[4].selected) {	/* Limits in RA */
	sra[0] = thefields[4].lim[0] ;
	if (thefields[4].lim[0] <= thefields[4].lim[1]) 
	     sra[1] = thefields[4].lim[1] ;
	else sra[3] = thefields[4].lim[1], sra[2] = 0 ;
    }

    for (i=0; i<4; i += 2) for (j=0; j<4; j += 2) {
	if (sra[j] < 0) continue ;
	if (tra[i] < 0) continue ;
	ra[0] = MAX(tra[i], sra[j]) ;
	ra[1] = MIN(tra[i+1], sra[j+1]) ;
	if (ra[0] > ra[1]) continue ;
	tested += usnob_search(ra, sd, digest) ;
    }

    return(tested) ;
}

int4 usnob_center(double center[2])
/*++++++++++++++++
.PURPOSE  Search USNOB stars from a central position:
	- either within circle of radius (degrees)
	- or within box of half-dimensions boxy
.RETURNS  Number of tested records.
-----------------*/
{
  int4 ra[2], sd[2];
  double value, sr, cosdec, da, dd, maxrad = RADIUS;

    ra[0] = 0, ra[1] = adeg(360) - 1 ;
    dd = 180. ;

    if ((radius==0) && (boxy[1]==0)) radius = RADIUS ;
    if (radius > 0) dd = maxrad = radius ;
    if (boxy[1] > 0) 		/* Search in a Box */
	dd = maxrad = sqrt(boxy[0]*boxy[0] + boxy[1]*boxy[1]) ;

    /* Don't accept too large searches... */
#if 0	/* Changed V1.96 */
    if (dd > 45.) {
	fprintf(stderr, "****Radius [%.5f]deg or Box [%.5fx%.5f] too large\n",
	    maxrad, boxy[0], boxy[1]) ;
	printf("#***Radius [%.5f]deg or Box [%.5fx%.5f] too large\n",
	    maxrad, boxy[0], boxy[1]) ;
	exit(1) ;
    }
#else
    if (dd>=180.) {
	fprintf(stderr, "#+++Whole sky (%.5fdeg)\n", maxrad);
        return(usnob_pos((int4 *)0, (int4 *)0));
    }
#endif
 
    /* Derive first the limits in Dec and RA */
    value = center[1] - dd ; sd[0] = (90.+value) * 3.6e6 ;
    value = center[1] + dd ; sd[1] = (90.+value) * 3.6e6 ;
    if (sd[0] < 0) sd[0] = 0 ;
    if (sd[1] > adeg(180)) sd[1] = adeg(180) ;

    cosdec = cosd(center[1]) ; 
    sr = sind(maxrad) ;
    du2max = 2. * sind(maxrad/2.) ;

    /* Compute limits on RA */
    if (sr < cosdec)  {		/* Pole not included in circle */
    	da = asind(sr/cosdec) ;
	ra[0] = (center[0] - da)*3.6e6 ;
	if (ra[0] < 0) ra[0] += adeg(360) ;
	ra[1] = (center[0] + da)*3.6e6 ;
	ra[1] %= adeg(360) ;
    }

    /* Define the constants */
    tr_oR(center, localR) ;
    du2max *= du2max ;

    /* Display the Constraints */
    if (usnob_options&1) {
	printf("#....usnob_center(%.5f, %.5f) maxrad=%.5f, limits_mas:\n", 
	    center[0], center[1], maxrad) ;
	printf("#....       ra=[%d,%d]", ra[0], ra[1]) ;
	printf(" sd=[%d,%d]\n", sd[0], sd[1]) ;
    }

    /* Merge the -la & -ld limits, and Launch Search */
    return(usnob_pos(ra, sd)) ;
}

/*==================================================================
		Main Program
 *==================================================================*/

/* Signal: if interrupted, return the signal number */
#include <signal.h>
static char *sig_msg;
void OnSignal(signo)
{
  char hostname[32];
    hostname[0] = 0;
    gethostname(hostname, sizeof(hostname));
    if (signo == SIGALRM) printf(
            "\n#***tooLong (>%ds), STOP (%s@%s) %s\n",
            TIMEOUT, theProg, hostname, sig_msg) ;
    else printf(
            "\n#***Signal #%d received, STOP (%s@%s) %s\n",
            signo, theProg, hostname, sig_msg) ;
    exit(signo) ;
}


int main (int argc, char **argv) 
{
  char line[BUFSIZ], *p, *a ;
  double center[2], flims[2], factor;
  char *the_center, *pgm, argline[BUFSIZ] ;
  struct s_fields *f, *fc ;
  int goon = 1 ;
  int4 tested, aint4;
  int4 Jpos[2], Jprec[2];
  int i, sign ;
  int non_flagged_arg = 0 ;
  int limradec = 0;
  FILE *input_file ;

    theProg = argv[0];
    if (argc < 2) {
	fprintf(stderr, "%s%s", usage, help) ;
	exit(1) ;
    }

    started = time(0);
    signal(SIGINT, OnSignal);
    signal(SIGPIPE, OnSignal);
    signal(SIGALRM, OnSignal);
    signal(SIGTTIN, OnSignal);
    siginterrupt(SIGALRM, 1);
    alarm(TIMEOUT);

    /* Keep program name to define the default USNOB root name */
    pgm = argv[0] ;
    /* fprintf(stderr, "....pgm=%s\n", pgm ? pgm : "(nil)") ; */

    /* NOTE: The options can also be  RA-DEC Radius */
    the_center = line ;
    input_file = stdin ;
    while (--argc > 0) {
	p = *++argv;
	if (*p == '-') switch(p[1]) {
	  case 'H':	/* HELP */
	    printf("%s", HELP);
	    exit(0) ;
	  case 'h':	/* Help */
	    fprintf(stderr, "%s%s", usage, help) ;
	    exit(0) ;
	  case 'f':	/* Next parameter = input file */
	    argc--, argv++;
	    input_file = fopen(*argv, "r") ;
	    if (!input_file) { perror(*argv) ; exit(1) ; }
	    continue ;
	  case 'b':	/* Next parameter = Box limits */
	    argc--, argv++;
	    switch(p[2]) {
	      case 'd': factor = 1; break ;
	      case 's': factor = 1./3600. ; break ;
	      default:  factor = 1./60. ; break ;
	    }
	    if (get_lim(*argv, flims) < 2) flims[1] = flims[0] ;
	    flims[0] *= factor; flims[1] *= factor;
	    flims[0] /= 2.0 ; flims[1] /= 2.0 ; 
	    boxy[0] = flims[0] ; boxy[1] = flims[1] ;
	    thefields[2].lim[1] = thefields[2].factor*tand(flims[0]) ;
	    thefields[3].lim[1] = thefields[3].factor*tand(flims[1]) ;
	    thefields[2].lim[0] = -thefields[2].lim[1] ;
	    thefields[3].lim[0] = -thefields[3].lim[1] ;
	    thefields[2].selected = thefields[3].selected = 1 ;
	    continue ;
	  case 'E':	/* Remove the proper motion effect */
	    optE = 1;
	    continue ;
	  case 'R':	/* Root Name of Catalogue  */
	    if (p[2])  p += 2;
	    else p = *++argv, argc-- ;
	    a = malloc(12+strlen(p)) ;
	    sprintf(a, "USNOBroot=%s", p) ;
	    putenv(a) ;
	    pgm = (char *)0 ;	/* Forget about implied from program name */
	    continue ;
	  case 'r':	/* Next parameter = Radius */
	    argc--, argv++;
	    switch(p[2]) {
	      case 'd': factor = 1; break ;
	      case 's': factor = 1./3600. ; break ;
	      default:  factor = 1./60. ; break ;
	    }
	    if (get_lim(*argv, flims) < 2) {
		flims[1] = flims[0] ;
		flims[0] = 0 ;
	    }
	    flims[0] *= factor; flims[1] *= factor;
	    radius = flims[1] ;
	    thefields[0].lim[0] = thefields[0].factor*flims[0] ;
	    thefields[0].lim[1] = thefields[0].factor*flims[1] ;
	    continue ;
	  case 'm':	/* Max number of records */
	    argc--, argv++;
	    mrec = atoi(*argv) ;
	    if (mrec < 1) mrec = 1 ;
	    continue ;
	  case 'e':	/* Edit option	*/
	    p += 2;	/* Is the argument of sort glued with -e ? */
	    if (!*p) p = *++argv, argc-- ;
	    opted = 0 ;
	    if (isdigit(*p)) opted = atoi(p) ;
	    else while(*p) switch(*(p++)) {
		case '=': opted = 0; continue;
		case ' ': continue;
		case '+':
		case '.': opted |= 6; continue;		/* Default */
		case 'd': opted &= ~17; continue;
		case 's': opted |= 1 ; continue ;
		case 'i': opted |= 2 ; continue ;
		case 'e': opted |= 4 ; continue ;
		case 'x': opted |= 8 ; continue ;
		case 'm': opted |= 16; continue ;
		case 'b': opted |=6|64; continue ;	/* V1.93: basic    */
		case 'p': opted |=128; continue ;	/* V1.93: pos.only */
		case 'a': opted = (opted&31)|6;		/* V1.93: all */
			  continue;
		default:
		   fprintf(stderr, "****Bad argument: -e '%s'\n%s", --p, usage);
		    exit(1) ;
	    }
	    continue ;
	  case 'i':	/* Input ID */
	    input_id = 1 ;
	    thefields[1].selected = 1;
	    if (argc > 1) {	/* ID as argument */
		stopid = -1 ;	/* Indicates to stop after last ID read */
		argc--, argv++;
		the_center = strdup(*argv) ;
	    }
	    continue ;
	  case 'z':	/* A Zone */
	    input_id = 4 ;
	    if (argc > 1) {	/* Zone as argument */
		usnob_stop(1) ;	/* Must stop at EOF */
		argc--, argv++;
		the_center = strdup(*argv) ;
	    }
	    continue ;
	  case 'l':	/* Set up the limits */
	    argc--, argv++;
	    i = get_lim(*argv, flims);
	    if (i==1) flims[1] = flims[0] ;
	    if (i==2) flims[0] = -0x7fffffff ;
	    if (!(f = get_field(thefields, p+2))) {
		fprintf(stderr, "****Unknown field in %s\n%s", p, usage);
		exit(1) ;
	    }
	    /* Exact name match, or just first few letters ? 
	       matching=1 when only 'm', matching=2 when 'mb'
	    */
	    if ((f->matching = strcmp(f->name, p+2)))
		 f->matching = strlen(p)-2;
	    f->selected = 1 ;
	    /* Modif. V1.9 */
	    flims[0] *= f->factor; 
	    flims[1] *= f->factor;
	    f->lim[0] = flims[0] < -2147483647.0 ? -2147483647 : flims[0];
	    f->lim[1] = flims[1] >  2147483647.0 ?  2147483647 : flims[1];
	    if (p[2] == 'a') 	limradec |= 1;
	    else if (p[2] == 'd')  {	/* Limits in Declination */
		f->lim[0] += adeg(90), f->lim[1] += adeg(90) ;
		limradec |= 2;
	    }
	    else if (p[2] == 'm')  {	/* Limits in Magnitude */
	        if (f->lim[0] <  -200) f->lim[0] = -200;
	        if (f->lim[1] >= 9999) f->lim[1] = 9998;
	    }
	    if ((f->lim[0] > f->lim[1]) && (p[2] != 'a'))
		aint4 = f->lim[0], f->lim[0] = f->lim[1], f->lim[1] = aint4 ;
	    continue ;
	  case 's':	/* Sort Order	*/
	    p += 2;	/* Is the argument of sort glued with -s ? */
	    if (!*p) p = *++argv, argc-- ;
	    for (i = 0 ; *p && (i < ITEMS(compare_fields)); i++, p++) {
		sign = 1 ;
		if (*p == '-') sign = -1, p++ ;
		else if (*p == '+') p++ ;
		f = get_field(thefields, p) ;
		if (!f) {
		    fprintf(stderr, "****Unknown field in -s %s\n%s", 
		    *argv, usage) ;
		    exit(1) ;
		}
		f = dup_field(f);
	    	f->order    = sign ;
		/* Skip the rest of the word, until next sort */
		for (sign=1; p[1] && f->name[sign] && isalnum(*p); p++) sign++;
		f->name[sign] = 0;	/* e.g. magnitudes truncated */
		compare_fields[i] = f ;
	    }
	    continue ;
	  case 'c':	/* Get Center	*/
	    argc--, argv++;
	    if (argc < 1) {
		fprintf(stderr, "****Unspecified center in -c argument\n%s",
		    usage) ;
		exit(1) ;
	    }
	    strcpy(argline, *argv);
	    the_center = argline ;
	    while (argc > 1) {		/* Position as several arguments ? */
		if (issign(argv[1][0])) {
		    if (! isdigit(argv[1][1])) break ;
		}
		else if (! isdigit(argv[1][0])) break ;
		argc--, argv++ ;
		strcat(argline, " ") ;
		strcat(argline, *argv) ;
	    }
	    continue ;
	  case 'v':	/* Verbose	*/
	    if (strncmp(p, "-ver", 4) == 0) {
	        printf("usnob1(%s) -- Version %s\n", ROOTdir, VERSION);
		exit(0);
	    }
	    usnob_options |= 1 ;
	    continue ;
	  case 'w':	/* Whole sky	*/
	    if (strcmp(p, "-whole") == 0) { 
	        whole_usnob = 1 ; 
	        mrec = 1999999999 ;
		continue ; 
	    }
	    /* NO BREAK */
	  default:
	    fprintf(stderr, "****Unknown argument: %s\n%s", p, usage);
	    exit(1) ;
	}
	/* Non-Option: if  */
	if (isdigit(*p) && (non_flagged_arg < 2)) {
	    non_flagged_arg++ ;
	    if (the_center == line) { the_center = *argv; continue ; }
	    get_lim(*argv, flims);
	    radius = flims[0]/60. ;
	    continue ;
	}
        /* Non-Option: accept Jnames (V1.1) */
        if ((toupper(*p) == 'J') && (input_id == 0)) {
            input_id = 2;
            the_center = p;
            continue;
        }
	fprintf(stderr, "****Unknown argument: %s\n%s", p, usage);
	exit(1) ;
    }
    printf(pmm_title, VERSION);

    /* Limits in RA and DEC can be ok */
    if ((input_id == 0) && (limradec == 3)) {
	input_id = 3;
	the_center = (char *)0;
    }

    /* Define USNOB from the program name */
    if (!getenv("USNOBroot")) set_root(pgm);
#if 0
    if (pgm && (!getenv("USNOBroot"))) {
	a = malloc(12+strlen(pgm)) ;
	sprintf(a, "USNOBroot=%s", pgm) ;
	for (p = a + strlen(a) -1 ; (p>a) && (*p != '/'); p--) ;
	if (p>a) for (--p; (p>a) && (*p != '/'); p--) ;
	if ((strncmp(p, "/bin/", 5) == 0) 
	  ||(strncmp(p, "/src/", 5) == 0)) {
	    *p = 0;
	    putenv(a) ;
	}
	else free(a) ;
    }
#endif

    /* Set up the check_fields */
    for (f=thefields, i=0; f->name[0]; f++) {
	if (!f->selected) continue;
	check_fields[i++] =  fc = f;  /* dup_field(f); */
	if (fc->matching) fc->name[(int)fc->matching] = 0;
    }

    /* Set up the array of results */
    if (compare_fields[0]) arec = (LUSNOB *)malloc(mrec*sizeof(LUSNOB)) ;

    while (goon) {
	compare_calls = 0;
	if (whole_usnob) goon = 0 ;
	else if (the_center == line) {
    	    if (isatty(fileno(input_file))) 
	        printf("----Give %s: ",  prompt[input_id]) ;
	    sig_msg = "(reading target)";
	    alarm(300);		/* Never wait too long... */
	    if (!fgets(line, sizeof(line), input_file)) break ;
	    sig_msg = "";
	    alarm(TIMEOUT);	/* Reset alarm       ... */
	    p = line + strlen(line) ;
	    while ((p>line) && (iscntrl(p[-1]))) p-- ;
	    *p = 0 ;
	    if (strncasecmp(line, "quit", 4) == 0) break ;
	    if (ispunct(line[0])) { puts(line); continue ; }
	    /* Could be a center, identifier, or Jname */
	    for (p=line; isspace(*p); p++) ;
	    if (input_id&5) ;	 /* Must be USNO-ID */
	    else input_id = toupper(*p) == 'J' ? 2 : 0;
	}
	else goon = 0 ;
    	irec = truncated = tested = matched = 0 ;

	if (whole_usnob) {
	    printf("#USNOB %s\n", "(whole)") ;
	    puts(usnob_head(opted)) ;
	    tested = usnob_pos((int4 *)0, (int4 *)0);	
	}

	else switch(input_id) {

	  case 1:		/* Get from USNOB-IDs */
	    usnob_options &= ~0x10 ;
	    get_usnob(the_center, thefields[1].lim);
	    printf("#USNOB %s\n", the_center) ;
	    if (optE) printf("%s\n", optEmsg);
	    puts(usnob_head(opted)) ;
	    if (usnob_set(thefields[1].lim[0], thefields[1].lim[1]) == 0)
	        tested = usnob_loop() ;
	    break ;
	    
	  case 4:		/* Get in Zone */
	    usnob_options &= ~0x10 ;
	    printf("#USNOB Zone %s\n", the_center) ;
	    puts(usnob_head(opted)) ;
	    if (usnob_zopen(atoi(the_center)) == 0)
	       tested = usnob_loop() ;
	    break ;

	  case 0:		/* Get from Center */
	    usnob_options &= ~0x10 ;
	    if (compare_fields[0]) {
		if (((compare_fields[0])->name[0] == 'r') 
		  &&((compare_fields[0])->order > 0)) 
		  usnob_options |= 0x10 ;
	    }
	    if (get_center(the_center, center) < 0) continue ;
	    printf("#Center: %s\n", the_center) ;
	    /* v1.5: Verify RA/Dec in correct range */
	    if ((center[0]>=360.0) || (center[1]<-90.) || (center[1]>90.)) {
		printf("#***bad: %s\t***(center out of limits)\n", the_center);
		break;
	    }
	    if (optE) printf("%s\n", optEmsg);
	    puts(usnob_head(opted)) ;
	    tested = usnob_center(center) ;
	    break;

	  case 2:		/* Jname (V1.91)   */
	    /* get_Jname returns position and Jprec in mas */
	    if (get_Jname(the_center, Jpos, Jprec) < 0)
		continue;
	    f = thefields+4;
	    f->lim[0] = Jpos[0];	/* unit=1mas */
	    f->lim[1] = Jpos[0] + (Jprec[0]-1);
	    f->selected = 1;
	    f++;
            if (Jprec[1] > 0) { /* North */
                f->lim[0] = Jpos[1];
                f->lim[1] = Jpos[1] + (Jprec[1]-1);
            }
            else {              /* South */
                f->lim[1] = Jpos[1];
                f->lim[0] = Jpos[1] + (Jprec[1]+1);
            }
            f->selected = 1;
            usnob_options |= 0x10 ;
            printf("#Jname: %s\n", the_center) ;
            puts(usnob_head(opted)) ;
            tested = usnob_pos(thefields[4].lim, thefields[5].lim);
            break;

	  case 3:		/* Use RA+Dec Lim. */
	    usnob_options |= 0x10;
	    printf("#Limits (mas) in RA[%d,%d] and SPD[%d,%d]\n", 
	      thefields[4].lim[0], thefields[4].lim[1],
	      thefields[5].lim[0], thefields[5].lim[1]);
	    if (optE) printf("%s\n", optEmsg);
	    puts(usnob_head(opted));
	    tested = usnob_pos(thefields[4].lim, thefields[5].lim);
	    break;
	}

	/*---- List saved records in order (replace backward by forward link) */
    	if (compare_fields[0]) { 
	    print_nodes(root);
	    root = last = (LUSNOB *)0;
	}
	if (truncated)  {
	    printf("#+++Truncated to %d out of ", mrec) ;
	    if (matched)  printf("%d", matched) ;
	    else printf("(not-computed)") ;
	    printf(" matches (%d tested)\n", tested) ;
	}
	else printf("#--- %d matches (%d tested)\n", matched, tested);
	printf("#...sort required %d total comparisons\n", compare_calls);
    }
    usnob_close() ;
    exit(0);
}
