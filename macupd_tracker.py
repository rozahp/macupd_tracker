#!/usr/bin/env python
##
## Filename:    macupd_tracker.py
##
## Description: Collects and tracks MACudp data from DD-WRT Router
##

import atexit
import os
import SocketServer
from daemon import runner
#import runner
from datetime import datetime
from collections import defaultdict

##
## Import project classes and variables
##
from alerter import Alerter
from globals import *
from handler import Handler
from reporter import Reporter

##====================
##
## MACupdDaemon
##
##====================
class MACupdDaemon():
    """Daemon runner for detaching process from terminal"""

    def __init__(self):
        self.MACLIST, self.CONFIG = self.read_configfile()
        self.logdir = self.CONFIG['logdir']
        self.reportdir = self.CONFIG['reportdir']
        self.host = self.CONFIG['host']
        self.port = int(self.CONFIG['port'])
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stdout_path = self.logdir+"/stdout.log"
        self.stderr_path = '/dev/tty'
        self.stderr_path = self.logdir+"/stderr.log"
        self.pidfile_path = self.CONFIG['pidfile']
        self.pidfile_timeout = 5
        #
        # Error check
        #
        if not os.path.exists(self.logdir):
            print "Err: LOGDIR does not exist - please check system/configfile."
            exit(-1)
        if not os.path.exists(self.reportdir):
            print "Err: REPORTDIR does not exist - please check system/configfile."
            exit(-1)

    ##
    ## Set logfile sizes
    ##
    def set_logfile_sizes(self):
        """Set column sizes for logfiles"""
        #
        # Set column size for largest name in configfile
        #
        LOGFILE_SIZES['name']=max(len(x) for x in self.server.MACLIST.values())+1

    ##
    ## Read Configfile
    ##
    def read_configfile(self):
        """Read Configfile and return dict with CONFIG and MACLIST[mac->name]"""

        #
        # Parse configfile
        #
        filename=CONFIGFILE
        try:
            fp=open(filename,"r")
            if DEBUG: print "Log: reading configurations from:", filename
        except:
            try:
                fp=open('/etc/'+filename,"r")
                if DEBUG: print "Log: reading configurations from:", '/etc/'+filename
            except:
                print "Err: did not find configuration file:", filename
                print "Err: please check documentations."
                exit(-1)
            filename='/etc/'+filename

        CONFIG={}
        MACLIST={}
        for row in fp.readlines():
            #
            # Check For Comments
            #
            if "#" == row[0] or '[' == row[0]: continue

            #
            # CONFIG
            #
            if '=' in row:
                row=row.strip().split()[0].split('=')
                if len(row)!=2:
                    print "Err: bad row in configuration file:", filename, "row:", row
                    exit(-1)
                key=row[0].lower()
                value=row[1]
                if key not in CONFIG_PARTS:
                    print "Err: unknown configuration key in file:", filename, "row:", row
                    exit(-1)

                if key in CONFIG:
                    print "Err: key already set in configuration file:", filename, "row:", row, "last config:", CONFIG[key]
                    exit(-1)
                if len(value)==0:
                    print "Err: value has no length in configuration file:", filename, "row:", row
                CONFIG[key]=value
            #
            # MACLIST
            #
            elif "|" in row:
                row=row.strip().split('|')
                #
                # Error Check
                #
                if len(row)!=len(MACLIST_PARTS):
                    print "Err: error in configfile",filename,"- row:", row
                    exit(-1)
                row_dict={x: row[LOGFILE_HEADER.index(x)] for x in MACLIST_PARTS}
                #
                # Check Config Parts
                #
                if len(row_dict['mac'].split(':'))!=6:
                    print "Err: error in configfile", filename,"- row:", row
                    exit(-1)
                #
                # Fix Bad Name
                #
                row_dict['name']=''.join(row_dict['name'].split())
                MACLIST[row_dict['mac'].lower()]=row_dict['name']
            #
            # Else Error
            #
            else:
                print "Err: bad row in configuration file:", filename, "row:", row
                exit(-1)
        #
        # Close File
        #
        fp.close()
        #
        # Error Check CONFIG
        #
        if all(key in CONFIG for key in CONFIG_PARTS)!=True:
            print "Err: missing key in configuration", filename, "keys:", CONFIG_PARTS
            exit(-1)
        #
        # Add Default Dict
        #
        MACLIST = defaultdict(lambda: DEFAULT_NAME, MACLIST)
        #
        # Return
        #
        return MACLIST, CONFIG

    ##
    ## Check Row
    ##
    def check_row(self, row):
        """Check that rows from logfiles are sane"""
        #
        # Check for comments
        #
        if "#" == row[0]: return False
        row=row.strip().split()
        #
        # Check for headers
        #
        if all(header in row for header in LOGFILE_HEADER): return False
        if len(row)!=len(LOGFILE_HEADER):
                print "Err: error in logfile",filename,"- row:", row
                exit(-1)
        #
        # Get row data
        #
        row_dict={x: row[LOGFILE_HEADER.index(x)] for x in LOGFILE_HEADER}
        #
        # Check key parts
        #
        if len(row_dict['mac'].split(':'))!=6:
            print "Err: error in logfile", filename,"- row:", row
            exit(-1)
        if len(row_dict['ip'].split('.'))!=4:
            print "Err: error in logfile", filename, "- row:", row
            exit(-1)
        #
        # Check active-hours
        #
        if len(list(row_dict['active-hours']))!=24:
            print "Err: error in logfile:", filename, "- row:", row
            exit(-1)
        #
        # Make active-hours to list and digits to integers
        #
        row_dict['active-hours']=list(row_dict['active-hours'])
        for x in [i for i in range(0,len(row_dict['active-hours'])) if row_dict['active-hours'][i].isdigit()]:
            row_dict['active-hours'][x]=int(row_dict['active-hours'][x])

        return row_dict

    ##
    ## Read Status from last logfile (if current date exists)
    ##

    def read_tracker_status(self):
        """Read current tracker status from logfile (if it exists)"""

        filename=self.logdir+"/"+TRACKERFILE_PREFIX+"."+str(self.server.LOG_DATE)+"."+LOGFILE_SUFFIX

        try:
            fp = open(filename,"r")
            print "Log: reading status from current logfile:", filename
            for row in fp.readlines():
                #
                # Check Row
                #
                row_dict=self.check_row(row)
                if row_dict==False: continue
                #
                # Check mac name
                #
                if row_dict['mac'] in self.MACLIST: row_dict['name']=self.MACLIST[row_dict['mac']]
                #
                # Add Row To Dict
                #
                row_key=TRACKER_KEY_DELIM.join(row_dict[x] for x in TRACKER_KEY_PARTS)
                self.server.TRACKER[row_key]=row_dict
            #
            # Close File
            #
            fp.close()
            #
            # Dump Dict
            #
            if DEBUG: self.dump_tracker()

        except Exception, err:
            if DEBUG: print "Log: did not find any logfile for current date:", err

    ##
    ## Set Line Data
    ##

    def set_line(self, keyline):
        """
        Input: dictionary with macupd data from DD-WRT.
        Output: string with data for logfiles.
        """
        line=""
        for key in LOGFILE_HEADER:
            if isinstance(keyline[key], list):
                line+=''.join(str(x) for x in keyline[key])
            else:
                line+='{0:{1}}'.format(keyline[key],LOGFILE_SIZES[key])
        return line
    ##
    ## Get logfiles
    ##
    def get_logfiles(self):
        """Returns a list of logfiles in logdir"""
        logfiles=[]
        for f in os.listdir(self.logdir):
            #
            # Check If logfile
            #
            if "." not in f: continue
            if len(f.split("."))!=3: continue
            if not f.split(".")[1].isdigit(): continue
            if f[-len(LOGFILE_SUFFIX):]!=LOGFILE_SUFFIX: continue

            logfiles.append(f)

        return logfiles


    ##
    ## Rotate logs
    ##
    def rotate_logs(self):
        """Every midnight rotate logs"""
        now=datetime.now()
        maxdays=int(self.server.CONFIG['maxlogs'])
        logfiles=self.get_logfiles()
        for f in logfiles:
            then=datetime.strptime(f.split(".")[1], "%Y%m%d")
            x=now-then
            #
            # Remove logs older then maxdays
            #
            filename=self.logdir + "/" + f
            if x.days>maxdays: os.remove(filename)

    ##
    ## Dump tracker dictionary to logfile
    ##
    def dump_tracker_log(self):
        """Dump current tracker status to logfile"""
        filename=self.logdir+"/"+TRACKERFILE_PREFIX+"."+str(self.server.LOG_DATE)+"."+LOGFILE_SUFFIX
        try:
            with open(filename,"w") as f:
                #
                # Write Header
                #
                if LOGFILE_HEADER:
                    line=""
                    for key in LOGFILE_HEADER:
                        line+='{0:{1}}'.format(key,LOGFILE_SIZES[key])
                    f.write(line)
                    f.write('\n')
                for key in sorted(self.server.TRACKER.keys()):
                    f.write(self.set_line(self.server.TRACKER[key]))
                    f.write('\n')

        except Exception as err:
            print "Err: error while opening file:", err
            exit(-1)
    ##
    ## Dump line to terminal
    ##
    def dump_tracker(self):
        """For debug purposes program will dump tracker status to terminal"""
        for key in sorted(self.server.TRACKER.keys()):
            print self.set_line(self.server.TRACKER[key])
    ##
    ## If program terminates - dump tracker status to logfile
    ##
    def dump_atexit(self):
        print "Log: exiting - writing current status to logfile."
        self.dump_tracker_log()
        self.server.report()

    ##========================
    ##
    ## Daemon runner
    ##
    ##========================

    def run(self):
        """Function which is called from the Daemon runner"""
        print "MACupdTracker Starting on HOST: " + self.host + " on port", self.port
        self.server = SocketServer.UDPServer((self.host, self.port), Handler)
        #
        # Set Variables
        #
        self.server.TRACKER = {}
        self.server.MACLIST=self.MACLIST
        self.server.CONFIG=self.CONFIG
        #
        # Set current log date
        #
        now = datetime.now()
        self.server.LOG_DATE = now.strftime('%Y%m%d')
        #
        # Read status if current tracker logfile exists
        #
        self.read_tracker_status()
        #
        # Set logfile sizes
        #
        self.set_logfile_sizes()
        #
        # Instantiate alerter
        #
        alerter=Alerter()
        self.server.alert = alerter.alert
        #
        # Instantiate reporter
        #
        reporter=Reporter(logdir=self.logdir, reportdir=self.reportdir, maclist=self.MACLIST)
        self.server.report = reporter.report
        #
        # Export function to handler
        #
        self.server.dump_tracker_log = self.dump_tracker_log
        self.server.set_line = self.set_line
        self.server.rotate_logs = self.rotate_logs
        self.server.logdir = self.logdir
        self.rotate_logs()
        #
        # Register atexit
        #
        atexit.register(self.dump_atexit)
        #
        # Start UDP handler forever ...
        #
        self.server.serve_forever()

##=======================
##
## MAIN
##
##=======================

if __name__ == "__main__":

    app = MACupdDaemon()
    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.do_action()

##
## EOF
##
