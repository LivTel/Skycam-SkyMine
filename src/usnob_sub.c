/*++++++++++++++
.IDENTIFICATION usnob_sub.c
.LANGUAGE       C
.AUTHOR         Francois Ochsenbein [CDS]
.ENVIRONMENT    USNO-A2.0 Catalogue
.KEYWORDS       CDS Catalogue Server
.VERSION  1.0   11-Nov-2002
.VERSION  1.1   05-Dec-2002: a	dded pb_stargal (when stargal looks wrong)
.VERSION  1.2   31-Jan-2004: BUG in aseek (was not re-initialized)
.VERSION  1.3   13-Sep-2004: BUG in usnob_search
.VERSION  1.3   23-Apr-2005: Take care of 64-bit
.VERSION  1.4   15-Nov-2005: Edition of xi, eta
.VERSION  1.5   31-Jul-2007: Options basic-only, position only
.VERSION  1.51  03-Mar-2008: close to 24h
.COMMENTS       Edition of USNOB data.

---------------*/

#include <usnob1def.h>	/* Structure definitions */
#include <usnob1.h>	/* Structure definitions */

#include <stdio.h>
#include <stdlib.h>	/* Malloc   */
#include <unistd.h>
#include <string.h>
#include <ctype.h>
#include <fcntl.h>	/* O_BINARY */
#include <math.h>
#define  sind(x)	sin(x*(M_PI/180.))
#define  cosd(x)	cos(x*(M_PI/180.))
#define  asind(x)	(180./M_PI)*asin(x)

#ifndef O_BINARY	/* Required for MS-DOS	*/
#define O_BINARY 0
#endif
#include <stdio.h>

#define ITEMS(a)	(int)(sizeof(a)/sizeof(a[0]))
#define MIN(a,b)	((a)<=(b) ? (a) : (b))
#define MAX(a,b)	((a)>=(b) ? (a) : (b))

typedef int (*SORT_FCT)(const void *, const void *) ;

/* Options for USNOB queries.......	*/
int usnob_options ;		/* 0x10 for OrigOrder	*/

static struct {
    char *root;			/* Root name of USNOB	*/
    char *name ;		/* Name of opened file	*/
    int fno;
    char line[128] ;		/* First line of file	*/
    short SDz;			/* Zone opened 		*/
    char pb_stargal;		/* Problem STARGAL '*'	*/
    char reclen;		/* 17 or 18		*/
    short lename;		/* Length of name buffer*/
    short nchunks;		/* Actual # chunks	*/
    short Ofpmx[4];             /* Offset fld pm mag xi */
    short Nfpmx[4];             /* Max values -- extras */
    int mbuf ;			/* Allocated bytes mbuf	*/
    char *abuf;			/* Loaded data		*/
    int4 chunks[2*Nchunks];	/* List (filepos, ID)	*/
    int4 *echunks;		/* (Last+1) valid chunk	*/
    CHUNK dat;			/* All details of Chunk	*/
} USNOBcat ;

/* The first byte of a data record is related to the record length;
   We just install this as a table.
*/
static unsigned char photolen[] = {
      /* 0   1   2   3   4   5   6   7   8   9   a   b   c   d   e   f */
 /*0*/   0,  6,  6, 12,  6, 12, 12, 18,  6, 12, 12, 18, 12, 18, 18, 24,
 /*1*/   6, 12, 12, 18, 12, 18, 18, 24, 12, 18, 18, 24, 18, 24, 24, 30,
 /*2*/   0,  6,  6, 12,  6, 12, 12, 18,  6, 12, 12, 18, 12, 18, 18, 24,
 /*3*/   6, 12, 12, 18, 12, 18, 18, 24, 12, 18, 18, 24, 18, 24, 24, 30,
 /*4*/   0,  7,  7, 14,  7, 14, 14, 21,  7, 14, 14, 21, 14, 21, 21, 28,
 /*5*/   7, 14, 14, 21, 14, 21, 21, 28, 14, 21, 21, 28, 21, 28, 28, 35,
 /*6*/   0,  7,  7, 14,  7, 14, 14, 21,  7, 14, 14, 21, 14, 21, 21, 28,
 /*7*/   7, 14, 14, 21, 14, 21, 21, 28, 14, 21, 21, 28, 21, 28, 28, 35,
 /*8*/   0,  2,  2,  4,  2,  4,  4,  6,  2,  4,  4,  6,  4,  6,  6,  8,
 /*9*/   2,  4,  4,  6,  4,  6,  6,  8,  4,  6,  6,  8,  6,  8,  8, 10,
 /*a*/   0,  2,  2,  4,  2,  4,  4,  6,  2,  4,  4,  6,  4,  6,  6,  8,
 /*b*/   2,  4,  4,  6,  4,  6,  6,  8,  4,  6,  6,  8,  6,  8,  8, 10,
 /*c*/   0,  2,  2,  4,  2,  4,  4,  6,  2,  4,  4,  6,  4,  6,  6,  8,
 /*d*/   2,  4,  4,  6,  4,  6,  6,  8,  4,  6,  6,  8,  6,  8,  8, 10,
 /*e*/   0,  2,  2,  4,  2,  4,  4,  6,  2,  4,  4,  6,  4,  6,  6,  8,
 /*f*/   2,  4,  4,  6,  4,  6,  6,  8,  4,  6,  6,  8,  6,  8,  8, 10,
};
static int stopat_eof ;		/* 1=stop at EOF, 2=stop at EndOfChunk */
static int swapping ;		/* Set to 1 or 2 (swap)	*/
static int the_status;		/* Last Status Read     */

/*==================================================================
		Internal Utilities
 *==================================================================*/

static int strloc(char *text, int c)
/*++++++++++++++++
.PURPOSE  Locate specified character
.RETURNS  Index of located char
-----------------*/
{
  char *s;
    for ( s = text; *s; s++)      if (*s == c)    break;
    return(s-text);
}

static int get(unsigned char *a, int b, int len)
/*++++++++++++++++
.PURPOSE  Get a value made of 'len' bits
          starting from byte position 'a', bit offset 'b'.
.RETURNS  The value
.REMARKS  Independent of the architecture.
-----------------*/
{
   static unsigned int mask[] = {
    0x00, 0x01, 0x03, 0x07, 0x0f, 0x1f, 0x3f, 0x7f,
    0x00ff, 0x01ff, 0x03ff, 0x07ff, 0x0fff, 0x1fff, 0x3fff, 0x7fff,
    0x00ffff, 0x01ffff, 0x03ffff, 0x07ffff, 0x0fffff,
              0x1fffff, 0x3fffff, 0x7fffff,
    0x00ffffff, 0x01ffffff, 0x03ffffff, 0x07ffffff, 0x0fffffff,
                0x1fffffff, 0x3fffffff, 0x7fffffff,
    0xffffffff } ;
  int value;
  unsigned char *ac;
  int nb ;      /* remaining bits to get */

    ac = a + (b>>3);    /* Byte position  */
    value = *(ac++);    /* Initialisation */
    nb = len;           /* Bits to read.  */
    nb -= 8 - (b&7);    /* Useful bits    */

    /* We don't care about the leftmost bits,
       these will be removed at the end
       (we assume that len <= 32...)
    */

    while (nb >= 8) { value = (value<<8) | *(ac++); nb -= 8; }
    if (nb < 0)         /* I've read too much */
        value >>= (-nb);
    else if (nb)        /* Remainder bits  */
        value = (value<<nb) | (*ac >> (8-nb));

    return(value&mask[len]);
}

static void swap2 (short *array, int nshort)
/*++++++++++++++++
.PURPOSE  Swap the bytes in the array of shorts if necessary
.RETURNS  0/1/2 (type of swap)
.REMARKS  Useful for big-endian machines
-----------------*/
{
  register int m, n ;
  register short *p, *e ;
    for (p=array, e=p+nshort; p<e; p++) {
        n = *p ;
	m =  (n>>8) & 0xff ;
	m |= (n<<8) ;
	*p = m ;
    }
}

