##
## Filename:  alerter.py
##
## Description: Alerter class for MACupdTracker
##

DEBUG=False

from globals import *

##=================================
##
## Alerter Class
##
##=================================
class Alerter:
    """
    Barebone alerter class for MACupdTracker
    Write your own and import it into this file
    """
    def __init__(self):
        pass
    #
    # Alert
    #
    def alert(self, message):
        """
        Alert message received from the MACupdTRacker()
        when a unknown MAC-address is collected.
        Message is a dictionary with following keys:
        'mac','name','ip','iface','date','time','last','active-hours'
        """
        if DEBUG: print "Alerter got message:", message


##
## EOF
##
