#!/usr/bin/env python

#+++++++++++++++++++++++++

import sys
import logging
import time
import urllib2
import xml.etree.ElementTree as ET
from collections import OrderedDict

#+++++++++++++++++++++++++

urlDict = OrderedDict([
                       ('IRV-PWRMTR', 'http://192.168.x.x/I/pdata.xml')
                     ])
logFilename = '/var/tmp/cdcpwrmtr.log'

def logWatts(d, totalInstWatt):
    #Setup logger object
    logger = logging.getLogger('cdcpwrmtr')
    hdlr = logging.FileHandler(logFilename)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    if(totalInstWatt > 0):
        for k,v in d.iteritems():
            l,r = v.split('!!')
            meterSide = k.split('-')
            logger.debug('%s %s-Side %s' % (l, meterSide[2], r))
        logger.debug('Total Instant Watt %d' % (totalInstWatt))

def totalWatts(d, totalInstWatt):
    print "Data that was logged: "
    print (time.strftime("%d/%m/%Y")) + " " + (time.strftime("%H:%M:%S"))
    for k,v in d.iteritems():
        l,r = v.split('!!')
        value = float(r.rstrip(" k"))
        totalInstWatt += value
        print k + ": " + l + ": " + str(value)
    print "Total Watt: " + str(totalInstWatt)
    logWatts(d, totalInstWatt)

def main():
    totalInstWatt = 0.0
    d = OrderedDict()

    for k,v in urlDict.iteritems():
        tree = ET.ElementTree(file=urllib2.urlopen(v))
        root = tree.getroot()
        instWattLbl = root[2][4].attrib.get('D_LABEL')
        instWatt = root[2][4].attrib.get('D_VALUE')
        d[k] = instWattLbl + '!!' + instWatt
    totalWatts(d, totalInstWatt)
    print "Done."

if __name__ == '__main__':
    sys.exit(main())