#define swap4(a,n)	swap((int *)(a), n)
static void swap (int *array, int nint)
/*++++++++++++++++
.PURPOSE  Swap the bytes in the array of integers if necessary
.RETURNS  0/1/2 (type of swap)
.REMARKS  Useful for big-endian machines
-----------------*/
{
  char *p, *e ;
  int n ;
  
    p = (char *)array ; e = p + 4*nint ;
    if (swapping == 1) swap2((short *)array, 2*nint) ;
    else if (swapping == 2) while (p < e) {
        n = p[0] ; p[0] = p[3] ; p[3] = n ;
        n = p[1] ; p[1] = p[2] ; p[2] = n ;
        p += 4 ;
    }
}

static int4 *binloc(int4 *start, int4 *end, int4 value, int step)
/*++++++++++++++++
.PURPOSE  Find index in table such that    start[i] <= value < start[i+step]
.RETURNS  NULL if pointer < *start / the pointer otherwise
-----------------*/
{
  int4 *low, *high, *med ;
  int i;

    if (value < *start) return((int4 *)0) ;
    /* Compute the highest item */
    i = (end-start)%step;	
    if (i == 0) i = step;
    low=start, high=end-i;
    if (value >= *high) return(high) ;
    while ((high-low) > step) {
    	med = low + step*((high-low)/2/step) ;
    	if (value < *med) high = med;
    	else low = med ;
    }
    return(low) ;
}

#if 0	/* Unused function */
static int binlocf(char *start, int bytes, int reclen, int4 (*f)(), int4 value)
/*++++++++++++++++
.PURPOSE  Find index in table such that   f(p) <= value < f(p+reclen)
.RETURNS  Byte position in start / -1 / bytes
-----------------*/
{
  char *low, *high, *med ;
    if (value < (*f)(start)) return(-1) ;
    low=start, high=start+bytes-reclen;
    if (value >= (*f)(high)) return(bytes) ;
    while ((high-low) > reclen) {
    	med = low + reclen*((high-low)/reclen/2) ;
    	if (value < (*f)(med)) high = med;
    	else low = med ;
    }
    return(low - start) ;
}
#endif

/*==================================================================
		USNOB File Manipulation
 *==================================================================*/
static void init(char *root)
/*++++++++++++++++
.PURPOSE  Initialisation of USNOB access.
.RETURNS  ---
-----------------*/
{
  static int value ;
  char *v ;
  int n ;

    if (USNOBcat.root) return ; 		/* Already opened... */

    /* Verify the Swapping ! */
  
    value = 0x010203 ;
    v = (char *)(&value) ;
    if ((v[0] == 0) && (v[1] == 1) && (v[2] == 2)) 
        swapping = 0 ; 	/* No swap necessary */
    else if ((v[0] == 1) && (v[1] == 0) && (v[2] == 3)) 
        swapping = 1 ; 	/* Half-word swap */
    else if ((v[0] == 3) && (v[1] == 2) && (v[2] == 1)) 
        swapping = 2 ; 	/* Full-word swap */
    else {
        fprintf(stderr, "****Irrationnal Byte Swap %02x%02x%02X%02x\n", 
            v[0]&0xff, v[1]&0xff, v[2]&0xff, v[3]&0xff) ;
	exit(2) ;
    }
    if (swapping && (usnob_options&1)) fprintf(stderr, 
        "#...swapping type=%d\n", swapping) ;

    /* Choose the root name */
    if (root)  USNOBcat.root = root ;
    if (!USNOBcat.root) USNOBcat.root = getenv("USNOBroot") ;
    if (!USNOBcat.root) USNOBcat.root = "/USNOB" ;
    n = 20 + strlen(USNOBcat.root);	/* Size of file name */
    if (n <  48) n = 128 ;
    USNOBcat.name = malloc(USNOBcat.lename = n) ;
    USNOBcat.fno = USNOBcat.SDz  = USNOBcat.dat.RAz = -1 ;
    /* USNOBcat.mbuf = 7*2048 ;
       USNOBcat.abuf = malloc(USNOBcat.mbuf) ;
    */
    memset(&USNOBcat.dat, 0, sizeof(CHUNK)) ;
}

static int usnob_fopen(char *name)
/*++++++++++++++++
.PURPOSE  Open a name-specified file
.RETURNS  0 = OK / -1 = error
-----------------*/
{
  char buffer[sizeof(USNOBcat.line)];
  int file, len, i, odp ;
  char *p;

    if (usnob_options&1) printf("#....usnob_fopen(%s)\n", name) ;
    if (!USNOBcat.root) init((char *)0) ;
    if (USNOBcat.fno >= 0) {
	fprintf(stderr, "++++usnob_fopen: Closing %s\n", USNOBcat.name);
	usnob_close();
    }
    file = open(name, O_BINARY);
    if (file < 0) {  fprintf(stderr, "****"); perror(name);  return (-1); }
    len = read(file, buffer, sizeof(buffer)) ;
    if (len <= 0)  {  fprintf(stderr, "****"); perror(name);  return (-1); }

    if (USNOBcat.name != name) strncpy(USNOBcat.name, name, USNOBcat.lename);
    USNOBcat.fno  = file;
    memset(USNOBcat.line,   0, sizeof(USNOBcat.line));
    memset(USNOBcat.chunks, 0, sizeof(USNOBcat.chunks));
    memset(&USNOBcat.dat,   0, sizeof(CHUNK));

    /* The end of the first line indicates the starting point
       of the List of Chunks 
    */
    len = strloc(buffer, '\n');
    if (len >= (int)sizeof(USNOBcat.line)) {
	fprintf(stderr,  "****File %s: too int4 first line (%d>=%d)\n",
	   name, len, (int)sizeof(USNOBcat.line)) ;
	return(-1);
    }
    memcpy(USNOBcat.line, buffer, len);
    while (len&3) len++;
    lseek(file, len, 0);		/* Reset File to List of Chunks */

    /* Example of a header line:
USNO-B1.0(18) 000/U0000.bin fld=0(0) pm=-500(1001) mag=700(1801) xi=-750(1501) 
USNO-B1*0(18) 000/U0000.bin fld=0(0) pm=-500(1001) mag=700(1801) xi=-750(1501) 
    */

    /* Verify magic */
    USNOBcat.pb_stargal = 0;
    i = strloc(header_text, '('); 
    if (strncmp(buffer, header_text, i+1) != 0) {
	odp = strloc(header_text, '.');
	if ((strncmp(buffer, header_text, odp) == 0) &&
	    (strncmp(buffer+odp+1, header_text+odp+1, i-odp) == 0))
	    USNOBcat.pb_stargal = buffer[odp];
	else {
    	    fprintf(stderr,  
	      "****File %s: bad magic, is not USNO-B1.0\n", name);
    	    return (-1);
	}
    }
    USNOBcat.reclen = atoi(buffer+i+1);

    p = strchr(buffer+i+2, 'U'); 	/* Find the zone */
    USNOBcat.SDz = atoi(p+1);
    USNOBcat.dat.RAz = -1;

    /* Find the parameters in Name=Ofpmx(Nfpmx) */
    for (i=0; i<4; i++) {
	p = strchr(p, '=');
	if (!p) {
	    fprintf(stderr,  "****File %s: missing parameters\n", name);
	    return(-1);
	}
	p++;
	USNOBcat.Ofpmx[i] = atoi(p);
	if (*p == '-') p++;
	while(isdigit(*p)) p++;
	p++;	/* Skip the ( */
	USNOBcat.Nfpmx[i] = atoi(p);
    }

    /* Read the Nchunks*(Offset, ID) designating Chunks. */
    if (read(file, USNOBcat.chunks, sizeof(USNOBcat.chunks)) <= 0) {
	fprintf(stderr, "****"); perror(USNOBcat.name); 
	return(-1);
    }
    if (swapping) swap4(USNOBcat.chunks, 
	    sizeof(USNOBcat.chunks)/sizeof(int));

    /* Find the actual end of Chunks -- there may be zeroes */
    for (i=2; (i<ITEMS(USNOBcat.chunks)) && (USNOBcat.chunks[i]); i += 2) ;
    USNOBcat.nchunks = i>>1;		/* 2 numbers (o,ID) per chunk   */
    USNOBcat.nchunks--;			/* Actually, last indicates EOF */
    USNOBcat.echunks = &(USNOBcat.chunks[i]);

    return(0) ;
}

