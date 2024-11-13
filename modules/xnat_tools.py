import os
import io
import xnat
import random
import string
import pandas as pd
import shutil


from models.db import XnatScan

class xnat_tools(object):

    def __init__(self, xnat_server, xnat_user, xnat_password):
        
        self.xnat_session = xnat.connect(server=xnat_server, user=xnat_user, password=xnat_password,
                                         default_timeout=3600)

    # ----------------------------
    # xnat server functions
    # ----------------------------
    
    #https://xnat.readthedocs.io/en/latest/static/tutorial.html#low-level-rest-directives

    def get_xnat_element(self, project_id=None, subject_id=None, experiment_id=None, scan_id=None):
        if project_id is not None:
            if subject_id is not None:
                if experiment_id is not None:
                    if scan_id is not None:
                        return self.xnat_session.projects[project_id].subjects[subject_id].experiments[experiment_id].scans[scan_id]
                    return self.xnat_session.projects[project_id].subjects[subject_id].experiments[experiment_id]
                return self.xnat_session.projects[project_id].subjects[subject_id]
            return self.xnat_session.projects[project_id]

    def get_xnat_scan_list(self, project_id, subject_id=None, experiment_id=None):
        xnat_list = []
        project = self.get_xnat_element(project_id)
        for subject in project.subjects.values():
            if subject_id is None or subject.id == subject_id:
                for experiment in subject.experiments.values():
                    if experiment_id is None or experiment.id == experiment_id:
                        for scan in experiment.scans.values():
                            info = {
                                'project_id': project.id,
                                'project_name': project.name,
                                'subject_id': subject.id,
                                'subject_label': subject.label,
                                'experiment_id': experiment.id,
                                'experiment_label': experiment.label,
                                'scan_id': scan.id,
                                'scan_modality': scan.modality,
                                'scan_type': scan.type,
                            }
                            xnat_list.append(info)
        return xnat_list

    def set_scan_json_resource(self, args, log, scan, json_text, json_name):
        
        random_string = ''.join(random.choices(string.ascii_letters, k=10))
        temp_dir_path = os.path.join(args['data_path'], "temp", random_string)
        temp_file_path = os.path.join(temp_dir_path, f'{random_string}.json')

        os.makedirs(temp_dir_path, exist_ok=True)
        
        with open(temp_file_path, 'w') as file:
            file.write(json_text)
 
        if 'QC' in scan.resources:
            resource = scan.resources['QC']
        else:
            try:
                scan.xnat_session.classes.ResourceCatalog(parent=scan, label='QC')
            except:
                log.info('Bypassing create_resource error')
            resource = scan.resources['QC']
  
        resource.upload(temp_file_path, f'{json_name}.json', overwrite=True)
        
        if os.path.exists(temp_dir_path):
            shutil.rmtree(temp_dir_path)

        # Upload as custom attribute (fails, attrs not)
        #scan.attrs.set(f'xnat:scanData/{json_name}', json_text)



    # ----------------------------
    # index scans
    # ----------------------------
    # retrieves scans from XNAT and compares to db and inserts the difference
    # ----------------------------

    def index_scans(self, args, log, dbtools):

        for project in args.xnat_projects:
            log.info(f'Indexing {project}')        

            xnat_df = pd.DataFrame(self.get_xnat_scan_list(project))

            db_df = dbtools.get_db_scan_list(df=True, project=project)
            db_df.set_index('xnat_scan_id', drop=True, inplace=True)

            merged = pd.merge(xnat_df, db_df, how='outer', indicator=True)
            new_records = merged[merged['_merge'] == 'left_only']

            scan_inserts = []
            for index, row in new_records.iterrows():
                new_scan = XnatScan(
                    project_id = row.project_id,
                    project_name = row.project_name,
                    subject_id = row.subject_id,
                    subject_label = row.subject_label,
                    experiment_id = row.experiment_id,
                    experiment_label = row.experiment_label,
                    scan_id = row.scan_id,
                    scan_modality = row.scan_modality,
                    scan_type = row.scan_type,
                )
                scan_inserts.append(new_scan)

            dbtools.insert_list(scan_inserts)




