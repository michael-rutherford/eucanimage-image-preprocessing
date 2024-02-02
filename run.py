import os
import sys
import json
from datetime import datetime
import multiprocessing

from modules.xnat_tools import xnat_tools
from modules.db_tools import db_tools

from modules.quality_tools import quality_tools
from modules.normalization_tools import normalization_tools

from modules.log_helper import log_helper
from modules.arg_helper import arg_helper

def run_preprocessing(args, log):
    
    log.info(f'Running Preprocessing')

    # --------------------------------------
    # initialize tools
    # --------------------------------------
    log.info(f'Initializing XNAT')
    xtools = xnat_tools(args.xnat_server, args.xnat_user, args.xnat_password)
    log.info(f'Initializing Database')
    dbtools = db_tools(args.db_connect_string)

    # --------------------------------------
    # if index is true, index scans (must run at least once)
    # --------------------------------------
    if args.index == True:
        index_xnat(args, log, xtools, dbtools)
        
    # --------------------------------------
    # run other script functions
    # --------------------------------------
    
    # quality functions
    if "quality_functions" in args.preprocess_functions:
        run_quality_functions(args, log, xtools, dbtools)

    # normalization functions
    if "normalization_functions" in args.preprocess_functions:
        run_normalization_functions(args, log, xtools, dbtools)
    
    return None

def index_xnat(args, log, xtools, dbtools):
    log.info(f'Indexing')
    xtools.index_scans(args, log, dbtools)        
    return None

def run_quality_functions(args, log, xtools, dbtools):
    log.info('Running Quality Functions')
    qtools = quality_tools()
    qtools.run_quality_functions(args, log, xtools, dbtools)  
    return None

def run_normalization_functions(args, log, xtools, dbtools):
    log.info('Running Normalization Functions')
    ntools = normalization_tools()
    ntools.run_normalization_functions(args, log, xtools, dbtools)
    return None


def main(argv):

    # --------------------------------------
    # parse arguments
    # --------------------------------------
    
    args = arg_helper(argv)

    # if no arguments, use default values for dev testing
    if len(argv) == 0:
        set_args = {}
        set_args['config_path'] = r"D:\data\XNAT\prod\config\xnat_remote.json"
        #set_args['config_path'] = r"D:\data\XNAT\sandbox\config\xnat_sandbox.json"
        args.setArgs(set_args)
        
    # --------------------------------------
    # parse config file
    # --------------------------------------

    with open(args.config_path) as json_file:
        data = json.load(json_file)

        args.setArg("data_path", data['data_path'])
        args.setArg("db_path", os.path.join(args.data_path, "db.db"))
        args.setArg("db_connect_string", f'sqlite+pysqlite:///{args.db_path}')
        args.setArg("stage_path", os.path.join(args.data_path, "stage"))
        args.setArg("log_path", os.path.join(args.data_path, "logs"))
        args.setArg("log_level", data['log_level'])

        args.setArg("xnat_server", data['xnat_server'])
        args.setArg("xnat_user", data['xnat_user'])
        args.setArg("xnat_password", data['xnat_password'])
        args.setArg("xnat_projects", data['xnat_projects'])
        args.setArg("xnat_subjects", data['xnat_subjects']) if 'xnat_subjects' in data else None
        args.setArg("xnat_experiments", data['xnat_experiments']) if 'xnat_experiments' in data else None
        args.setArg("xnat_scans", data['xnat_scans']) if 'xnat_scans' in data else None

        args.setArg("preprocess_functions", data['preprocess_functions'])
        args.setArg("index", data['index'])
        args.setArg("reset", data['reset'])

        args.setArg("multi_proc", data['multi_proc'])
        args.setArg("multi_proc_cpu", data['multi_proc_cpu'])
        args.setArg("multi_thread", data['multi_thread'])
        args.setArg("multi_thread_workers", data['multi_thread_workers'])

    # --------------------------------------
    # initialize logging
    # --------------------------------------
    start_time = datetime.now()
    prog_name = "eucanimage_xnat_preprocessor"
    log = log_helper(start_time, prog_name, args.log_path, args.log_level)
    # --------------------------------------

    log.info(f'Executing {prog_name}')

    run_preprocessing(args, log)

    #------------------------------------------
    # calculate duration
    #------------------------------------------
    end_time = datetime.now()
    elapsed_time = end_time - start_time
    seconds_in_day = 24 * 60 * 60
    duration = divmod(elapsed_time.days * seconds_in_day + elapsed_time.seconds, 60)

    log.info(f'Complete - Duration: {duration}')

    
if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", True)
    main(sys.argv[1:])













