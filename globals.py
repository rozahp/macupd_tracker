##
## Filename:  globals.py
##
## Description: Global variables for MACupdTracker
##
DEBUG=False
CONFIGFILE='macupd_tracker.conf'
TRACKERFILE_PREFIX='macupd_tracker'
ALERTFILE_PREFIX='macupd_alert'
ERRFILE_PREFIX='macupd_error'
LOGFILE_SUFFIX='log'
ACTIVE_HOUR='*'     # Character representing active hour (above 10 collections)
INACTIVE_HOUR='.'   # Character represeting inactive hour
ACTIVE_MAX=9        # Max activity per hour before ACTIVE_HOUR mark is set
MACUPD_POINTERS={'ip':1, 'mac':4,'iface':6} # Pointers to data in list from dd-wrt
TRACKER_KEY_PARTS=['mac','ip','iface']      # Dictionary key parts
TRACKER_KEY_DELIM='-' # Delimiter for key parts
REPORT_KEY_PARTS=['mac','name']
REPORT_KEY_DELIM=' '
REPORTFILE_HEADER=['date','time','last','ip','iface','active-hours']
LOGFILE_HEADER=['mac','name','date','time','last','ip','iface','active-hours']
LOGFILE_SIZES={'mac':18, 'name':9, 'ip':16, 'iface':6, 'date':9,'time':5, 'last':5,'active-hours':24}
MACLIST_PARTS=['mac','name']
CONFIG_PARTS=['host','port','pidfile','logdir','reportdir','maxlogs']
DEFAULT_NAME='unknown'
REPORTFILE_PREFIX='macupd_report'
##
## EOF
##
