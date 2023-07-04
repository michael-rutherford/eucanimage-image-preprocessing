import os
import logging

class log_helper(object):

    def __init__(self, start_time, prog_name, log_path, log_level):

        self.start_time = start_time
        self.prog_name = prog_name
        self.log_path = log_path
        self.log_level = log_level

        # If not exists, create
        if not os.path.exists(log_path):
            os.makedirs(log_path)

        str_date = start_time.strftime("%Y%m%d%H%M%S")
        self.log_file = os.path.join(log_path, f'{str_date}-{prog_name}-execution.log')

        set_level = logging.INFO
        if log_level == 'debug':
            set_level = logging.DEBUG
        elif log_level == 'info':
            set_level = logging.INFO
        elif log_level == 'warning':
            set_level = logging.WARNING
        elif log_level == 'error':
            set_level = logging.ERROR
        elif log_level == 'critical':
            set_level = logging.CRITICAL

        logging.basicConfig(
            level=set_level,
            format="%(asctime)s - [%(levelname)s] - %(message)s",
            handlers=[
                logging.FileHandler(self.log_file, 'a'),
                logging.StreamHandler()
            ]
        )

    def debug(self, log_text):

        logging.debug(log_text)

    def info(self, log_text):

        logging.info(log_text)

    def warning(self, log_text):

        logging.warning(log_text)

    def error(self, log_text):

        logging.error(log_text)

    def critical(self, log_text):

        logging.critical(log_text)