static int close_chunk()
/*++++++++++++++++
.PURPOSE  Close the currently opened chunk
.RETURNS  0 = OK / -1 = error
-----------------*/
{
    memset(&USNOBcat.dat, 0, sizeof(CHUNK));
    USNOBcat.dat.ppos= -1;	/* Unknown */
    USNOBcat.dat.RAz = -1;
    return(0) ;
}

int usnob_close()
/*++++++++++++++++
.PURPOSE  Close the currently opened file
.RETURNS  0 = OK / -1 = error
-----------------*/
{
    if (USNOBcat.fno < 0) 	/* Was never opened! */
	return(0);
    close_chunk();
    /* Remove Information on existing chunks */
    USNOBcat.nchunks = 0; USNOBcat.echunks = USNOBcat.chunks;
    memset(USNOBcat.chunks, 0, sizeof(USNOBcat.chunks)) ;
    if (close(USNOBcat.fno) < 0) 
        fprintf(stderr, "****"), perror(USNOBcat.name) ;
    USNOBcat.fno = -1 ;
    USNOBcat.SDz = -1 ;
    USNOBcat.pb_stargal  = 0 ;
    USNOBcat.reclen  = 0 ;
    if (USNOBcat.name) USNOBcat.name[0] = 0 ;
    if (USNOBcat.line) USNOBcat.line[0] = 0 ;
    return(0) ;
}

int usnob_zopen(int zone)
/*++++++++++++++++
.PURPOSE  Open a speficied zone (0..1799)
.RETURNS  0 = OK / -1 = error
-----------------*/
{
    if (usnob_options&1) printf("#...usnob_zopen(U%04d)\n", zone);
    if (!USNOBcat.root) init((char *)0);
    if (USNOBcat.SDz == zone) {
        close_chunk();
	return(0);
    }
    usnob_close();		/* Need another file! */
    sprintf(USNOBcat.name, 
      "%s/%03d/U%04d.bin", USNOBcat.root, zone/10, zone);
    return(usnob_fopen(USNOBcat.name));
}

int usnob_stop(int flag)
/*++++++++++++++++
.PURPOSE  Specify if reading should stop at EOF (1), endofChunck (2), never (0)
.RETURNS  Previous status
-----------------*/
{
  int ostat ;
    ostat = stopat_eof ;
    stopat_eof = flag ;
    return(ostat) ;
}

static int read_chunk(int chunkno)
/*++++++++++++++++
.PURPOSE  Load the specified chunk
.RETURNS  0 = OK / -1 = error
.REMARKS  The largest chunck is ~10Mbytes
-----------------*/
{
  int4 o, len, *aint4 ;
  int  ino;
  short *ashort;

    /* The file must be started and loaded */
    if (usnob_options&1) printf("#...read_chunk(%d) in zone U%04d\n",
        chunkno, USNOBcat.SDz) ;
    if (USNOBcat.SDz < 0) return(-1) ;	/* No zone loaded  */

    /* The table of Offsets gives the (location,ID) in the File */
    if (chunkno >= Nchunks-1)	/* Too large chunk number! */
	return(-1);

    /* Accept any chunk number of single-chunk file (pole) */
    if (USNOBcat.reclen == 18) chunkno = 0;
    ino = chunkno<<1;
      o = USNOBcat.chunks[ino] ;
    len = USNOBcat.chunks[ino+2] - o ;
    if (len <= 0) return(-1) ;

    /* Verify chunck not already loaded -- not necessary to reload ! */
    if (USNOBcat.dat.RAz != chunkno) {

        if (lseek(USNOBcat.fno, o, 0) != o) {
            fprintf(stderr, "****Can't move to %d, file: %s\n",
                o, USNOBcat.name) ;
            return(-1) ;
        }

        /* Need to read the whole chunck -- enough memory ? */
        if (USNOBcat.mbuf < len) {
            if (USNOBcat.abuf) free(USNOBcat.abuf) ;
            USNOBcat.mbuf = 1+(len|0xffff) ;    /* Multiple of 64Kbytes */
            USNOBcat.abuf = malloc(USNOBcat.mbuf) ;
        }
        USNOBcat.dat.len = read(USNOBcat.fno, USNOBcat.abuf, len) ;
        if (USNOBcat.dat.len != len) {
            fprintf(stderr, "****Got %d/%d bytes, ", USNOBcat.dat.len, len) ;
            if (USNOBcat.dat.len < 0) perror(USNOBcat.name);
            else fprintf(stderr, "file: %s\n", USNOBcat.name) ;
            return(-1) ;
        }
	/* NOTE: Buffer was rounded -- the actual size may be 
	   up to 3 bytes less. We therefore diminish the chunk length,
	   but will test more carefully for the end-of-chunk.
	*/
	USNOBcat.dat.len -= 3;
    
        aint4 = (int4 *)USNOBcat.abuf;	/* Starts by 7 integers */
        if (swapping) swap4(aint4, 7);	/* Len.preface, minmax	*/
        len = aint4[0];			/* Preface length...	*/
        ashort = (short *)(aint4+7);
        if (swapping) swap2(ashort, (len-7*4)/2);
    
	USNOBcat.dat.RAz  = chunkno;
	USNOBcat.dat.ppos = -1;
        USNOBcat.dat.id0  = aint4[1];
        USNOBcat.dat.ra0  = chunkno<<20;
        USNOBcat.dat.sd0  = USNOBcat.SDz*36000;    /* 0.1deg in 10mas */
        USNOBcat.dat.id1  = aint4[4];
        USNOBcat.dat.ra1  = USNOBcat.dat.ra0 + (1<<20);
        USNOBcat.dat.sd1  = USNOBcat.dat.sd0 + 36000;  /* 0.1deg in 10mas */
	if (USNOBcat.reclen == 18) USNOBcat.dat.ra1 <<= 8;
    
        USNOBcat.dat.Afpmx[0] = ashort + 4;
        USNOBcat.dat.Afpmx[1] = USNOBcat.dat.Afpmx[0] + ashort[0];
        USNOBcat.dat.Afpmx[2] = USNOBcat.dat.Afpmx[1] + ashort[1];
        USNOBcat.dat.Afpmx[3] = USNOBcat.dat.Afpmx[2] + ashort[2];

        /* The Index List starts just after the Preface.
	   The number of elements in this index is computed from
	   the position of the data in index[0].
	*/
        USNOBcat.dat.index = (int4 *)(USNOBcat.abuf + len) ;
	memcpy(&o, USNOBcat.abuf + len, sizeof(int));
	if (swapping) swap4(&o, 1);
        USNOBcat.dat.endex = (int4 *)(USNOBcat.abuf + o) ;
        if (swapping) swap4(USNOBcat.dat.index, 
	    USNOBcat.dat.endex - USNOBcat.dat.index);
    }

    /* Initialize the CHUNK parameters */
    USNOBcat.dat.pos = USNOBcat.dat.index[0];
    USNOBcat.dat.id  = USNOBcat.dat.id0;
    USNOBcat.dat.ppos = -1;

    return(0);
}

