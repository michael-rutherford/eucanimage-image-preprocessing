# -*- coding: utf-8 -*-
# ! /usr/bin/env python

#https://docs.sqlalchemy.org/en/14/orm/quickstart.html
#https://docs.sqlalchemy.org/en/14/core/type_basics.html#sql-standard-and-multiple-vendor-types
#https://www.sqlshack.com/introduction-to-sqlalchemy-in-pandas-dataframe/
#https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_introduction.htm#

from sqlalchemy import MetaData, Table, Column, ForeignKey, Index
from sqlalchemy import select, insert, update, delete, text
from sqlalchemy import TEXT, NUMERIC, INTEGER, REAL, BOOLEAN, DATETIME, DATE, TIME, JSON, BLOB

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

import pandas as pd
from datetime import datetime

Base = declarative_base()

class xnat_db(object):

    # Initialize
    def __init__(self, db_connect_string):

        self.engine = create_engine(db_connect_string, echo=False)
        self.session_maker = sessionmaker(bind = self.engine)

        return None

    # Exit
    def __exit__(self):

        self.Session.close()
        self.engine.close()

        return None

    # Create Database
    def create_database(self, check):

        Base.metadata.create_all(self.engine, checkfirst=check)

        return None
    
    # Drop Database
    def drop_database(self, check):

        Base.metadata.drop_all(self.engine, checkfirst=check)

        return None

    # Clear Database
    def clear_database(self, check):

        #Base.metadata.drop_all(self.engine, checkfirst=check)
        metadata = MetaData(bind=self.engine)
        metadata.reflect()
        
        with self.get_session() as session:
            for table in metadata.sorted_tables:
                try:
                    session.execute(table.delete())
                except:
                    session.rollback()
                    raise
                else:
                    session.commit()

        return None

    # Drop Table
    def drop_table(self, table):
        rem_table = Table(table, Base.metadata)
        rem_table.drop(self.engine, checkfirst=True)
        return None

    # Clear Table
    def clear_table(self, table):
        clear_table = Table(table, Base.metadata)
        with self.get_session() as session:
            try:
                session.query(clear_table).delete()
            except:
                session.rollback()
                raise
            else:
                session.commit()

        return None

    # Create Session
    def get_session(self):

        return self.session_maker()

    # Query
    def query(self, session=None, table=None, query_text=None, return_df=False):
        if return_df:
            #query = session.query(text(query_text))
            result_df = pd.read_sql(query_text, session.bind)
            return result_df
        else:
            if session:
                if not query_text == None:
                    result = session.query(table).from_statement(text(query_text)).all()
                else:
                    result = session.query(table).all()
                return result

    # Insert Dataframe
    def insert_dataframe(self, session, table_name, data_df):

        data_dict = data_df.to_dict(orient='records')
        metadata = MetaData(bind=self.engine)
        metadata.reflect()
        table = Table(table_name, metadata, autoload_with=self.engine)

        try:
            session.execute(table.insert(), data_dict)
        except:
            session.rollback()
            raise
        else:
            session.commit()

        return None

    # Insert List of Dictionaries    
    def insert_dicts(self, session, table_name, data_dict):
        
        data_dicts = None
        if isinstance(data_dict, dict):
            data_dicts = [data_dict]
        elif isinstance(data_dict, list):
            data_dicts = data_dict

        # Load the metadata and reflect to get table details
        metadata = MetaData(bind=self.engine)
        metadata.reflect()
        table = Table(table_name, metadata, autoload=True)

        try:
            # Insert data
            session.execute(table.insert(), data_dicts)
        except Exception as e:
            session.rollback()
            raise e
        else:
            session.commit()

        return None

    # Insert List
    def insert_list(self, session, insert_list):

        try:
            session.add_all(insert_list)
        except:
            session.rollback()
            raise
        else:
            session.commit()

        return None

# -------------------
# XNAT Data
# -------------------
class XnatScan(Base):
    __tablename__ = 'xnat_scan'

    xnat_scan_id = Column(INTEGER, primary_key=True, autoincrement=True)
    project_id = Column(TEXT)
    project_name = Column(TEXT)
    subject_id = Column(TEXT)
    subject_label = Column(TEXT)
    experiment_id = Column(TEXT)
    experiment_label = Column(TEXT)
    scan_id = Column(TEXT)
    scan_modality = Column(TEXT)
    scan_type = Column(TEXT)

    # JSON files to be pushed back to XNAT
    scan_quality = Column(TEXT)
    scan_acquisition = Column(TEXT)
    scan_normalization = Column(TEXT)