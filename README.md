SkyMine
=============

This is the repository for the pipeline discussed by 
[Mawson et al.](http://adsabs.harvard.edu/cgi-bin/bib_query?arXiv:1305.0573) 
refactored into Python.

# Installing

You will first need to edit the system specific information (paths etc.) 
in etc/pipe/pipeline.ini, etc/pipe/EXTERNAL_RESOURCES and etc/sex/params/*.sex files 
accordingly. 

You will need to make sure that the catalogue-webservices RESTful services 
are available.

Catalogues are selected through the pipeline.ini file in etc/pipe/. 
Generally, we use the APASS database which has a better colour match to 
the unfiltered Skycam cameras. 

The pipeline is invoked from the wrapper script src/run_pipe.py. 

# Running the pipeline

For a description of available runtime options:

`[rmb@rmb-tower src]$ python run_pipe.py --h`

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
>    --odb             overwrite entries with existing filename in db?  