static int usnob_next()
/*++++++++++++++++
.PURPOSE  Move to the next redord
.RETURNS  1 = OK / 0 = EOF / -1 = Error
-----------------*/
{
  int len, status;

    if (USNOBcat.dat.pos >= USNOBcat.dat.len) return(0);
    status = (USNOBcat.abuf[USNOBcat.dat.pos])&0xff;
    len = photolen[status] + USNOBcat.reclen;
    USNOBcat.dat.ppos = USNOBcat.dat.pos;
    USNOBcat.dat.pos += len;
    USNOBcat.dat.id  += 1  ;
    if (USNOBcat.dat.pos < USNOBcat.dat.len) return(1);
    if (USNOBcat.dat.pos <= USNOBcat.dat.len+3) /* Leave room for align */
	return(0);
    USNOBcat.dat.ppos = -1;	/* We've lost position of preceding record */
    USNOBcat.dat.pos -= len;
    USNOBcat.dat.id -= 1;
    fprintf(stderr, "****usnob_next %04d#%03d, id=%d: %d(%d) > %d\n",
	USNOBcat.SDz, USNOBcat.dat.RAz, USNOBcat.dat.id, 
	USNOBcat.dat.pos, len, USNOBcat.dat.len);
    return(-1);
}

/*==================================================================
		USNOB File Seek, by Position or Identification
 *==================================================================*/

static int4 aseek(int4 value)
/*++++++++++++++++
.PURPOSE  Position the file to specified RA value (in mas)
.RETURNS  The USNOB1 number in that zone / 0
-----------------*/
{
  int a0, a1, da, bra ;
  int4 *aval;

    value /= 10;	/* Unit is 10mas file USNOB */

    /* Verify -- maybe we're in the correct chunk ? */
    if ((USNOBcat.dat.RAz >= 0) && 
       (value >= USNOBcat.dat.ra0) && (value <= USNOBcat.dat.ra1)) ;
    else {
	if (read_chunk(value>>20)) return(-1) ;
    }

    if ((value < USNOBcat.dat.ra0) || (value >  USNOBcat.dat.ra1)) 
        return(-1) ;
    da = value - USNOBcat.dat.ra0 ;
    bra = USNOBcat.reclen == 17 ? 20 : 28;	/* Number of bits in RA */

    /* We look whether we're not just at the correct location ??? */
    if ((USNOBcat.dat.pos>=0) && (USNOBcat.dat.ppos>=0)) {
	a0 = get((unsigned char *)USNOBcat.abuf + USNOBcat.dat.ppos, 12, bra);
	a1 = get((unsigned char *)USNOBcat.abuf + USNOBcat.dat.pos, 12, bra);
	if ((da > a0) && (da <= a1)) 
	    return(USNOBcat.dat.id);
	/* Go back to the beginning of the chunk (done in read_chunk) */
	if (read_chunk(USNOBcat.dat.RAz)) return(-1);
    }

    /* Find the RA position in the index  (o, ID, RA)
       RA(n) <= value < RA(n+1)) 
    */
    aval = binloc(USNOBcat.dat.index+2, USNOBcat.dat.endex, value, 3) -2;
    if (!aval) aval = USNOBcat.dat.index;

    /* Move in the chunk */
    while (USNOBcat.dat.pos < USNOBcat.dat.len) {
	a1 = get((unsigned char *)USNOBcat.abuf + USNOBcat.dat.pos, 12, bra);
	if (a1 >= da) return(USNOBcat.dat.id);
	if (usnob_next()<=0) break;
    }
    return(0);		/* Impossible... */
}

int4 usnob_seek(int4 ra, int4 sd)
/*++++++++++++++++
.PURPOSE  Seek to specified position (in mas)
.RETURNS  The corresponding USNOB number (relative to SD zone)
-----------------*/
{
  int4 id;
  int z;

    if (!USNOBcat.root) init((char *)0) ;
    z = sd/Dstep ;
    if ((z<0) || (z >= 1800))
        return(-1) ; 		/* Outside Boundaries */

    /* Maye we're at the right position ? */
    if (USNOBcat.SDz == z) {
	id = aseek(ra);
	if (id > 0) return(id);
    }

    /* We can't find in the loaded zone. Reload. */
    if (usnob_zopen(z)) return(-1) ;

    /* Seek now until the specified RA found */
    return(aseek(ra));
}

static int set_id(int4 id)
/*++++++++++++++++
.PURPOSE  Set the current record to id 
.RETURNS  -1=Error / 0=OK / 1 = Error (too high)
.REMARKS  We assume we're in the correct SDzone.
-----------------*/
{
  int4 *aval, di;
  int i; 

    /* Maybe we're already at the correct location ? */
    if (USNOBcat.dat.id == id) return(0);

    /* A zero (negative) ID sets to beginning of file */
    if (id <= 0) id = 1;

    /* Locate first which chunk is concerned -- i.e. search in listofChunks */
    aval = binloc(USNOBcat.chunks+1, USNOBcat.echunks, id, 2)-1;
    if (!aval) return(-1);		/* e.g. id<0 */
    i = (aval-USNOBcat.chunks)>>1;	/* 2 numbers (o,ID) per chunk */
    if (i >= USNOBcat.nchunks) return(-1) ;

    /* Maybe we're already in the correct chunk -- taken care by read_chunk */
    if (i == USNOBcat.dat.RAz) {
	di = id - USNOBcat.dat.id;
	/* When new ID close to an index boundary, better to use the Index */
	if ((di>(Dacc/3)) && ((id-USNOBcat.dat.id0)%Dacc) < (Dacc/3))
	  di = -1;
    }
    else di = -1;

    /* When asking for just a bit further, use successive read's */
    if (di<0) {
        if (read_chunk(i) < 0) return(-1);
        /* Locate in the index of the Chunk */
        aval = binloc(USNOBcat.dat.index+1, USNOBcat.dat.endex, id, 3);
        USNOBcat.dat.id  = *aval;
        USNOBcat.dat.pos = *--aval;
        USNOBcat.dat.ppos= -1;		/* Not known... */
    }

    /* Loop the in <~1000 (Dacc) records */
    while (USNOBcat.dat.id < id) {
	if (usnob_next()<= 0) return(-1);
    }
    return(0) ;
}

int usnob_set(int zone, int4 id)
/*++++++++++++++++
.PURPOSE  Position in specified zone + id
.RETURNS  0 / -1
-----------------*/
{
    if (!USNOBcat.root) init((char *)0) ;
    /* Go to specified zone */
    if (zone == USNOBcat.SDz) ;
    else if (usnob_zopen(zone)) return(-1);

    return(set_id(id));
}

/*==================================================================
		Convert the Input Record(s)
 *==================================================================*/
static int extra_value(int value, int idxno)
/*++++++++++++++++
.PURPOSE  Retrieve a value from Index
.RETURNS  The Value
-----------------*/
{
  int i;
    if (value <= USNOBcat.Nfpmx[idxno]) return(value);
    i = value - USNOBcat.Nfpmx[idxno];
    return(USNOBcat.dat.Afpmx[idxno][i-1]);
}

