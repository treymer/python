#!usr/bin/python

# Created by: Tyler Reymer
# Date: 9/14/16
# Usage: Configure APC PDU's via CLI

#************ MODULES **************

import pexpect
import argparse
import time,sys
import readline

#***********************************

parser = argparse.ArgumentParser(description='Configure APC PDUs.')
parser.add_argument('-u', dest='default_username', default="apc", help='Default APC root username. (Default is typically "APC")')
parser.add_argument('-U', dest='default_password', default="apc", help='Defualt APC root password. (Default is typically "APC")')
parser.add_argument('-a', dest='super_username', default="root", help='Set superuser username.')
parser.add_argument('-A', dest='super_password', help='Change password for apc SU.') # We need to choose a pw

args = parser.parse_args() # Create object args from parser

def configure_pdu(ip):
	# Telnet to PDU using default creds
	exp = pexpect.spawn("telnet " + ip)
	# exp.timeout = 5 # For debugging

	file_log = open("test", "w")
	exp.logfile = file_log

	exp.expect("User Name :") # Username
	exp.send(args.default_username + "\r")
	exp.expect("Password  :") # Password
	exp.send(args.default_password + "\r") # Need the carriage return
	
	exp.expect("apc>")

	exp.send("console -s enable") # Enable SSH - Requires Reboot
	exp.expect("apc>")
	
	exp.send("console -t disable") # Disable Telnet - Requires Reboot
	exp.expect("apc>")

	exp.send("user-an" + args.super_username)
	exp.expect("") # Need to test this
	
	print ip + ' Login was successful'
	exp.sendline("exit")


ip = raw_input('Enter IP of APC PDU:') 

configure_pdu(ip)

print 'Complete'

sys.exit(0)
