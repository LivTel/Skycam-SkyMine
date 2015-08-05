cat/
=============

# What is this?

This is where the APASS database and USNOB files go. They are not stored in 
this repository. 

The catalogue used is selected through the pipeline.ini file in etc/pipe/. 
Generally, we use the APASS database which has a better colour match to 
the unfiltered Skycam cameras. 

## APASS

If using APASS for source cross-matching, you are not required to keep a 
local copy. 

For both local and remotely hosted copies, you will need to change your 
host/ip/user/pw details for the "apass" entry in the etc/pipe/PW_LIST file 
accordingly.

### ingesting an APASS database

* install postgres:

`sudo yum install postgres postgres-server postgresql-devel pgadmin3`

* initialise postgres:

`initdb -D /some/path`

* change lockfile permissions:

`sudo chmod o+w /var/run/postgresql/`

* start postgres server:

`postgres -D /same/path/as/before`

* create database:

`createdb apass`

* install postgis:

`sudo yum install postgis`

* download pgSphere [source](http://pgfoundry.org/frs/?group_id=1000240&release_id=1577#pgsphere-_1.1.1-title-content):

* install pgSphere:

`make USE_PGXS=1`
`sudo make install USE_PGXS=1`

* edit resulting .sql (/usr/share/pgsql/contrib/pg_sphere.sql) file that is 
used to load the functions. Change instances of LANGUAGE 'C' to LANGUAGE 'c' 
(i.e. lowercase). Change instances of LANGUAGE 'SQL' to LANGUAGE 'sql' 
(i.e. lowercase)

* load functions into database

`psql apass < /usr/share/pgsql/contrib/pg_sphere.sql`

* after adding pgsphere support, create table "stars":

`psql: create table stars(id bigserial primary key not null, name text not   
null, RADeg real not null, RAErrAsec real not null, DECDeg real not null,  
DECErrAsec real not null, NightsObs integer not null, ImagesObs integer not   
null, Vmag real not null, BVmag real not null, Bmag real not null, Gmag real   
not null, Rmag real not null, Imag real not null, Verr real not null, BVerr   
real not null, Berr real not null, Gerr real not null, Rerr real not null,   
Ierr real not null, coords spoint);`  

* ingest data into postgres server.

* update coords field with pgSphere spoint type:

`UPDATE stars SET coords = spoint(radians(radeg), radians(decdeg));`

* (optional) add a spherical index on this field:

`CREATE INDEX stars_coords ON stars USING GIST(coords);`

* (optional) cluster on this index

`CLUSTER stars_coords ON stars;`

### hosting your own local copy

Assuming you have access to a copy of the database, ensure you have a 
directory structure like, e.g.

`[rmb@rmb-tower apass]$ pwd`

> /skycam/SkyMine/cat/apass

`[rmb@rmb-tower apass]$ ls`

> base         pg\_ident.conf  pg\_serial     pg\_tblspc    postgresql.conf  
> global       pg\_log         pg\_snapshots  pg\_twophase  postmaster.opts  
> pg\_clog      pg\_multixact   pg\_stat_tmp   PG\_VERSION   postmaster.pid  
> pg\_hba.conf  pg\_notify      pg\_subtrans   pg\_xlog  

The command to then start the postgres daemon is:

`[rmb@rmb-tower cat]$ pwd`

> /skycam/SkyMine/cat

`[rmb@rmb-tower cat]$ postgres -D apass/`

### accessing a remotely hosted copy

Remote access must be allowed from the postgres configs.

* edit postgresql.conf and add '*' to listen_addresses, unless you have a 
specific IP you want to listen for, in which case use that. This file also
contains information on the port used.

* to allow a user access, edit pg_hba.conf and add a line like:

> host	all	rmb	{IP}	{GATEWAY}	trust

## USNOB

The USNOB catalogue is currently stored as a series of directories. A binary 
file, "query_usnob", must be compiled in order to use this catalogue for 
source cross-matching. 

The catalogue can either be held locally or be hosted over some 
file-sharing protocol e.g. NFS. The directory structure should exactly 
match:

`[rmb@rmb-tower usnob]$ pwd`

> /skycam/SkyMine/cat/usnob

`[rmb@rmb-tower usnob]$ ls`

> 000  012  024  036  048  060  072  084  096  108  120  132  144  156  168  
> 001  013  025  037  049  061  073  085  097  109  121  133  145  157  169  
> 002  014  026  038  050  062  074  086  098  110  122  134  146  158  170  
> 003  015  027  039  051  063  075  087  099  111  123  135  147  159  171  
> 004  016  028  040  052  064  076  088  100  112  124  136  148  160  172  
> 005  017  029  041  053  065  077  089  101  113  125  137  149  161  173  
> 006  018  030  042  054  066  078  090  102  114  126  138  150  162  174  
> 007  019  031  043  055  067  079  091  103  115  127  139  151  163  175  
> 008  020  032  044  056  068  080  092  104  116  128  140  152  164  176  
> 009  021  033  045  057  069  081  093  105  117  129  141  153  165  177  
> 010  022  034  046  058  070  082  094  106  118  130  142  154  166  178  
> 011  023  035  047  059  071  083  095  107  119  131  143  155  167  179  