static int ed_rec(USNOBrec *prec)
/*++++++++++++++++
.PURPOSE  Convert the current compressed USNOB record into its standard 
	  structure
.RETURNS  -1=Error / 0=OK / 1 = Error (too high)
-----------------*/
{
  USNOBtyc *ptyc;
  int4 value ;
  unsigned char *pc;
  int status, len, m, i ;
  short fld, mag, xi, eta;

    memset(prec, 0, sizeof(USNOBrec));
    ptyc = (USNOBtyc *)prec;

    /* Convert the compacted record */
    pc = (unsigned char *)(USNOBcat.abuf + USNOBcat.dat.pos) ;
    status = *pc;
    the_status = status;  /* printf("=%02X", status); */
    prec->flags = status&USNOB_TYC;
    prec->ndet = pc[1]>>4;
    prec->zone = USNOBcat.SDz;
    prec->id   = USNOBcat.dat.id;
    prec->ra   = ((pc[1]&0x0f)<<16) | (pc[2]<<8) | pc[3];
    if (USNOBcat.reclen == 18) {
	++pc;
	prec->ra <<= 8;
	prec->ra |= pc[3]; 
    }
    prec->ra  |= USNOBcat.dat.ra0;
    prec->ra  *= 10;		/* Express in mas */

    prec->sd   = (pc[4]<<8) | pc[5];
    prec->sd  += USNOBcat.dat.sd0;
    prec->sd  *= 10; 		/* Express in mas */

    prec->pmtot= -1;
    prec->pmra = (pc[11]<<4) | (pc[12]>>4);
    prec->pmsd = ((pc[12]&0x0f)<<8) | pc[13];
    prec->pmra = 2*(extra_value(prec->pmra, 1) + USNOBcat.Ofpmx[1]);
    prec->pmsd = 2*(extra_value(prec->pmsd, 1) + USNOBcat.Ofpmx[1]);

    if (status&USNOB_TYC) {
	prec->epoch = 20000;
	ptyc->TYC1 = (pc[6]<<8) | pc[7];
	ptyc->TYC2 = (pc[8]<<8) | pc[9];
	ptyc->TYC3 = pc[10];
	ptyc->fileno = (pc[14]>>2)&0x1f;
	ptyc->recno = ((pc[14]&3)<<16) | (pc[15]<<8) | pc[16];
	if (pc[14]&0x80) ptyc->recno = -ptyc->recno;
	if (ptyc->fileno == 21) prec->flags |= USNOB_TS1;
	if (ptyc->fileno == 22) prec->flags |= USNOB_TS2;
    }
    else {
        prec->flags = pc[8]&(USNOB_PM|USNOB_SPK|USNOB_YS4);
        prec->e_ra = (pc[6]<<2) | (pc[7]>>6);
        prec->e_sd = ((pc[7]&0x3f)<<4) | (pc[8]>>4);
        prec->epoch = (((pc[8]&1)<<8) | pc[9]) + 19500;
        prec->fit_ra = pc[10]>>4;
        prec->fit_sd = pc[10]&0x0f;
	prec->muprob = pc[14]>>4;
	prec->e_pmra = ((pc[14]&0x0f)<<6) | (pc[15]>>2);
	prec->e_pmsd = ((pc[15]&0x03)<<8) |  pc[16];
    }
    prec->rho = -1 ;

    /* Photometries */
    if (status&USNOB_TYC) len = 2;
    else len = status&USNOB_ph7 ? 7 : 6;
    pc += 17;
    for (i=0, m=16; m; m >>= 1, i++) {
	prec->mag[i] = 9999;			/* NULL Magnitude */
	if ((status&m) == 0) continue;
	if (len == 2) {
	    prec->mag[i] = (pc[0]<<8) | pc[1];
	    pc += len;
	    continue;
	}
	value = (pc[0]<<3) | (pc[1]>>5);	/* stargal*100+calib*10+survey*/
	prec->phot[i].survey = value%10; value /= 10;
	prec->phot[i].calib  = value%10; value /= 10;
	prec->phot[i].stargal = value;
	prec->phot[i].pb_stargal = USNOBcat.pb_stargal;

	if (len == 6) {		/* SHORT RECORDS */
	    fld = (pc[1]>>1)&0xf;
	    mag = ((pc[1]&0x01)<<10) | (pc[2]<<2) | (pc[3]>>6);
	    xi  = ((pc[3]&0x3f)<< 5) | (pc[4]>>3);
	    eta = ((pc[4]&0x07)<< 8) | pc[5];
	}
	else {			/* LONG  RECORDS */
	    fld = ((pc[1]&0x1f)<<1) | (pc[2]>>7);
	    mag = ((pc[2]&0x7f)<<6) | (pc[3]>>2);
	    xi  = ((pc[3]&0x03)<<11)| (pc[4]<<3) | (pc[5]>>5);
	    eta = ((pc[5]&0x1f)<<8) |  pc[6];
	}
	fld = extra_value(fld, 0) + USNOBcat.Ofpmx[0];
	mag = extra_value(mag, 2) + USNOBcat.Ofpmx[2];
	xi  = extra_value(xi , 3) + USNOBcat.Ofpmx[3];
	eta = extra_value(eta, 3) + USNOBcat.Ofpmx[3];
	prec->mag[i] = mag;
	prec->phot[i].field = fld;
	prec->phot[i].xi    = xi;
	prec->phot[i].eta   = eta;
	pc += len;
    }

    return(0) ;
}

int usnob_read(USNOBrec *rec)
/*++++++++++++++++
.PURPOSE  Read next record in USNOB
.RETURNS  0(End) / -1 (Err) / 1(OK)
.REMARKS  When end if a RA file is found, action depends on stopat_eof
	When rec is NULL, jusr set to to next.
-----------------*/
{
  int i; 

    if (!USNOBcat.root) init((char *)0) ;
    if ((!USNOBcat.abuf) || (USNOBcat.SDz < 0)) {
	i = USNOBcat.SDz;
	if (i < 0) i=0, fprintf(stderr, 
	    "++++usnob_read: no zone specified, read from South Pole\n");
	if (usnob_set(i, 0) < 0) return(-1);
    }
    if (USNOBcat.dat.pos >= USNOBcat.dat.len) {	/* End of Chunk ? */
	if (stopat_eof == 2) return(0) ;
	i = USNOBcat.dat.RAz + 1;		/* Next Chunk */
	if (i >= USNOBcat.nchunks) {		/* Need to read a new file */
	    if (stopat_eof) return(0);
	    i = USNOBcat.SDz+1;			/* New Zone...*/
	    if (i >= 1800) return(0);		/* FINAL END  */
	    if (usnob_zopen(i)) return(-1);
	    i = 0;
	}
	if (read_chunk(i)) return(-1);
    }
    if (rec) ed_rec(rec) ;
    usnob_next();
    return(1) ;
}

int usnob_get(int zone, int4 id, USNOBrec *rec)
/*++++++++++++++++
.PURPOSE  Read specified record in USNOB
.RETURNS  0 / -1
-----------------*/
{
    if (usnob_set(zone, id) < 0) return(-1) ;
    return(usnob_read(rec)) ;
}

static int edra10mas(char *buf, int4 ra, int opt /* 0=deg, 1=sexa 16=mas */)
/*++++++++++++++++
.PURPOSE  Edit a RA (unit=10mas) into HH:MM:SS.SSS
.RETURNS  Number of bytes (12 or 10)
-----------------*/
{
  int i ; 
  int4 value ;
    if (opt&16) {
	value = ra; 
	i=10;           buf[--i] = '0' ;
	while (value>0) buf[--i] = '0' + value%10, value /= 10;
    	while (i>0)     buf[--i] = ' ';
    	return(10);
    }
    if (opt) {		/* Sexagesimal */
    	value = ra ;
    	value = value - (value/3) ;	/* 2/3 for number in ms */
    	for (i=11; i>8; i--) buf[i] = '0' + value%10, value /= 10 ;
    	buf[8] = '.' ;
    	buf[7] = '0' + value%10, value /= 10 ;
    	buf[6] = '0' + value%6,  value /= 6 ;
    	buf[5] = ':' ;
    	buf[4] = '0' + value%10, value /= 10 ;
    	buf[3] = '0' + value%6,  value /= 6 ;
    	buf[2] = ':' ;
    	buf[1] = '0' + value%10, value /= 10 ;
    	buf[0] = '0' + value ;
    	return(12) ;
    }
    else {
    	value = 3*ra ;	/* 10^6/360000 = 3 * (1 - 2/27) */
    	value -= (2*value)/27 ;
    	for (i=9; i>3; i--) buf[i] = '0' + value%10, value /= 10 ;
    	buf[3] = '.' ;
    	buf[2] = '0' + value%10, value /= 10 ;
    	buf[1] = '0' + value%10, value /= 10 ;
    	buf[0] = '0' + value ;
    	return(10) ;
    }
}

