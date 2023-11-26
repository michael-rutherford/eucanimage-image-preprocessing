import xnat
import pandas as pd

from models.xnat_db import xnat_db
from models.xnat_db import XnatScan

class xnat_tools(object):

    def __init__(self, db_connect_string, xnat_server, xnat_user, xnat_password):
        
        self.xnat_db = xnat_db(db_connect_string)
        self.xnat_db.create_database(True)
        self.db_session = self.xnat_db.get_session()

        self.xnat_session = xnat.connect(server=xnat_server, user=xnat_user, password=xnat_password)

    # ----------------------------
    # database functions
    # ----------------------------

    def reset_database(self):
        self.drop_table('xnat_scan')
        self.create_database(True)
        return None

    def create_database(self, check):
        self.xnat_db.create_database(check)
        return None

    def clear_database(self, check):
        self.xnat_db.clear_database(check)
        return None

    def flush_database(self):
        try:
            self.db_session.flush()
        except:
            self.db_session.rollback()
            raise
        else:
            self.db_session.commit()
        return None

    def drop_table(self, table):
        self.xnat_db.drop_table(table)
        return None

    def clear_table(self, table):
        self.xnat_db.clear_table(table)
        return None

    def insert_list(self, insert_list):
        self.xnat_db.insert_list(self.db_session, insert_list)
        return None

    def insert_dataframe(self, table, insert_df):
        self.xnat_db.insert_dataframe(self.db_session, table, insert_df)
        return None

    # Get scan list (from database)
    def get_db_scan_list(self, df, project=None, subject=None, experiment=None, scan=None):
        clause = 'where'
        project_string = f"{clause} project_id = '{project}'" if project else ""
        if project_string:
            clause = 'and'
        subject_string = f"{clause} subject_id = '{subject}'" if subject else ""
        if subject_string:
            clause = 'and'
        experiment_string = f"{clause} experiment_id = '{experiment}'" if experiment else ""
        if experiment_string:
            clause = 'and'
        scan_string = f"{clause} scan_id = '{scan}'" if scan else ""
        
        query = f"select * from xnat_scan {project_string} {subject_string} {experiment_string} {scan_string}"
        scans = self.xnat_db.query(session=self.db_session, table=XnatScan, query_text=query, return_df=df)

        return scans

    # ----------------------------
    # xnat server functions
    # ----------------------------
    
    #https://xnat.readthedocs.io/en/latest/static/tutorial.html#low-level-rest-directives

    def get_xnat_element(self, project=None, subject=None, experiment=None, scan=None):
        if project is not None:
            if subject is not None:
                if experiment is not None:
                    if scan is not None:
                        return self.xnat_session.projects[project].subjects[subject].experiments[experiment].scans[scan]
                    return self.xnat_session.projects[project].subjects[subject].experiments[experiment]
                return self.xnat_session.projects[project].subjects[subject]
            return self.xnat_session.projects[project]

    # Get scan list (from xnat)
    def get_xnat_scan_list(self, xnat_project, xnat_subject=None, xnat_experiment=None):

        xnat_list = []

        project = self.get_xnat_element(xnat_project)
        #print(f'Indexing Project: {project.name}')

        for subject in project.subjects.values():
            if xnat_subject is None or subject.id == xnat_subject:
                #print(f'  Indexing Subject: {subject.label}')

                for experiment in subject.experiments.values():
                    if xnat_experiment is None or experiment.id == xnat_experiment:
                        #print(f'    Indexing Experiment: {experiment.label}')
                    
                        for scan in experiment.scans.values():
                            #print(f'      Indexing Scan: {scan.id}')

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

    
    # ----------------------------
    # index scans
    # ----------------------------
    # retrieves scans from XNAT and compares to db and inserts the difference
    # ----------------------------

    def index_project_scans(self, xnat_project):

        xnat_df = pd.DataFrame(self.get_xnat_scan_list(xnat_project))

        db_df = self.get_db_scan_list(df=True, project=xnat_project)
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

        self.insert_list(scan_inserts)




