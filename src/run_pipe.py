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

from process import process
from util import read_ini

if __name__ == "__main__":
    parser = optparse.OptionParser()
    group1 = optparse.OptionGroup(parser, "General options")
    group1.add_option('--pi', action='store', default='../etc/pipe/pipeline.ini.rmb-tower', type=str, dest='pipeCfgPath', help='path to pipeline config file')
    group1.add_option('--from', action='store', default='2013-06-10 23:45:00', dest='dateFrom', help='ASYNC ONLY - process images from date (YYYY-MM-DD HH:MM:SS)')
    group1.add_option('--to', action='store', default='2013-06-10 23:59:00', dest='dateTo', help='ASYNC ONLY - process images to date (YYYY-MM-DD HH:MM:SS)')
    group1.add_option('--i', action='store', default='SkyCamZ', dest='instrument', help='instrument (SkyCamT|SkyCamZ)')
    group1.add_option('--log', action='store', default='INFO', dest='logLevel', help='logging level (DEBUG|INFO|WARNING|ERROR|CRITICAL)')
    group1.add_option('--o', action='store_true', dest='clobber', help='overwrite res folder?')
    group1.add_option('--s', action='store_true', dest='skipArchive', help='skip archive search and use mock data')
    group1.add_option('--pl', action='store_true', dest='makePlots', help='make plots')
    group1.add_option('--d', action='store_true', dest='daemon', help='run daemon')
    parser.add_option_group(group1)

    group2 = optparse.OptionGroup(parser, "Postgres database options")
    group2.add_option('--sdb', action='store_true', dest='storeToDB', help='store to db?')
    parser.add_option_group(group2)

    options, args = parser.parse_args()
    params = {
        'pipeCfgPath' : str(options.pipeCfgPath), 
        'dateFrom' : str(options.dateFrom), 
        'dateTo' : str(options.dateTo), 
        'instrument' : str(options.instrument), 
        'logLevel' : str(options.logLevel),
        'clobber'  : bool(options.clobber),
        'skipArchive'  : bool(options.skipArchive),
        'makePlots'  : bool(options.makePlots),
        'daemon' : bool(options.daemon),
        'storeToDB' : bool(options.storeToDB)
    } 

    # ------------------------
    # ---- set up logging ----
    # ------------------------ 

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

    # -------------------------------
    # ---- read pipeline configs ----
    # ------------------------------- 

    # parse config file
    pipe_cfg = read_ini(params['pipeCfgPath'])  

    # establish which header we'll be using to populate instrument parameters
    if params['instrument'] == 'SkyCamT':
        inst_cfg_header = "skycamt_params"
    elif params['instrument'] == 'SkyCamZ':
        inst_cfg_header = "skycamz_params"

    # add to params dict
    try:
        params['rootPath']                      = str(pipe_cfg['paths']['path_root_skymine'].rstrip("/") + "/") 
        params['resRootPath']                   = str(pipe_cfg['paths']['path_root_res'].rstrip("/") + "/") 
        params['path_pw_list']                  = str(pipe_cfg['paths']['path_pw_list'])
        params['cat']                           = [c.upper() for c in str(pipe_cfg['general']['xmatch_cat']).split(',')]
        params['processes']                     = int(pipe_cfg['general']['max_processes'])
        params['obs_day_start']                 = str(pipe_cfg['general']['obs_day_start'])
        params['obs_day_end']                   = str(pipe_cfg['general']['obs_day_end'])
        params['t_sync_check']                  = float(pipe_cfg['general']['t_sync_check'])   
        params['archive_credentials_id']        = str(pipe_cfg['lt_archive']['pw_file_entry_id'])
        params['catalogue_credentials_id']      = str(pipe_cfg['catalogue']['pw_file_entry_id'])
        params['skycam_cat_db_credentials_id']  = str(pipe_cfg['catalogue']['pw_file_entry_id'])
        params['skycam_lup_db_credentials_id']  = str(pipe_cfg['skycam_lookup']['pw_file_entry_id'])
        # inst specific keys
        params['pointingDiffThresh']            = float(pipe_cfg[inst_cfg_header]['pointing_diff_thresh'])
        params['sExConfFile']                   = str(pipe_cfg[inst_cfg_header]['sex_conf_file'])
        params['minSources']                    = int(pipe_cfg[inst_cfg_header]['min_sources'])
        params['maxElongation']                 = float(pipe_cfg[inst_cfg_header]['max_elongation'])
        params['maxExKurtosis']                 = float(pipe_cfg[inst_cfg_header]['max_ex_kurtosis'])
        params['maxCombExKurtosis']             = float(pipe_cfg[inst_cfg_header]['max_comb_ex_kurtosis'])
        params['maxCombElongation']             = float(pipe_cfg[inst_cfg_header]['max_comb_elongation'])
        params['maxSourcesCombCheck']           = int(pipe_cfg[inst_cfg_header]['max_sources_comb_check'])
        params['maxFlux']                       = float(pipe_cfg[inst_cfg_header]['max_flux'])
        params['fieldMargin']                   = int(pipe_cfg[inst_cfg_header]['field_margin'])
        params['CCDSizeX']                      = int(pipe_cfg[inst_cfg_header]['ccd_size_x'])
        params['CCDSizeY']                      = int(pipe_cfg[inst_cfg_header]['ccd_size_y'])
        params['matchingTolerance']             = float(pipe_cfg[inst_cfg_header]['matching_tolerance'])
        params['upperColourLimit']              = float(pipe_cfg[inst_cfg_header]['upper_colour_limit'])
        params['lowerColourLimit']              = float(pipe_cfg[inst_cfg_header]['lower_colour_limit'])
        params['limitingMag']                   = float(pipe_cfg[inst_cfg_header]['limiting_mag'])
        params['fieldSize']                     = float(pipe_cfg[inst_cfg_header]['field_size'])
        params['schemaName']                    = str(pipe_cfg[inst_cfg_header]['schema_name'])
        params['minNumMatchedSources']          = int(pipe_cfg[inst_cfg_header]['min_num_matched_sources'])
        params['maxNumSourcesXMatch']           = int(pipe_cfg[inst_cfg_header]['max_num_sources_xmatch'])
        params['forceCatalogueQuery']           = bool(int(pipe_cfg[inst_cfg_header]['force_cat_query']))     
    except KeyError, e:
        logger.info("[run_pipe.go] Key/section " + str(e) + " appears to be missing.")
        exit(0) 

    # add pipeline subdirectory locations according to root
    params['binPath'] = params['rootPath'] + 'bin/'
    params['srcPath'] = params['rootPath'] + 'src/'
    params['etcPath'] = params['rootPath'] + 'etc/'
    params['tmpPath'] = params['rootPath'] + 'tmp/'
    
    params['tmpMockPath']   = params['tmpPath'] + 'mock/'

    # some input sanity checks
    try:
        assert params['instrument'] == 'SkyCamZ' or params['instrument'] == 'SkyCamT' 
    except AssertionError: 
        logger.critical("(__main__) instrument is invalid.")
        exit(0)
    try:
        for c in params['cat']:
            assert c in ['USNOB', 'APASS', 'SKYCAM']
    except AssertionError: 
        logger.critical("(__main__) unknown reference catalogue.")
        exit(0)
        
    # ----------------------------
    # RUN PIPELINE ASYNCHRONOUSLY.
    # ----------------------------
    if not params['daemon']:
        # start process timer
        startProcessTime = time.time()

        # ----------------------------------------------------------------------------------------------------------------
        # The following section adds some degree of parallelism to the process by constructing separate process calls
        # with independent dateFrom, dateTo and resPath parameters, otherwise the entire batch will only ever run 
        # on a single core (because of python's GIL)
        #
        # This works by creating a worker pool and farming off subprocesses to call pipe.py. Because pipe.py is called as
        # an external program rather than a class, it requires the input parameters passed through. This is done by 
        # serialising the input provided to this program as JSON. 
        # 
        # Note that using too many cores may move the bottleneck to memory, and thus increase disk I/O as swapping occurs.
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
            startObsDayDatetime = datetime.combine((datetimeFrom.date() + td(days=i))-td(days=1), datetime.strptime(params['obs_day_start'], "%H:%M:%S").time())
            endObsDayDatetime 	= datetime.combine((datetimeFrom.date() + td(days=i)), datetime.strptime(params['obs_day_end'], "%H:%M:%S").time())

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
            params_copy['dateFrom']     = start.strftime("%Y-%m-%d %H:%M:%S")
            params_copy['dateTo']       = end.strftime("%Y-%m-%d %H:%M:%S")
            params_copy['resPath']      = params['resRootPath'] + obsDate.strftime("%Y%m%d") + '/'

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

    # -------------------------
    # RUN PIPELINE AS A DAEMON.
    # -------------------------
    else:
        # add resPath
        params['resPath'] = params['resRootPath'] + "service" + '/'

        sync_p = process(json.dumps(params))
        sync_p.run_sync()
        

