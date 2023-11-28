import os
import argparse

class arg_helper(object):

    def __init__(self, argv):

        self.__parser = argparse.ArgumentParser(description=(""))

        self.parseArgs()

    def parseArgs(self):        

        self.__parser.add_argument("-config_path", "--config_path")
        self.__parser.add_argument("-data_path", "--data_path")
        self.__parser.add_argument("-log_level", "--log_level")
        
        self._args = vars(self.__parser.parse_args())

    def setArgs(self, args):

        self._args = args

    def setArg(self, arg, value):

        self._args[arg] = value

    def getArgs(self):
        return self._args

    #---------------------------------------    
    # Properties
    #---------------------------------------  

    @property    
    def config_path(self):
        return self._args['config_path']

    @property    
    def data_path(self):
        return self._args['data_path']

    @property    
    def db_path(self):
        #db_path = os.path.join(self._args['data_path'], "db.db")
        #return db_path
        return self._args['db_path']

    @property    
    def db_connect_string(self):
        #db_connect_string = f'sqlite+pysqlite:///{self.db_path}'
        #return db_connect_string
        return self._args['db_connect_string']

    @property    
    def stage_path(self):
        #stage_path = os.path.join(self._args['data_path'], "stage")
        #return stage_path
        return self._args['stage_path']

    @property    
    def log_path(self):
        #log_path = os.path.join(self._args['data_path'], "logs")
        #return log_path
        return self._args['log_path']

    @property    
    def log_level(self):
        return self._args['log_level']

    @property    
    def xnat_server(self):
        return self._args['xnat_server']

    @property    
    def xnat_user(self):
        return self._args['xnat_user']

    @property    
    def xnat_password(self):
        return self._args['xnat_password']

    @property    
    def xnat_projects(self):
        return self._args['xnat_projects']

    @property    
    def xnat_subjects(self):
        return self._args['xnat_subjects']

    @property    
    def xnat_experiments(self):
        return self._args['xnat_experiments']

    @property    
    def xnat_scans(self):
        return self._args['xnat_scans']

    @property    
    def preprocess_functions(self):
        return self._args['preprocess_functions']

    @property    
    def index(self):
        return self._args['index']

    @property    
    def reset(self):
        return self._args['reset']

    @property    
    def multi_proc(self):
        return self._args['multi_proc']

    @property    
    def multi_proc_cpu(self):
        return self._args['multi_proc_cpu']

    @property    
    def multi_thread(self):
        return self._args['multi_thread']

    @property    
    def multi_thread_workers(self):
        return self._args['multi_thread_workers']