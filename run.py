import os
import sys
import json
from datetime import datetime
import multiprocessing

from modules.xnat_tools import xnat_tools
from modules.quality_tools import quality_tools
from modules.log_helper import log_helper
from modules.arg_helper import arg_helper

def initiate_preprocessing(args, log):
    
    log.info(f'Initiating Preprocessing')

    # --------------------------------------
    # initialize xnat and index scans
    # --------------------------------------

    xtools = xnat_tools(args.db_connect_string, args.xnat_server, args.xnat_user, args.xnat_password)

    # --------------------------------------
    # --------------------------------------
    # TODO: attempt to filter by project, subject, 
    # and experiment from config file. Needed? for testing?
    # --------------------------------------
    # --------------------------------------
    # --------------------------------------
    #has_projects = args.xnat_projects != None and len(args.xnat_projects) > 0
    #has_subjects = args.xnat_subjects != None and len(args.xnat_subjects) > 0
    #has_experiments = args.xnat_experiments != None and len(args.xnat_experiments) > 0

    #def index_scans(project, subject, experiment):
    #    if has_projects == True:
    #        if has_subjects == True:
    #            if has_experiments == True:
    #                return xtools.index_scans(project, subject, experiment)
    #            return xtools.index_scans(project, subject)
    #        return xtools.index_scans(project)

    #    for project in projects:
    #        for subject in subjects:
    #            for experiment in experiments:
    #                xtools.index_scans(project, subject, experiment)
    # --------------------------------------
    # --------------------------------------
    # --------------------------------------

    # --------------------------------------
    # if index is true, index scans 
    # --------------------------------------
    if args.index == True:
        for project in args.xnat_projects:
            log.info(f'Indexing {project}')
            xtools.index_project_scans(project)
        
    # --------------------------------------
    # run other script functions
    # --------------------------------------
    
    # quality functions
    if "quality_functions" in args.preprocess_functions:
        log.info('Initializing Quality Tools')
        qtools = quality_tools()

        process_scan_list = []

        for project in args.xnat_projects:
            if not args.xnat_subjects:
                process_scan_list.extend(xtools.get_db_scan_list(df=False, project=project))
            else:
                for subject in args.xnat_subjects:
                    if not args.xnat_experiments:
                        process_scan_list.extend(xtools.get_db_scan_list(df=False, project=project, subject=subject))
                    else:
                        for experiment in args.xnat_experiments:
                            process_scan_list.extend(xtools.get_db_scan_list(df=False, project=project, subject=subject, experiment=experiment))
                    

        qtools.preprocess_project(args.getArgs(), process_scan_list, log)

    # other functions

    # !!!!!!!!!!!!!!!!!!!!!
    # ADD OTHER TOOLKIT FUNCTIONS HERE
    # !!!!!!!!!!!!!!!!!!!!!
    
    return None


def main(argv):

    # --------------------------------------
    # parse arguments
    # --------------------------------------
    
    args = arg_helper(argv)

    # if no arguments, use default values for dev testing
    if len(argv) == 0:
        set_args = {}
        #set_args['config_path'] = r"D:\Data03\XNAT\config\xnat_remote.json"
        #set_args['config_path'] = r"D:\Data03\XNAT\config\xnat_local.json"
        set_args['config_path'] = r"D:\Data03\XNAT\config\xnat_sandbox.json"
        args.setArgs(set_args)
        
    # --------------------------------------
    # parse config file
    # --------------------------------------

    with open(args.config_path) as json_file:
        data = json.load(json_file)

        args.setArg("data_path", data['data_path'])
        args.setArg("db_path", os.path.join(args.data_path, "xnat_db.db"))
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

    initiate_preprocessing(args, log)

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













