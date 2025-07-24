#!/usr/bin/python

# Tested on NXOS
# Purpose: Program to grab MAC addresses from MS switches for mgmt interfaces
# Current Functionality: Returns a dictionary with FEX Serial Number (key)/Interface ID (value)

from __future__ import print_function

__version__ = "1.0.1"
__date__    = "2019-05-17"
__author__  = "Tyler Reymer"
__email__   = ""

import argparse
import os
import getpass
import re
import sys
import traceback
import readline
import time

import pexpect
import json

parser = argparse.ArgumentParser(description='Get MAC addresses from MS switch')
required_group = parser.add_argument_group(title="Required", description="Regex modes")
required_group.add_argument("-i", dest="ms_ip", help="Management Switch IP")
required_group.add_argument("-s", dest="fex_serial_number", help="Enter the Serial Number of the FEX")

args = parser.parse_args()  
USER = getpass.getuser()

def build_fex_dict(buffer):
    fex_id_dict = {}
    fex_serial = ""
    fex_list = buffer.split('\r\n')
    fex_list = fex_list[4:] # Chop first 4 lines of table headers
    fex_list = fex_list[:-1] # Chop last line which is actually the command prompt
    for i in fex_list:
       fex_id = i.split()[0]
       if len(i.split()[-1]) == 11: # Since we make assumption serial is last element, sanity check if it's 11 char long
           fex_serial = i.split()[-1] # which is typical length of a Cisco serial number
       else:
           print("No FEX serial found")
           fex_serial = "XXXXXXXXXXX" # Fail safe
       fex_id_dict[fex_serial] = fex_id
    return fex_id_dict

def get_fex_id(fex_dict, serial):
    return fex_dict[serial]

def build_serial_int_dict(fex_id, exp):
    print("FEX ID is {} for {}".format(fex_id, args.fex_serial_number))
    exp.sendline("show interface status | grep Eth" + fex_id)
    exp.expect('#')
    exp.sendline("show mac address-table | grep Eth" + fex_id)
    exp.expect("#")
    # Get the interface id for the fex
    interface_id_list = re.findall('Eth' + fex_id + '/1/\d{1,2}', exp.before)
    mac_address_list = re.findall('[a-z0-9]{4}\.[a-z0-9]{4}\.[a-z0-9]{4}', exp.before)
    # Create a dictionary with MAC and int id
    mac_address_interface_dict = {key:value for key, value in zip(mac_address_list, interface_id_list)}
    # Reformat the MAC addresses to xx.xx.xx.xx.xx.xx format
    for key, value in mac_address_interface_dict.items():
        new_key = key.replace('.', '').upper()
        new_key = ':'.join([new_key[i : i + 2] for i in range(0, len(new_key), 2)])
        mac_address_interface_dict[new_key] = mac_address_interface_dict.pop(key)
    return mac_address_interface_dict

def spawn_ssh():
    exp = pexpect.spawn("ssh " + args.ms_ip, timeout=15)
    exp.setwinsize(400,400)
    exp.setecho(False)
    return exp

def main():
    args.password_ldap = getpass.getpass("Enter LDAP password:")
    file_log = ""
    try:
        exp = spawn_ssh()
        file_log = open("/home/" + USER + "/ms_mac_interrogator_" + args.ms_ip, "w")
        exp.logfile_read = file_log
        connected = False
        login_attempts = 0
        while connected == False:
            i = exp.expect(["Password: ", "Are you sure you want to continue connecting (yes/no)?", "#", "Authentication failed."])
            if i == 0:
                exp.sendline(args.password_ldap)
                login_attempts += 1
            elif i == 1:
                exp.sendline("yes")
                exp.expect("Password: ")
                exp.sendline(args.args.password_ldap)
                login_attempts += 1
            elif i == 2:
                connected = True
            elif i == 3:
                connected = False
                print("Authentication Failed... Terminating program... Check log home/" + USER + "/ms_mac_interrogator_" + args.ms_ip)
                login_attempts += 1
                os._exit(1)
            else:
                connected = False
                login_attempts += 1
    except:
        tb = traceback.format_exc()
        file_log.write(tb)
        print(tb)
        exp.close(force=True)
        return False

    if connected:
        print("Connected to " + args.ms_ip)
        exp.sendline("show fex")
        exp.expect('#')
        # Build FEX ID dict
        fex_dict = build_fex_dict(exp.before)
        # Find FEX ID for given serial number
        fex_id = get_fex_id(fex_dict, args.fex_serial_number)
        # Build dict with FEX serial numbers (key) and eth interfaces (value)
        mac_address_interface_dict = build_serial_int_dict(fex_id, exp)
        print(json.dumps(mac_address_interface_dict, indent=4))
        # Exit gracefully
        exp.sendline("exit")
        exp.close(force=True)
        exp.logfile_read.close()
    else:
        print("Not connected to " + args.ms_ip)

    print("Done")

if __name__ == "__main__":
    main()
