import os
import sys
from time import strptime, mktime
import numpy as np

if __name__ == "__main__":
    try:
        root_dir = sys.argv[1]
    except IndexError:
        root_dir = "53907948da66b"

    subquery_times = []
    getData_times = []
    decompressFiles_times = []
    sExtractor_times = []
    crossmatch_times = []
    database_times = []

    if os.path.exists(root_dir + "/log"):
        with open(root_dir + "/log") as f:
            for line in f:
                if "(__main__) parent process finished in" in line:
                    query_time = float(line.split()[8].rstrip('s'))

    for j in os.listdir(root_dir):
        try:
            float(j)
        except ValueError:
            continue
        path_to_log = root_dir + "/" + j + "/res.log"
        if os.path.exists(path_to_log):
            with open(path_to_log) as f: 
 
                getData_startFlag = False
                getData_start = None
                getData_end = None

                decompressFiles_startFlag = False
                decompressFiles_start = None
                decompressFiles_end = None

                sExtractor_startFlag = False
                sExtractor_start = None
                sExtractor_end = None

                crossmatch_startFlag = False
                crossmatch_start = None
                crossmatch_end = None

                database_startFlag = False
                database_start = None
                database_end = None
 
                for line in f:
                    time_seg = line.split()[2]
                    time_seg = time_seg.rstrip(":INFO")
                    time_seg = time_seg.rstrip(":WARNING")
                    this_time = strptime(time_seg, "%H:%M:%S,%f")
                    if "(archive.getData)" in line:
                        if not getData_startFlag:
                            getData_start = this_time
                            getData_startFlag = True
                        getData_end = this_time

                    if "(decompress_files)" in line:
                        if not decompressFiles_startFlag:
                            decompressFiles_start = this_time
                            decompressFiles_startFlag = True
                        decompressFiles_end = this_time
 
                    if "(pipeline._extractSources)" in line:
                        if not sExtractor_startFlag:
                            sExtractor_start = this_time 
                            sExtractor_startFlag = True

                    if "(pipeline._matchSources_USNOB1)" in line:
                        if sExtractor_startFlag:
                            sExtractor_end = this_time 
                            sExtractor_startFlag = False
                        if not crossmatch_startFlag:
                            crossmatch_start = this_time 
                            crossmatch_startFlag = True

                    if "(pipeline._calibrateSources)" in line:
                        if crossmatch_startFlag:
                            crossmatch_end = this_time 
                            crossmatch_startFlag = False
                        if not database_startFlag:
                            database_start = this_time 
                            database_startFlag = True

                    if "(plotCalibration) Made plot" in line:
                        database_end = this_time

                    if "(process.run) child process" in line:
                        subquery_times.append(float(line.split()[8].split("s")[0]))
                            
                getData_delta = mktime(getData_end) - mktime(getData_start)
                decompressFiles_delta = mktime(decompressFiles_end) - mktime(decompressFiles_start)
                sExtractor_delta = mktime(sExtractor_end) - mktime(sExtractor_start)
                crossmatch_delta = mktime(crossmatch_end) - mktime(crossmatch_start)
                database_delta = mktime(database_end) - mktime(database_start)

                getData_times.append(getData_delta)
                decompressFiles_times.append(decompressFiles_delta)
                sExtractor_times.append(sExtractor_delta)
                crossmatch_times.append(crossmatch_delta)
                database_times.append(database_delta)

    print "query:\t\t", query_time
    print "subquery:\t", np.mean(subquery_times), "+/-", np.std(subquery_times), subquery_times
    print "gettingdata:\t", np.mean(getData_times), "+/-", np.std(getData_times), getData_times
    print "decompressing:\t", np.mean(decompressFiles_times), "+/-", np.std(decompressFiles_times), decompressFiles_times
    print "extracting:\t", np.mean(sExtractor_times), "+/-", np.std(sExtractor_times), sExtractor_times
    print "xmatching:\t", np.mean(crossmatch_times), "+/-", np.std(crossmatch_times), crossmatch_times
    print "databasing:\t", np.mean(database_times), "+/-", np.std(database_times), database_times

