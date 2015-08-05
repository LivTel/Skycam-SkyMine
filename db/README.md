db/
=============

This is where the Skycam postgresql database is normally kept if it 
is to be hosted locally. Like the APASS database, it does not need to 
be. You will need to change your host/ip/user/pw details for the 
"skycam" entry in the etc/pipe/PW_LIST file accordingly.

### hosting your own local copy

Assuming you have access to a copy of the database, ensure you have a 
directory structure like, e.g.

`[rmb@rmb-tower skycam]$ pwd`

> /skycam/SkyMine/db/skycam

`[rmb@rmb-tower skycam]$ ls`

> base         pg\_ident.conf  pg\_serial     pg\_tblspc    postgresql.conf  
> global       pg\_log         pg\_snapshots  pg\_twophase  postmaster.opts  
> pg\_clog      pg\_multixact   pg\_stat_tmp   PG\_VERSION   postmaster.pid  
> pg\_hba.conf  pg\_notify      pg\_subtrans   pg\_xlog  

The command to then start the postgres daemon (running on port 5433) is:

`[rmb@rmb-tower db]$ pwd`

> /skycam/SkyMine/db

`[rmb@rmb-tower db]$ postgres -p 5433 -D skycam/`

You will need to make sure to specify a port number if you're already 
running a postgres database for APASS on the default port (5432).

### accessing a remotely hosted copy

Remote access must be allowed from the postgres configs.

* edit postgresql.conf and add '*' to listen_addresses, unless you have a 
specific IP you want to listen for, in which case use that. This file also
contains information on the port used.

* to allow a user access, edit pg_hba.conf and add a line like:

> host  all     rmb     {IP}    {GATEWAY}       trust


