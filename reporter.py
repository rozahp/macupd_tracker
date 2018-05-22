#!/usr/bin/env python
##
## Filename: reporter.py
##
## Description: Reporter class
##

import os
import sys
from datetime import datetime

##
## Import project variables
##
from globals import *

##=======================
##
## MacupdReporter
##
##=======================

class Reporter:
    """Report class for creating html reports from logfiles"""
    def __init__(self, logdir=False, reportdir=False, maclist={}):
        self.logdir = logdir
        self.reportdir = reportdir
        self.filename = False
        self.maclist=maclist

    ##
    ## Check Row
    ##
    def reporter_check_row(self, row):
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
    ## Set line
    ##
    def reporter_set_line(self, keyline):
        """
        Input: dictionary with macupd data from DD-WRT.
        Output: string with data for logfiles.
        """
        line=""
        for key in REPORTFILE_HEADER:
            if isinstance(keyline[key], list):
                line+=''.join(str(x) for x in keyline[key])
            else:
                line+='{0:{1}}'.format(keyline[key],LOGFILE_SIZES[key])
        return line
    ##
    ## Get logfiles
    ##
    def reporter_get_logfiles(self):
        """Returns a list of logfiles in logdir"""
        alertFiles=[]
        trackerFiles=[]
        errorFiles=[]
        for f in os.listdir(self.logdir):
            #
            # Check If logfile
            #
            if "." not in f: continue
            if len(f.split("."))!=3: continue
            if not f.split(".")[1].isdigit(): continue
            if f[-len(LOGFILE_SUFFIX):]!=LOGFILE_SUFFIX: continue
            #
            # Get tracker logfiles
            #
            if f[0:len(TRACKERFILE_PREFIX)]==TRACKERFILE_PREFIX:
                trackerFiles.append(f)
            #
            # Get alert logfiles
            #
            elif f[0:len(ALERTFILE_PREFIX)]==ALERTFILE_PREFIX:
                alertFiles.append(f)
            #
            # Get error logfiles
            #
            elif f[0:len(ERRFILE_PREFIX)]==ERRFILE_PREFIX:
                errorFiles.append(f)
            #
            else: continue
        return trackerFiles, alertFiles, errorFiles

    ##
    ## Parse tracker files for report
    ##
    def parse_tracker_files(self, filelist):
        """Read logfiles and parse them for report"""
        REPORT={}
        filelist.sort()
        for filename in filelist:
            filename=self.logdir+"/"+filename
            try:
                fp = open(filename,"r")
            except Exception, err:
                print "Err: error while opening file", err
                exit(-1)
            for row in fp.readlines():
                #
                # Check row
                #
                row_dict=self.reporter_check_row(row)
                if row_dict==False: continue
                #
                # Fix mac name
                #
                if row_dict['mac'] in self.maclist: row_dict['name']=self.maclist[row_dict['mac']]
                #
                # Add row to dict
                #
                row_key=REPORT_KEY_DELIM.join(row_dict[x] for x in REPORT_KEY_PARTS)
                if row_key not in REPORT:
                    REPORT[row_key]=[]
                REPORT[row_key].append(row_dict)
            #
            # Close file
            #
            fp.close()

        return REPORT
    ##
    ## Parse logfiles for report
    ##
    def parse_logfiles(self, filelist):
        """Read lines from error and alert logfiles and parse them for report"""
        LINES=[]
        filelist.sort()
        for filename in filelist:
            filename=self.logdir+"/"+filename
            try:
                fp = open(filename,"r")
            except Exception, err:
                print "Err: error while opening file:" ,err
                exit(-1)

            for row in fp.readlines():
                row=row.strip()
                LINES.append(row)
            #
            # Close file
            #
            fp.close()

        return LINES

    ##
    ## Report
    ##
    def report(self):
        """Read logfiles and produce html-report to logdir"""
        #
        # Create report files
        #
        self.filename=self.reportdir+"/"+REPORTFILE_PREFIX+".html"
        try:
            fp=open(self.filename,"w")
        except Exception, err:
            print "Err: error while opening filename for report:", err
            exit(-1)
        #
        #  HTML header
        #
        now=datetime.now()
        fp.write("<html>\n")
        fp.write("<head><title>MACupdTracker Report</title></head>\n")
        fp.write("<h1>MACupdTracker Report - "+now.strftime('%Y-%m-%d %H:%M:%S')+"</h1>\n")
        fp.write("<body>\n")
        #
        # Get logfiles
        #
        trackerFiles, alertFiles, errorFiles=self.reporter_get_logfiles()
        #
        # Get data from logfiles
        #
        trackerDict=self.parse_tracker_files(trackerFiles)
        alertList=self.parse_logfiles(alertFiles)
        errorList=self.parse_logfiles(errorFiles)
        #
        # Set big and small pre-tag
        BIGPRE='<pre style="font-size: 18px; bold">'
        SMALLPRE='<pre style="font-size: 14px">'
        #
        #
        # Print mac list
        #
        fp.write("<h2>Collected MAC-addresses</h2>\n")
        if len(trackerDict)==0:
            fp.write(SMALLPRE+'\nNo MAC-addresses.\n')
        else:
            fp.write(BIGPRE+'\n')
            for key in sorted(trackerDict.keys()):
                fp.write(str(key)+'\n')
        fp.write('</pre>\n')
        #
        # Print tracker details
        #
        fp.write("<h2>Activity Details</h2>\n")
        if len(trackerDict)==0:
            fp.write(SMALLPRE+'\nNo activity details.\n</pre>\n')
        else:
            for key in sorted(trackerDict.keys()):
                lines=trackerDict[key]
                fp.write(BIGPRE+str(key)+"</pre>\n")
                fp.write(SMALLPRE+"\n")
                lines=sorted([self.reporter_set_line(row) for row in lines])
                for row in lines:
                    fp.write(row)
                    fp.write('\n')
                fp.write("</pre>\n")
        #
        # Print alerts
        #
        fp.write("<h2>Alerts</h2>\n")
        fp.write(SMALLPRE+'\n')
        if len(alertList)==0:
            fp.write("No alerts.\n")
        else:
            for row in alertList:
                fp.write(row)
                fp.write('\n')
        fp.write('</pre>\n')
        #
        # Print error data
        #
        fp.write("<h2>Errors</h2>\n")
        fp.write(SMALLPRE+'\n')
        if len(errorList)==0:
            fp.write("No errors.\n")
        else:
            for t in errorList:
                fp.write(t)
                fp.write('\n')
        fp.write('</pre>\n')
        #
        # End
        #
        fp.write("<h3>End of report</h3></body>\n</html>\n")
        fp.close()

##==================
##
## MAIN
##
##==================
if __name__ == '__main__':

    if len(sys.argv) < 2:
        sys.stderr.write('Usage: ./reporter.py LOGDIR \n')
        sys.exit(1)

    if not os.path.exists(sys.argv[1]):
        sys.stderr.write('Err: logdir was not found!\n')
        sys.exit(1)

    reporter=Reporter(logdir=sys.argv[1], reportdir=sys.argv[1])
    reporter.report()

    with open(reporter.filename, "r") as fp:
        for line in fp.readlines():
            print line.strip()

##
## EOF
##
