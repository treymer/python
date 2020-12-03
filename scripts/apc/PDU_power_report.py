#!/usr/bin/python

# Created by: Ezio Ballarin
# Date: 7/17/18 
# Last Updated; 7/17/18
# Usage: Generate a report of PDUs instantaneous watt usage 
# TODO:  
# Tested on APC's AOS v6.4.6

#************ MODULES **************
import sys
import argparse
import time
import string

import getpass   # Prompting for un-echoed password
import pexpect   # SSH  


#***********************************

parser = argparse.ArgumentParser(description='Generate a power report for a given list of PDUs')
parser.add_argument('-r', dest='reboot_interface', action='store_true', help='Reboots the management interface. (Does not affect PDU power)')

args = parser.parse_args()  # Create object args from parser

TIMEOUT_SHORT = 1
TIMEOUT_LONG = 20

########### CLASSES ###########
# Base class for our PDUs
class PDU:
    
    # Superclass ctor
    def __init__(self, ip):
        self.ssh_session = None
        self.pw = None
        self.ip = ip

    # Abstract methods, implemented in subclasses
    def login_ssh(self):
        raise NotImplementedError("Subclass must implement login_ssh()")
    def logout_ssh(self):
        raise NotImplementedError("Subclass must implement logout_ssh()")
    def get_instant_power(self):
        raise NotImplementedError("Subclass must implement get_instant_power()")

# APC specific implentations
class APC_PDU(PDU):
    def login_ssh(self):
        ip = str(self.ip)
        user = "apc"
        pw = self.pw

        self.ssh_session = pexpect.spawn("ssh", [user + '@' + ip])

        self.ssh_session.expect('password: ', TIMEOUT_LONG)
        self.ssh_session.sendline(pw)

        time.sleep(1)
        self.ssh_session.expect('apc>')
        return

    def logout_ssh(self):
        if (self.ssh_session) is not None:
            self.ssh_session.sendline('bye')
            self.ssh_session.kill(9)
        return

    def get_instant_power(self):
        if (self.ssh_session) is not None:
            self.ssh_session.sendline("bkReading")
            self.ssh_session.expect('apc>', TIMEOUT_LONG)
        return self.ssh_session.before

# Server Technology specific implementations
class ST_PDU(PDU):
    def login_ssh(self):
        return
    def logout_ssh(self):
        return
    def get_instant_power(self):
        return

###############################

# Close open files, print a message to console/log, and
# exit with bad status code
def pdu_report_failed(ip_file, log_file, msg):
    print(msg)
    if log_file is not None:
        if not log_file.closed:
            log_file.write("[" + time.strftime("%H:%M:%S") + "] ERROR: " + msg + "\n\n")
            log_file.close()
    if ip_file is not None:
        if not ip_file.closed:
            ip_file.close()
    print("Exiting")
    sys.exit(-1)
    return


# Write to the log file with a specific format
def pdu_power_log_msg(log_file, msg):
    print(msg)
    log_file.write("[" + time.strftime("%H:%M:%S") + "] " + msg + "\n")
    return

# Get the current power from an APC/Server Tech PDU
def get_power(pdu_info, pdu_pw, log_file):
    pdu_manufacturer = pdu_info[0]
    pdu_ip = pdu_info[1]
    pdu = None

    # Initialize appropriate object
    if pdu_manufacturer == "APC":
        pdu = APC_PDU(pdu_ip)
    elif pdu_manufacturer == "ST":
        pdu = ST_PDU(pdu_ip)
    
    # Login to the PDU, grab the power reading, and logout
    pdu.pw = pdu_pw
    pdu.login_ssh()
    timestamp = time.strftime("%H:%M:%S")
    power = pdu.get_instant_power()
    pdu.logout_ssh()

    # Remove all white space
    power = "".join(power.split()) 

    # Find indices for substring later on
    try:
        bank_1 = power.index("1:")
    except ValueError as err:
        pdu_power_log_msg(
            log_file, 
            "Bank 1 not found in power result: {0}".format(err)
        ) 
    try:
        bank_2 = power.index("2:")
    except ValueError as err:
        pdu_power_log_msg(
            log_file, 
            "Bank 2 not found in power result: {0}".format(err)
        ) 
   
    # At this point, power contains a string similar to
    #    bkReadingE000:Success1:4.4A2:3.6A
    # We need to trim this down to just the power bank, and the power being used.

    # Create substrings that contain only the power bank number and power 
    bank_1_power = power[bank_1:bank_2-1]
    bank_2_power = power[bank_2:-1]

    # Partition strings to allow for easier access of bank number and power
    bank_1_power = bank_1_power.partition(":")
    bank_2_power = bank_2_power.partition(":")
    
    power_usage = [timestamp, float(bank_1_power[2]), float(bank_2_power[2])]
    return power_usage

def main():

    print ("Enter the master password for the PDU's: ")
    master = getpass.getpass()

    log_file = None
    pdu_ip_file = None

    log_file = open("PDU_power_report_" + time.strftime("%b_%d_%Y") + ".log", "a")
    pdu_power_log_msg(log_file, "Starting script...")

    # Write all command line args to the log
    log_file.write(str(vars(args)) + "\n")

    # Prompt user for path to file which contains newline separated
    # IP addresses of PDU's
    while True:
        pdu_ip_fname = raw_input("Enter filename for PDU IP's: ")
        try:
            pdu_ip_file = open(pdu_ip_fname)
            break
        except OSError as err:
            pdu_report_failed(pdu_ip_file, log_file, "{}".format(err))

    # File was successfully opened, convert its contents to a list
    pdu_power_log_msg(log_file, "Reading from " + pdu_ip_fname)

    # IP file is comma separted with format: vendor, IP
    # Move through IP file line by line and get instant power 
    # for each (PDU, IP) pair
    for line in pdu_ip_file:
        line = line.strip()
        pdu_info = line.split(",")
        power_usage = get_power(pdu_info, master, log_file)
        print power_usage
        

    pdu_ip_file.close()
    return


if __name__ == "__main__":
    main()
