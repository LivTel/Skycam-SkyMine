#!/bin/python
'''
name:		run_pipe.py
author:		rmb

description:	A wrapper script for the skycam pipeline.
'''
from multiprocessing import Pool
import subprocess
import optparse
import logging
import os
import json
from datetime import date, datetime, timedelta as td
import time

# GLOBALS
OBS_DAY_START	= ' 17:30:00'
OBS_DAY_END	= ' 09:00:00'

if __name__ == "__main__":
    parser = optparse.OptionParser()
    group1 = optparse.OptionGroup(parser, "General options")
    group1.add_option('--root', action='store', default='/skycam/SkyMine/', type=str, dest='rootPath', help='path to root of skycam directory')
    group1.add_option('--res', action='store', default='/skycam/tmp/', type=str, dest='resRootPath', help='path to root of results directory')
    group1.add_option('--from', action='store', default='2013-06-10 23:45:00', dest='dateFrom', help='query archive for images from date (YYYY-MM-DD HH:MM:SS)')
    group1.add_option('--to', action='store', default='2013-06-10 23:59:00', dest='dateTo', help='query archive for images to date (YYYY-MM-DD HH:MM:SS)')
    group1.add_option('--i', action='store', default='SkyCamZ', dest='instrument', help='instrument (SkyCamT|SkyCamZ)')
    group1.add_option('--log', action='store', default='INFO', dest='logLevel', help='logging level (DEBUG|INFO|WARNING|ERROR|CRITICAL)')
    group1.add_option('--pr', action='store', default=8, type=int, dest='processes', help='maximum number of concurrent processes to spawn')
    group1.add_option('--o', action='store_true', dest='clobber', help='overwrite res folder?')
    group1.add_option('--s', action='store_true', dest='skipArchive', help='skip archive search and use mock data')
    group1.add_option('--cat', action='store', dest='cat', default='USNOB', help='catalogue to use for matching (USNOB||APASS||BOTH)')
    group1.add_option('--pl', action='store_true', dest='makePlots', help='make plots')
    parser.add_option_group(group1)

    group2 = optparse.OptionGroup(parser, "Postgres database options")
    group2.add_option('--sdb', action='store_true', dest='storeToDB', help='store to db?')
    group2.add_option('--odb', action='store_true', dest='clobberDB', help='overwrite entries with existing filename in db?')
    group2.add_option('--host', action='store', default='localhost', dest='dbHost', help='database hostname')
    group2.add_option('--port', action='store', default='5432', dest='dbPort', help='database port')
    group2.add_option('--u', action='store', default='rmb', dest='dbUser', help='database username')
    group2.add_option('--p', action='store', default='pw', dest='dbPass', help='database password')
    group2.add_option('--name', action='store', default='skycam', dest='dbName', help='database name')
    group2.add_option('--d', action='store_true', dest='destroyMine', help='destroy mine before committing')
    parser.add_option_group(group2)

    options, args = parser.parse_args()
    params = {
        'rootPath' : str(options.rootPath), 
        'resRootPath' : str(options.resRootPath), 
        'dateFrom' : str(options.dateFrom), 
        'dateTo' : str(options.dateTo), 
        'instrument' : str(options.instrument), 
        'logLevel' : str(options.logLevel),
        'processes' : int(options.processes),
        'clobber'  : bool(options.clobber),
        'skipArchive'  : bool(options.skipArchive),
        'cat'  : str(options.cat).upper(),
        'makePlots'  : bool(options.makePlots),
        'storeToDB' : bool(options.storeToDB),   
        'clobberDB' : bool(options.clobberDB), 
        'dbHost' : str(options.dbHost),
        'dbPort' : int(options.dbPort),
        'dbUser' : str(options.dbUser),
        'dbPass' : str(options.dbPass),
        'dbName' : str(options.dbName),
        'destroyMine' : bool(options.destroyMine)
    }

    # set logging
    logger = logging.getLogger('skycam_pipeline_init')
    logger.setLevel(getattr(logging, params['logLevel'].upper()))

    ## console handler
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, params['logLevel'].upper()))

    ## set logging format
    formatter = logging.Formatter("(" + str(os.getpid()) + ") %(asctime)s:%(levelname)s: %(message)s")
    ch.setFormatter(formatter)

    ## add handlers to logging object
    logger.addHandler(ch)

    # some input sanity checks
    if params['cat'] == 'APASS':
        logger.critical("(__main__) catalogue not supported yet")
        exit(0)
    try:
        assert params['instrument'] == 'SkyCamZ' or params['instrument'] == 'SkyCamT' 
        assert params['cat'] == 'USNOB' or params['cat'] == 'APASS'
    except AssertionError: 
        logger.critical("(__main__) input sanity check failed")
        exit(0)

    # start process timer
    startProcessTime = time.time()

    # add pipeline specific directory locations according to root
    params['binPath'] = params['rootPath'] + 'bin/'
    params['srcPath'] = params['rootPath'] + 'src/'
    params['etcPath'] = params['rootPath'] + 'etc/'
    params['tmpPath'] = params['rootPath'] + 'tmp/'

    params['tmpMockPath'] = params['tmpPath'] + 'mock/'
    params['catUSNOBPath'] = params['rootPath'] + 'cat/usnob/'

    # unpack pipeline parameters file and append parameters into params dict
    if params['instrument'] == 'SkyCamT':
        paramsFilePath = params['etcPath'] + 'pipe/params_T'
    elif params['instrument'] == 'SkyCamZ':
        paramsFilePath = params['etcPath'] + 'pipe/params_Z'

    with open(paramsFilePath) as f:
        for line in f:
            if '#' not in line:
                key, val = line.rstrip('\n').split() 
                params[key] = val

    # ----------------------------------------------------------------------------------------------------------------
    # This is a bit of a bodge to add some degree of parallelism to the process by constructing separate process calls
    # with independent dateFrom, dateTo and resPath parameters, otherwise the entire batch will only ever run 
    # on a single core (because of python's GIL)
    #
    # This works by creating a worker pool and farming off subprocesses to call pipe.py. Because pipe.py is called as
    # an external program, rather than a class, it requires the input parameters passed through. This is done by 
    # serialising the input provided to this program as JSON. 
    # 
    # Using too many cores may move the bottleneck to memory, and thus disk I/O as swapping occurs.
    # ----------------------------------------------------------------------------------------------------------------
    #
    # SEPARATE INPUT BY OBSERVATIONAL DAY
    ## parse requested dates into datetime objects
    dateFrom, timeFrom = params['dateFrom'].split()
    dateTo, timeTo = params['dateTo'].split()

    dateFrom_year, dateFrom_mon, dateFrom_day = dateFrom.split('-')
    timeFrom_hour, timeFrom_min, timeFrom_sec = timeFrom.split(':')
    dateTo_year, dateTo_mon, dateTo_day = dateTo.split('-')
    timeTo_hour, timeTo_min, timeTo_sec = timeTo.split(':')

    datetimeFrom = datetime(int(dateFrom_year), int(dateFrom_mon), int(dateFrom_day), int(timeFrom_hour), int(timeFrom_min), int(timeFrom_sec))
    datetimeTo = datetime(int(dateTo_year), int(dateTo_mon), int(dateTo_day), int(timeTo_hour), int(timeTo_min), int(timeTo_sec))
 
    ## get a list of day-separated parameter dicts (with independent dateFrom, dateTo and resPath parameters)
    params_list = []
    dateDelta = datetimeTo.date() - datetimeFrom.date()
    for i in range(dateDelta.days + 2):	# + 2 to account for possibility that end datetime runs into a new "observational" day
        ### create datetime object corresponding to the times for this observational" day. n.b. runs from day-1 to day.
	startObsDayDatetime 	= datetime.combine((datetimeFrom.date() + td(days=i))-td(days=1), datetime.strptime(OBS_DAY_START, " %H:%M:%S").time())
        endObsDayDatetime 	= datetime.combine((datetimeFrom.date() + td(days=i)), datetime.strptime(OBS_DAY_END, " %H:%M:%S").time())

        ### make sure that the boundaries of the requested start/end datetimes lie within the current observational day
        if datetimeFrom > endObsDayDatetime or datetimeTo < startObsDayDatetime:
            continue
	
        ### establish if start/end dates are in current observational day
        fromInObsDay = True if datetimeFrom > startObsDayDatetime and datetimeFrom < endObsDayDatetime else False
        toInObsDay = True if datetimeTo > startObsDayDatetime and datetimeTo < endObsDayDatetime else False

        ### and construct start/end/obsdate appropriately
        start = datetimeFrom if fromInObsDay is True else startObsDayDatetime
        end = datetimeTo if toInObsDay is True else endObsDayDatetime  
        obsDate = startObsDayDatetime.date()

        ### copy params as-they-were to newParams dict
        params_copy = dict(params)

        ### replace the necessary keys with their updated values
        params_copy['dateFrom'] = start.strftime("%Y-%m-%d %H:%M:%S")
        params_copy['dateTo'] = end.strftime("%Y-%m-%d %H:%M:%S")
        params_copy['resPath'] = params['resRootPath'] + obsDate.strftime("%Y%m%d") + '/'

        ### add this dict to newParams list
        params_list.append(params_copy)

    ## farm off subprocesses to worker pool
    workers = Pool(processes=params['processes'])
    for i in params_list:
        ### serialise this params input to pass to pipe.py on command line
        params_json = json.dumps(i)
        res = workers.apply_async(subprocess.call, [["python", params['srcPath'] + "process.py", params_json]]) # no worker callback called when complete
 
    ## rejoin this main thread upon completion
    workers.close()
    workers.join()

    elapsed = (time.time() - startProcessTime)
    logger.info("(__main__) parent process finished in " + str(round(elapsed)) + "s")