static int edsd10mas(char *buf, int4 sd, int opt /* 0=deg, 1=sexa */)
/*++++++++++++++++
.PURPOSE  Edit a SPD (unit=10mas) into +DD:MM:SS.SS
.RETURNS  Number of bytes (12 or 10)
-----------------*/
{
  int i ; 
  int4 value ;
    value = sd - 90*3600*100 ;
    if (value > 0) buf[0] = '+' ;
    else buf[0] = '-', value = -value ;
    if (opt&16) {
	i=10;           buf[--i] = '0' ;
	while (value>0) buf[--i] = '0' + value%10, value /= 10;
	buf[--i] = buf[0];
    	while (i>0)     buf[--i] = ' ';
    	return(10);
    }
    if (opt) {		/* Sexagesimal */
    	buf[11] = '0' + value%10, value /= 10 ;
    	buf[10] = '0' + value%10, value /= 10 ;
    	buf[9] = '.' ;
    	buf[8] = '0' + value%10, value /= 10 ;
    	buf[7] = '0' + value%6,  value /= 6 ;
    	buf[6] = ':' ;
    	buf[5] = '0' + value%10, value /= 10 ;
    	buf[4] = '0' + value%6,  value /= 6 ;
    	buf[3] = ':' ;
    	buf[2] = '0' + value%10, value /= 10 ;
    	buf[1] = '0' + value ;
    	return(12) ;
    }
    else {
    	value = 3*value ; 		/* 10^6/360000 = 3 * (1 - 2/27) */
    	value -= ((2*value)/27) ; 
    	for (i=9; i>3; i--) buf[i] = '0' + value%10, value /= 10 ;
    	buf[3] = '.' ;
    	buf[2] = '0' + value%10, value /= 10 ;
    	buf[1] = '0' + value ;
    	return(10) ;
    }
}

static int edmag(char *buf, int mag) 
/*++++++++++++++++
.PURPOSE  Edit a Magnitude in cmag
.RETURNS  Number of bytes (5)
-----------------*/
{
  int value ;
  value = mag ;
    buf[0] = buf[1] = buf[2] = buf[3] = buf[4] = ' ' ;
    if (value >= 9999) 
	buf[1] = buf[2] = buf[3] = '-'; 
    else {
        if (value < 0) value = -value, buf[0] = '-';
        buf[4] = '0' + value%10, value /= 10 ;
        buf[3] = '0' + value%10, value /= 10 ;
        buf[2] = '.' ;
        buf[1] = '0' + value%10, value /= 10 ;
        if (value) buf[0] = '0' + value ;
    }
    return(5) ;
}

static int ed06_2(char *buf, int xi) 
/*++++++++++++++++
.PURPOSE  Edit the xi/eta values
.RETURNS  Number of bytes (6)
-----------------*/
{
  int value;
    if (xi>=0) { buf[0] = '+'; value =  xi; }
    else       { buf[0] = '-'; value = -xi; }
    buf[5] = '0' + value%10, value /= 10;
    buf[4] = '0' + value%10, value /= 10;
    buf[3] = '.';
    buf[2] = '0' + value%10, value /= 10;
    buf[1] = '0' + value%10, value /= 10;
    if(value) {
        buf[1] = buf[2] = buf[4] = buf[5] = '9';
	if (buf[0] == '+') buf[0] = '>';
	else strncpy(buf, "<=-100", 6);
    }
    return(6) ;
}

static int edmas(char *buf, int4 value)
/*++++++++++++++++
.PURPOSE  Edit a value in units of mas as arcsec
.RETURNS  Number of bytes written. Round to 0.01arcsec
-----------------*/
{
  static char aval[16] ;
  char s, *p, *b ;  int4 x ;
    if (value < 0) s = '-', x = (5-value)/10;
    else           s = 0  , x = (6+value)/10;
    p = aval + sizeof(aval) ;
    *--p = 0 ;
    *--p = '0' + x%10 ; x /= 10 ;
    *--p = '0' + x%10 ; x /= 10 ;
    *--p = '.' ;
    do { *--p = '0' + x%10, x /= 10 ; }
    while (x) ;
    if (s) *--p = s ;

    for (b = buf, x = 9 - strlen(p) ; --x >= 0; b++) *b = ' ' ;
    while (*p) *(b++) = *(p++) ;
    *b = 0 ;
    return(b-buf) ;
}

/*==================================================================
		Edit a Record
 *==================================================================*/

char *usnob_head(int opt 
	/*0=deg, 1=sexa, 2=ID, 4=Ep, 8=x,y, 64=basic, 128=pos.Only */)
/*++++++++++++++++
.PURPOSE  Get the Header for one edition
.RETURNS  The Header, starting by #
-----------------*/
{
  static char *magtitle[] = {	/* Titles of Magnitudes */
    "Bmag1", "Rmag1", "Bmag2", "Rmag2", "Imag"
  };
  static char buf[500] ;
  char *p; int i, b ;

    p = buf ; b = '#' ;

    if (opt&128) ;	/* V1.5 */
    else if (opt&2) {	/* Edit the USNO-ID */
    	sprintf(p, "#%-11s", "USNO-B1.0");
    	p += strlen(p) ;
	b = ' ';	/* Separator */
	if (opt&64) {	/* V1.5: Basic edition (no Tycho#) */
	    *(p++) = b;
	    *(p++) = 'T';
	}
        else {
	    sprintf(p, "%c%-12s", b, "Tycho-2"); 
	    p += strlen(p);
        }
        *(p++)= ' ';
    }

    /* Edit the Position */
    i = edra10mas(p, 0, opt&17) + edsd10mas(p, 0, opt&17);
    b = (i-15)/2;
    if (p == buf)   { *(p++) = '#'; b--; }
    while(--b >= 0) { *(p++) = ' '; i--; }
    strcpy(p, "RA  (J2000) Dec"), i -= 15, p += 15;
    while(--i >= 0) *(p++) = ' ';
    if (opt&128) {	/* V1.5: pos.only */
	*p = 0;
	return(buf);
    }
    *(p++) = ' ';

    /* Edit the sigma's */
    strcpy(p, "sRA sDE "); p += strlen(p);

    /* Epoch */
    if (opt&4) 
	strcpy(p, " Epoch "), p += strlen(p);

    /* Proper Motions + Muprob + Sigmas */
    sprintf(p, "%6s %6s P spA spD ", "pmRA", "pmDE");
    p += strlen(p);

  if (opt&64) ;		/* V1.5: Basic edition */
  else {
    /* FITs, Ndet */
    strcpy(p, "Fit N "), p += strlen(p);

    /* Flags */
    strcpy(p, "MsY"), p += strlen(p);
  }
  *(p++) = '|';

    /* Magnitudes */
    for (i=0; i<5; i++) {
	sprintf(p, opt&64 ? /* V1.5: Basic = only mag. */
		   "%6s|" :
		   "%6s C Surv. cl <-xi-><-eta>|", 
		magtitle[i]);
	p += strlen(p);
    }

    /* Distance in arcsec */
    if (opt&8) sprintf(p, " ;%9s %9s", "x(\")", "y(\")");
    else sprintf(p, " ;%9s", "r(\")");
    p += strlen(p);

    *p = 0;
    return(buf) ;
}

char *usnob2a(USNOBrec *pr, 
   int opt /*0=deg, 1=sexa, 2=ID, 4=Ep, 8=x,y, 64=basic, 128=pos.Only */)
