"""
"""
import logging
from daemonize import Daemonize
import lockfile
import signal
import time
import sys


class Daemon():
    """ """
    def __init__(self, ETLHandler, run_interval_hrs=0.1):
        
        self.pid = '/tmp/mongotosql-daemon.pid'
        self.ETL = ETLHandler
        self.run_interval_sec = self.hours_to_sec(run_interval_hrs)

        logging.basicConfig(
            format='%(asctime)s -- %(levelname)s: %(message)s',
            filename='ETLactivity.log',
            level=logging.DEBUG, 
            datefmt='%m/%d/%Y %I:%M:%S %p'
            )

        self.daemon = Daemonize(
            app='MongoToSqlD-Daemon', 
            pid=self.pid, 
            action=self.start_action,
            foreground=True
            )


    def hours_to_sec(self, t):
        """ convert hours to seconds (sec = hrs x 60min x 60sec) """
        return float(t*3600)


    def start_action(self):
        """ runs the program as a linux daemon or windows service
        """
        while True:
            self.ETL.get_from_mongo()
            self.ETL.push_to_sql()
            self.ETL.send_email_update()

            logging.info(" <daemon> pulled from mongo")
            logging.info(" <daemon> sleeping for {} sec".format(self.run_interval_sec))
            time.sleep(self.run_interval_sec)
            

    def start(self):
        """ """
        self.daemon.start()


    def stop(self):
        """ """
        self.daemon.exit()

        