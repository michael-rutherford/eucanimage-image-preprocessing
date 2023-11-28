from models.db import db
from models.db import XnatScan

class db_tools(object):

    def __init__(self, db_connect_string):
        
        self.db = db(db_connect_string)
        self.db.create_database(True)
        self.db_session = self.db.get_session()

    # ----------------------------
    # database functions
    # ----------------------------

    def reset_database(self):
        self.drop_table('xnat_scan')
        self.create_database(True)
        return None

    def create_database(self, check):
        self.db.create_database(check)
        return None

    def clear_database(self, check):
        self.db.clear_database(check)
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
        self.db.drop_table(table)
        return None

    def clear_table(self, table):
        self.db.clear_table(table)
        return None

    def insert_list(self, insert_list):
        self.db.insert_list(self.db_session, insert_list)
        return None

    def insert_dataframe(self, table, insert_df):
        self.db.insert_dataframe(self.db_session, table, insert_df)
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
        scans = self.db.query(session=self.db_session, table=XnatScan, query_text=query, return_df=df)

        return scans