/*++++++++++++++++
.PURPOSE  Edit (in a static buffer) one record.
.RETURNS  The edited record
-----------------*/
{
  static char buf[500] ;
  USNOBtyc *pt;
  char *p ; int i ;
  int4 value ;
    p = buf ;

    pt = pr->flags&USNOB_TYC ? (USNOBtyc *)pr : (USNOBtyc *)0;
    if (opt&128) ;	/* V1.5 */
    else if (opt&2) {
    	sprintf(p, "%04d-%07d ", pr->zone, pr->id) ;
    	p += strlen(p) ;

        /* Tycho Number */
        if (opt&64) { 	/* V1.5: basic edition */
	    *(p++) = pr->flags&USNOB_TYC ? 'T' : ' ';
	    *(p++) = ' ';
        }
        else {
            if (pr->flags&USNOB_TYC) {
	        sprintf(p, "%04d-%05d-%d ", pt->TYC1, pt->TYC2, pt->TYC3);
            }
            else {
	        sprintf(p, "%-12s ", "");
            }
            p += strlen(p);
        }
    }

    /* Edit the Position */
    p += edra10mas(p, pr->ra/10, opt&17) ;
    p += edsd10mas(p, pr->sd/10, opt&17) ;
    if (opt&128) {	/* V1.5: pos.only */
	*p = 0;
	return(buf);
    }
    *(p++) = ' ';

    /* Edit the sigma's */
    sprintf(p, "%3d %3d ", pr->e_ra, pr->e_sd);
    p += strlen(p) ;

    /* Epoch */
    if (opt&4) {
	sprintf(p, "%d.%d ", pr->epoch/10, pr->epoch%10);
	p += strlen(p) ;
    }

    /* Proper Motions + Muprob + Sigmas -- Note that pmsd = pmdec */
    sprintf(p, "%+6d %+6d ", pr->pmra, pr->pmsd);
    p += strlen(p);
    *(p++) = pt ? '-' : '0'+pr->muprob;
    *(p++) = ' ';
    sprintf(p, "%3d %3d ", pr->e_pmra, pr->e_pmsd);
    p += strlen(p);

    /* FITs, Ndet */
  if (opt&64) ;		/* V1.5: Basic edition */
  else {
    *(p++) = pr->fit_ra+'0'; *(p++) = ' ';
    *(p++) = pr->fit_sd+'0'; *(p++) = ' ';
    *(p++) = pr->ndet  +'0'; *(p++) = ' ';

    /* Flags */
    *(p++) = pr->flags&USNOB_PM ? 'M' : '.';
    *(p++) = pr->flags&USNOB_SPK? 's' : '.';
    *(p++) = pr->flags&USNOB_YS4? 'Y' : '.';
  }
    *(p++) = '|';

    /* Magnitudes */
    for (i=0; i<5; i++) {
        *(p++) = ' ';
	p += edmag(p, pr->mag[i]);
	if (opt&64) {	/* V1.5: Basic = only mag. */
	    *(p++) = '|';
	    continue;
	}
	*(p++) = ' ';
	if (pt || (pr->mag[i] >= 9999)) {
	    strcpy(p, "- --    --             |");
	    p += strlen(p);
	    continue;
	}
	*(p++) = pr->phot[i].calib+'0';  *(p++) = ' ';	/* Calib */
	*(p++) = pr->phot[i].survey+'0'; *(p++) = '-';	/* Survey#*/
	sprintf(p, "%03d ", pr->phot[i].field); p += strlen(p); 
	value = pr->phot[i].stargal;			/* StarGal*/
	if (value == 19) p[0] = p[1] = '-';
	else {
	    p[1] = value%10+'0'; value /= 10;
	    p[0] = value ? '1' : ' ';
	}
	p += 2; *(p++) = ' ';
	/* Residuals */
	p += ed06_2(p, pr->phot[i].xi);
	p += ed06_2(p, pr->phot[i].eta);
	*(p++) = pr->phot[i].pb_stargal ? pr->phot[i].pb_stargal : '|';
	/* sprintf(p, "%+04d%+04d%c", pr->phot[i].xi, pr->phot[i].eta,
	    pr->phot[i].pb_stargal ? pr->phot[i].pb_stargal : '|');
	p += strlen(p);
	*/
    }

    /* Distance in arcsec */
    if (pr->rho >= 0)  {
	*(p++) = ' ' ; *(p++) = ';' ; *(p++) = ' ' ; 
	if (opt&8) {	/* Edit x,y */
	    p += edmas(p, pr->xy[0]);
	    *(p++) = ' '  ;
	    p += edmas(p, pr->xy[1]);
	}
	else p += edmas(p, pr->rho) ;
    }

    *p = 0 ;
    return(buf) ;
}

static int prec(USNOBrec *rec) { 	/* DEFAULT ACTION ROUTINE */
    printf("%s\n", usnob2a(rec, 3)); 
    return(1); 
}

/*==================================================================
		Operate on a file
 *==================================================================*/

void tr_ou(double o[2], double u[3])
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

static int s2dist(int *a1, int *a2)
/*++++++++++++++++
.PURPOSE  Sort routine (called by qsort), 5 integers (min,max(sd) minx,max(ra)
		distance)
.RETURNS  <0 0 >0
-----------------*/
{
  int diff ;
    diff = a1[4] - a2[4] ;
    if (!diff) diff = a1[0] - a2[0] ;
    return(diff) ;
}

