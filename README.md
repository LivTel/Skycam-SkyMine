Skycam-Skymine
=============

# Overview

Skycam-Skymine provides a facility to extract and cross-match sources from the Liverpool Telescope's 
Skycam[TZ?] frames. The resulting information can then be (optionally) stored to a Postgres backend. The 
pipeline is based off the work done by [Mawson et al.](http://adsabs.harvard.edu/cgi-bin/bib_query?arXiv:1305.0573)

Some of the most notable changes include:

* Migration of codebase from CSH to Python2
* Use of multithreading to allow processing of several days simultaneously
* Addition of APASSdr9 to available cross matching catalogues
* Migration from MySQL database backend to Postgres9.5
* Daemon mode to process files in real-time (work in progress)

# Getting Started

You will first need to edit the system specific information in various locations: 

* the pipeline config file ([**paths**], [**skycamt\_params**.**sex\_conf\_file**], [**skycamz\_params**.**sex\_conf\_file**])
in *etc/pipe/*
* the sExtractor config files ([**PARAMETERS\_NAME**]) in *etc/sex/*
* the external resources file in *etc/pipe/*. 

The first two of these should be copied and configuration dependent suffixes attached. Just remember to reference the 
correct sExtractor parameter files from the pipeline config, and to call the correct config file at runtime using the 
--pi flag discussed below.

A sample *EXTERNAL\_RESOURCES.sample* file is provided, and must be copied and renamed without the suffix. 
**This file must never be added to the repo** - it contains the passwords in plain text!

You will need to make sure that the catalogue-webservices RESTful services are available.

Cross-matching catalogues are selected through the pipeline.ini file. Generally we use APASS because it has a better colour match to 
the unfiltered Skycam cameras, although default is actually both USNOB and APASS (why not?). Further options are explictly commented 
in the pipeline.ini file.

The pipeline is invoked from the wrapper script `src/run_pipe.py`. It has several python module dependencies. Rather than list them all, it is probably 
more efficient to install them as and when they are called for at runtime (there aren't that many!). Use `sudo pip install` or `sudo easy_install`.

# Invoking Skycam-Skymine

For a description of available runtime options:

`[rmb@rmb-staging src]$ python run_pipe.py --h`

> Usage: run_pipe.py [options]  
>  
> Options:  
>  -h, --help          show this help message and exit  
>  
>  General options:  
>    --pi=PIPECFGPATH  path to pipeline config file  
>    --from=DATEFROM   query archive for images from date (YYYY-MM-DD HH:MM:SS)  
>    --to=DATETO       query archive for images to date (YYYY-MM-DD HH:MM:SS)  
>    --i=INSTRUMENT    instrument (SkyCamT|SkyCamZ)  
>    --log=LOGLEVEL    logging level (DEBUG|INFO|WARNING|ERROR|CRITICAL)  
>    --o               overwrite res folder?  
>    --s               skip archive search and use mock data  
>    --pl              make plots  
>    --d               run daemon  
  
>  Postgres database options:  
>    --sdb             store to db?  

# Known Issues

Daemon mode is largely untested. Use at your own risk.

There is currently no facility to overwrite data. This is to maintain consistency between the catalogue and sources tables. Consider this: 
once a record has been updated in the catalogue table, how are you to distinguish its previous state? Would need to keep track of exactly what 
commands were issued to the database in order that these can be reversed after the fact.

