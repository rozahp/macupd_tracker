##
## Filename: handler.py
##
## Description: handler class for receiving UDP-data from DD-WRT
##

import SocketServer

from datetime import datetime
import re

##
## Import project variables
##

from globals import *

##=================================
##
## Handler Class
##
##=================================
class Handler(SocketServer.BaseRequestHandler):
    """Handle MACudp information from DD-WRT router"""

    ##
    ## Setup
    ##
    def setup(self):
        """setup() is called first when a request is received"""
        self.current_date = False
        self.current_time = False
        self.current_hour = False
        self.current_key = False
        self.current_alert = False
        self.current_key_dict = {'mac':False,'ip':False,'iface':False}

    ##
    ## Set time
    ##
    def set_time(self):
        """Set date and time"""
        now = datetime.now()
        self.current_date = now.strftime("%Y%m%d")
        self.current_time = now.strftime("%H%M")
        self.current_hour = now.hour

    ##
    ## New row
    ##
    def new_row(self):
        """When a new key (mac+ip+iface) is found a new instance is created"""
        return {'mac':self.current_key_dict['mac'],
                'ip':self.current_key_dict['ip'],
                'iface': self.current_key_dict['iface'],
                'name': self.server.MACLIST[self.current_key_dict['mac']],
                'date':self.current_date,
                'time':self.current_time,'last': self.current_time,
                'active-hours':[INACTIVE_HOUR]*24}
    ##
    ## Update tracker
    ##
    def update_tracker(self):
        """This function updates the tracker and set alert=True if mac-address is unknown"""
        #
        # Set key
        #
        self.current_key = TRACKER_KEY_DELIM.join(self.current_key_dict[x] for x in TRACKER_KEY_PARTS)
        #
        # Check if key exists
        #
        if self.current_key not in self.server.TRACKER:
            #
            # New Key
            #
            self.server.TRACKER[self.current_key]=self.new_row()
            #
            # Check if MAC-address is unknown
            #
            if self.server.TRACKER[self.current_key]['name']==DEFAULT_NAME:
                #
                # Set Alert Flag
                #
                self.current_alert=True
        #
        # Update last time
        #
        self.server.TRACKER[self.current_key]['last']=self.current_time
        #
        # Update hour
        #
        if self.server.TRACKER[self.current_key]['active-hours'][int(self.current_hour)]==INACTIVE_HOUR:
            self.server.TRACKER[self.current_key]['active-hours'][int(self.current_hour)]=1
            ##
            ## Change is stored in the current logfile
            ##
            self.server.dump_tracker_log()
            self.server.report()
        #
        # Add hour counter
        #
        else:
            if self.server.TRACKER[self.current_key]['active-hours'][int(self.current_hour)]!=ACTIVE_HOUR:
                self.server.TRACKER[self.current_key]['active-hours'][int(self.current_hour)]+=1
                if self.server.TRACKER[self.current_key]['active-hours'][int(self.current_hour)]>ACTIVE_MAX:
                    self.server.TRACKER[self.current_key]['active-hours'][int(self.current_hour)]=ACTIVE_HOUR

    ##
    ## Dump line to terminal
    ##
    def dump_line(self, key):
        print self.server.set_line(self.server.TRACKER[key])
    ##
    ## Dump error
    ##
    def dump_err(self, error):
        """Log errors to file"""
        filename=self.server.logdir+"/"+ERRFILE_PREFIX+"."+str(self.server.LOG_DATE)+"."+LOGFILE_SUFFIX
        if DEBUG: print "Dumping error to file:", filename
        try:
            with open(filename,"a") as f:
                    f.write(str(self.current_date))
                    f.write(":")
                    f.write(str(self.current_time))
                    f.write(":")
                    f.write(error)
                    f.write('\n')

        except Exception as err:
            if DEBUG: print "Err: error while opening file:", err
            exit(-1)
    ##
    ## Dump alert
    ##
    def dump_alert(self, alert):
        """Log alerts to file"""
        filename=self.server.logdir+"/"+ALERTFILE_PREFIX+"."+str(self.server.LOG_DATE)+"."+LOGFILE_SUFFIX
        if DEBUG: print "Dumping alert to file:", filename
        try:
            with open(filename,"a") as f:
                    f.write(self.server.set_line(alert))
                    f.write('\n')

        except Exception as err:
            if DEBUG: print "Err: error while opening file:", err
            exit(-1)
    ##
    ## Check new date
    ##
    def check_new_date(self):
        """Check if date has changed, then rotate logfile and reset tracker"""
        if self.server.LOG_DATE != self.current_date:
            #
            # Dump tracker dictionary to file
            #
            self.server.dump_tracker_log()
            self.server.report()
            self.server.rotate_logs()
            self.server.LOG_DATE = self.current_date
            #
            # Reset tracker dictionary
            #
            self.server.TRACKER={}

    ##=========================================
    ##
    ## Handle Udp Data - The Request Handler
    ##
    ## Is called after setup()
    ##
    ##=========================================
    def handle(self):
        """handle() is called after setup()"""
        #
        # Update time
        #
        self.set_time()
        #
        # Error catcher
        #
        try:
            #
            # Parse udp data
            #
            data = self.request[0].strip()
            client = self.client_address[0]
            data_array = re.split(r"\s+", data)

            #
            # Error check
            #
            if len(data_array) != 7:
                error="Err: data_array is invalid: "+str(data_array)
                if DEBUG: print error
                self.dump_err(error)
                return
            #
            # Check if new date, then rotate logfiles
            #
            self.check_new_date()
            #
            # Get key data
            #
            self.current_key_dict['ip'] = data_array[MACUPD_POINTERS['ip']]
            self.current_key_dict['mac'] = data_array[MACUPD_POINTERS['mac']].lower()
            self.current_key_dict['iface'] = data_array[MACUPD_POINTERS['iface']]
            #
            # Update tracker
            #
            self.update_tracker()
            #
            # Check alert flag
            #
            if self.current_alert:
                self.server.alert(self.server.TRACKER[self.current_key])
                self.dump_alert(self.server.TRACKER[self.current_key])
                self.server.report()
        #
        # Exception handler
        #
        except Exception as err:
            error="Err: exception occurred in handle(): "+str(err)
            if DEBUG: print error
            self.dump_err(error)

    ##
    ## Finish
    ##
    def finish(self):
        """finish() is called last after a request is received"""
        #
        # Print current row to terminal
        #
        if DEBUG: self.dump_line(self.current_key)

##
## EOF
##