int4 usnob_search(int4 ra[2], int4 sd[2], int (*digest_routine)())
/*++++++++++++++++
.PURPOSE  Search USNO stars within range of positions.
.RETURNS  Number of tested records.
.REMARKS  The supplied digest_routine(USNOBrec *record) does whatever,
	return -1 if stop asked. Default is just to print out.
	The search is done from middle to borders, according to
	a crude distance estimate between the center and the point
  ===>	When usnob_options&0x10 ==> Keep Original Order  <===
-----------------*/
{
  static USNOBrec rec ;
  double u[3], u0[3], dsin, dx, du;
  int4 lac[256*2], ldc[1800*2];		/* Limits on one zone */
  int4 ld[2], la[2], d, a, acen, dcen, high;
  int4 dist2, tested_records ;
  int ja, jd, i, *alist, *p;
  int goon, saved_eof ;

    if (!USNOBcat.root) init((char *)0) ;
    if (!digest_routine) digest_routine = prec ;
    saved_eof = stopat_eof ; 
    stopat_eof = 2 ;			/* Stop after each chunk */
    tested_records = 0 ;

    /* Verify whole range */
    if (ra) {
	if ((ra[0] == 0) && (ra[1] >= 360*3600*1000-10))
	   ra = (int4 *)0;
    }
    if (sd) {
	if ((sd[0] == 0) && (sd[1] >= 180*3600*1000-10)) 
	   sd = (int4 *)0;
    }

    if (!ra) {
	if (!sd) {	/* Whole Sky */
	    if (USNOBcat.fno >= 0) usnob_close();
	    stopat_eof = 0;
	    while (usnob_read(&rec)) {
		tested_records++;
		if ((*digest_routine)(&rec) < 0)        /* Ask to stop! */
		    break;
	    }
	    stopat_eof = saved_eof ;
	    return(tested_records) ;
	}
	stopat_eof = 1;	/* No test on RA ==> stop at end-of-file */
	ra = la;
	ra[0] = 0; ra[1] = (360*3600*1000)-1;
    }
    if (!sd) {
        sd = ld ;
	sd[0] = 0;
	sd[1] = 180*3600*1000;
    }

    /* Set the limits in their legal range/order. 
       Remember that the order of RA limits is important !
    */
    ld[0] = sd[0] ;
    ld[1] = sd[1] ;
    if (ld[0] > ld[1]) d=ld[1], ld[1]=ld[0], ld[0]=d ;
    la[0] = ra[0] % (360*3600*1000);
    la[1] = ra[1] % (360*3600*1000);

    /* Direction Cosines of the Center */
    acen = (la[0]/2) + (la[1]/2) + ((la[0]&1)+(la[1]&1))/2; /* Mod. V1.51 */
    if(la[0]>la[1]) acen += 180*3600*1000;
    if(acen >= 360*1000*3600) acen -= 360*1000*3600;
    dcen = (ld[0] + ld[1])/2; 
    dsin  = sind(dcen/3.6e6);
    u0[0] = dsin*cosd(acen/3.6e6);
    u0[1] = dsin*sind(acen/3.6e6);
    u0[2] = cosd(dcen/3.6e6);

    /* Limits on the Zones */
    ldc[0] = ld[0];
    jd = 1;
    high = (Dstep*(ldc[0]/Dstep)) + (Dstep-1);
    while (ld[1] > (high+1)) {	/* The pole requires the +1 */
	ldc[jd++] = high;
	ldc[jd++] = high+1;
	high += Dstep;
    }
    ldc[jd++] = ld[1];
    /* jd = 2*Number of zones   */

    /* Distribute RA Range */
    lac[0] = la[0];
    ja = 1;
    if (stopat_eof == 2) {
        a = ((lac[0]/10) >> 20) ;	/* Chunk index */
        high = (a<<20) | 0xfffff;	/* Upper Limit 10mas */
        high *= 10;			/* Upper limit, mas  */
        if (high >= 360*3600*1000) high = 360*3600*1000-1;
        if (la[0] > la[1]) {		/* Around 0deg 10mas */
	    lac[ja++] = high;
	    while (high < 360*3600*1000-10) {
	        lac[ja++] = high+10;	/* V1.3 Corrected */
	        high += (1<<20)*10; 
		if (high >= 360*3600*1000) high = 360*3600*1000-1;
		lac[ja++] = high;	/* V1.3 Corrected */
	    }
	    lac[ja++] = 0;
	    high = 0xfffff;
        }
        while (la[1] > high) {
	    lac[ja++] = high;
	    lac[ja++] = high+10;
	    high += (1<<20)*10; 
        }
    }
    lac[ja++] = la[1] ;
    /* ja = 2*Number of RA zones */

    /* Create a table with all the chunks to read.	*/
    alist = (int *)malloc(((ja*jd/4) + 1)*5*sizeof(int));
    for (i=0, d=0; d<jd; d+=2) {
	dcen = (ldc[d]+ldc[d+1]+1)/2;
	u[2] = cosd(dcen/3.6e6);
	dsin = sind(dcen/3.6e6);
	for (a=0; a<ja; a+=2) {
	    alist[i++] = ldc[d]; alist[i++] = ldc[d+1];
	    alist[i++] = lac[a]; alist[i++] = lac[a+1];
	    if (usnob_options&0x10) dist2 = 0;
	    else {
		acen = (lac[a]/2)+(lac[a+1]+1)/2;
		u[0] = dsin*cosd(acen/3.6e6);
		u[1] = dsin*sind(acen/3.6e6);
		dx = u[0]-u0[0];
		du = dx*dx;
		dx = u[1]-u0[1];
		du += dx*dx;
		dx = u[2]-u0[2];
		du += dx*dx;
		dist2 = (du*4.e8) ;
	    }
	    alist[i++] = dist2;
        }
    }
    /* End Indicator */
    alist[i++] = -1; alist[i++] = -1;
    alist[i++] = -1; alist[i++] = -1;
    alist[i++] = -1;

    if (usnob_options&0x10) ;
    else qsort(alist, (ja*jd)/4, 5*sizeof(int), (SORT_FCT)s2dist);

    /* Loop on the zones */
    for (goon=0, p=alist; (goon>=0) && (p[4]>=0); p += 5) {
	/* Ignore the large distances  written when reclen=28 */
	if (p[4] >= 1999999999) continue;
	if (usnob_seek(p[2], p[0]) < 0) break;
	while((goon>=0) && (usnob_read(&rec) > 0)) {
	    tested_records++;
	    if (rec.ra > p[3]) break;
	    if (rec.sd < p[0]) continue;
	    if (rec.sd > p[1]) continue;
	    goon = (*digest_routine)(&rec);
	    /* goon=1 for good, 0 for rejected, -1 for stop	*/
	}
    }

    free(alist);
    stopat_eof = saved_eof ;
    return(tested_records) ;
}

/*==================================================================
		Main Program
 *==================================================================*/
#ifdef TEST
static char usage[] = "\
Usage: usnob_sub [-b bin_file] compressed_input_zone\n\
";

static char help[] = "\
		      -b: Compare with file created by pmm80 -o \n\
   compressed_input_zone: one of the files created by usnob_make\n\
";
int main (argc, argv) int argc; char **argv;
{
  FILE *bf; char *bname;
  char buf[BUFSIZ], *p ;
  int4 id = 0, ra, sd ;
  double q[2];
  int  getpos = 0 ;
  int  z, len, records;
  USNOBrec rec, brec ;
  char read_zone = 0;

    usnob_options = 1 ;
    bf = (FILE *)0; bname = (char *)0;
    while (argc > 2) {
	p = *++argv; --argc;
	if (*p != '-') break;
	if (p[1] != 'b') break;
	p = *++argv; argc--;
	bf = fopen(p, "r");
	if (!bf) perror(p);
	bname = p;
    }
    if (argc != 2) {
	fprintf(stderr, "%s%s", usage, help) ;
	exit(1) ;
    }
    ++argv;
    if (strcmp(*argv, "-q") == 0) getpos = 2 ;
    else if (**argv != '-') usnob_fopen(*argv); 

    usnob_stop(1);		/* Stop at EOF */
    records = 0;
    while (1) {
	buf[0] = 0;
	if (bf) fread(&brec, sizeof(brec),1,bf);
    	else if (isatty(0) && (read_zone == 0)) { 
	    if (getpos) 
		 printf("----Give a position (degrees): ") ;
    	    else printf("----Give a zone USNO-B number: ") ;
    	    if (! fgets(buf, sizeof(buf), stdin)) break ;
        } else buf[0] = 0 ;
	if (buf[0]) {
	    for (p=buf; isspace(*p); p++) ;
	    q[0] = atof(p) ;
	    while (isgraph(*p)) p++ ;
	    q[1] = atof(p) ;
	    if (getpos) {
	    	ra = q[0]*3.6e6 ; sd = 3.6e6*(90. + q[1]) ;
	    	id = usnob_seek(ra, sd) ;
	    } 
	    else {
		z = q[0] ; id = q[1];
		if (usnob_set(z, id) < 0) continue;
		read_zone = id == 0;
	    }
	}
    	len = usnob_read(&rec);
	if (len>0) records++,
	    printf("%s\n%s\n", usnob_head(7), usnob2a(&rec, 7)),
	    printf("%s\n%s\n", usnob_head(6), usnob2a(&rec, 6)),
	    printf("%s\n%s\n", usnob_head(0), usnob2a(&rec, 0)) ; 
	else { printf("====EOF====\n"); break; }
	if (bf) { int i, *a, *b;
	    len = rec.flags&USNOB_TYC ? sizeof(USNOBtyc) : sizeof(brec);
	    if (memcmp(&rec, &brec, len)) {
    		printf("=%02X ", the_status);
    		printf("++ %04d-%d, ra=%010d, sd=%09d ",
	    	   rec.zone, rec.id, rec.ra, rec.sd);
		printf("++ DIFFER!\n");
		a = (int *)&rec; b=(int *)&brec;
		for (i=0; i<sizeof(rec); i+=4, a++, b++) {
		    if (*a != *b) printf("    +%3d: %08X %08X\n", i, *a, *b);
		}
	    }
	}
    	else printf("== %04d-%d, ra=%010d, sd=%09d\n",
	    rec.zone, rec.id, rec.ra, rec.sd);
    }
    printf("====Total of records read: %d\n", records);
    usnob_close() ;
    exit(0);
}
#endif
