# macupd_tracker

This program process MACupd data from DD-WRT router. Every hour current status is written to a logfile and a HTML-report is also created/updated. When an unknown MAC-adress is received for the 1st time an alert-function is called (see below about the alerter function) and the logfile and the HTML-report is created/updated.

When the program is started it tries to read the status from the current logfile. The tracker status is cleared every midnight and logfiles are rotated. On exit or if an exception occur, status is saved to current logfile and the HTML-report is updated. The name of the logfiles are changed every day (se format below)

Errors are dumped to a logfile (see below).

This program should work on any Linux system with Python 2.7

## AUTHOR

Phazor / Cascade 1733

## LICENSE

Please feel free to copy, distribute and change this program in any way you like.

## INSTALLATION

1) Install python 2.7

2) Activate MACupd service on DD-WRT:

* Login on the routers webinterface and click on tab: Services > Services
* Scroll down and find: RFlow / MACupd
* Enable MACupd and set the IP-address to the host running macupd_tracker.py

3) Edit: macupd_tracker.conf

5) Start: python macupd_tracker.py start

6) Stop:  python macupd_tracker.py stop

Debugging: To enable debugging set DEBUG=True in globals.py.

## CONFIGFILE

Edit macupd_tracker.conf to suit your system.

Example:

    [MAIN]
    HOST=0.0.0.0  # Host running macupd_tracker.py
    PORT=2056     # Default port for dd-wrt's macupd
    PIDFILE=/path/to/pid/dir/macupd_tracker.pid
    LOGDIR=/path/to/log/dir
    REPORTDIR=/path/to/report/dir
    MAXLOGS=31    #Remove logs older then 31 days
    ##
    ## List of known MAC-addresses
    ##
    [MACLIST]
    11:11:11:11:11:11|router
    22:22:22:22:22:22|windows
    33:33:33:33:33:33|linux
    44:44:44:44:44:44|tv
    55:55:55:55:55:55|mobile

## LOGFILES

There are 3 types of logfiles:

* Tracker: macupd_tracker.YYYYMMDD.log - current status.
* Alert:   macupd_alert.YYYYMMDD.log - log of alerts.
* Error:   macupd_error.YYYYMMDD.log

### Tracker log example:

    mac               name      ip              iface date     time last   active-hours
    22:22:22:22:22:22 windows   192.168.1.124   br0   20180320 1031 2231 ......12..............*.
    33:33:33:33:33:33 linux     192.168.1.240   br0   20180320 2251 2251 ...........1..........*.
    55:55:55:55:55:55 mobile    192.168.1.244   vlan2 20180320 2037 2359 ..............9.....****

#### Explanation:

    mac:    MAC-address as reported by MACupd
    ip:     IP-address as reported by MACupd
    iface:  Interface as reported by MACupd
    date:   date
    time:   first time a mac/ip/iface was reported.
    last:   last time the mac/ip/iface was reported.
    active-hour: 24 characters for each hour a day:
            .     inactive
            1-9   active between 1 to 9 times
            *     active 10 times or more

### Alert log example:

    66:66:66:66:66:66 unknown   192.168.1.124   br0   20180320 1031 1031 ......12.......**.......
    77:77:77:77:77:77 unknown   192.168.1.240   br0   20180320 2251 2251 ...........1............
    88:88:88:88:88:88 unknown   172.16.42.33    vlan2 20180320 2037 2037 ..............1.........

## ALERTER

If you want you could write an alerter function by editing alerter.py.  Current file is a barebone class which does nothing.

The alerter is instantiated by the MACupdDaemon class and called by the handler when an unknown MAC-address is processed. This will happen every day because the tracker is cleared at midnight. You have to name the MAC-address in the macupd_tracker.conf if you don't want any daily alerts.

All alerts are logged to file: macupd_alert.YYYYMMDD.log

### Example code

Editing alerter.py:

    from boxcar_class import BoxcarClass # boxcar.io

    class Alerter:
        def __init__(self):
            pass
        def alert(self, message):
            b=BoxcarClass(tokenfile="mytokenfile.ini")
            b.title="New MAC-address"
            b.message="New mac-address on your network"
            b.source="MACupdTracker"
            b.send()  #Send message via boxcar.io
            del b

## REPORTS

Every hour and when an unknown MAC-address is processed a HTML-report is created/updated and saved: REPORTDIR/macupd_report.html

Run ./reporter.py LOGDIR to update HTML-report and dump it to the terminal.

## REMARKS

Builds on ideas from **ntop-description-updater** by **beaugunderson**. Thanks for the inspiration!

## TODO

* Better report format
* ?
