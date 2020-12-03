#!/usr/bin/python

# Created by: Tyler Reymer
# Date: 5/21/2018
# Usage: Check Firmware version, change admn password, sets hostname, queries LDAP. I changed.
# Citations: Dell/HP Configurator/Interrogator.
# TODO: Disable telnet, set temp probe names

import pexpect
import argparse
import sys
import readline
import re
import traceback
import getpass
import ldap
import ldap.modlist

OU_LOCATIONS = "ou=locations,dc=battle,dc=net"

parser = argparse.ArgumentParser(description='Check Server Tech PDU firmware version.')
parser.add_argument('-u', dest='username', default="admn", help='Default Server Tech root username. (Default is typically "admn")')
parser.add_argument('-p', required=True, dest='current_super_password', action='store_true', default="admn", help='Enter current super user password for admn account. (Default is \'admn\')')
parser.add_argument('-P', dest="change_super_password", action='store_true', help='Set the new super use password for admn account.')
parser.add_argument('-b', dest="set_hostname", action='store_true', help='Set the hostname of PDU')
required_group = parser.add_argument_group(title="Required", description="Regex modes")
regex_group = required_group.add_mutually_exclusive_group(required=True)
regex_group.add_argument("-i", dest="regex_pdu", help="Regex defining PDUs to configure.")
optional_group = parser.add_argument_group(title="Optionals")
optional_group.add_argument("-l", dest="ldapurl", help="LDAP URL", default="ldap://{uri}")
optional_group.add_argument("-d", dest="ldapdn", help="LDAP DN")

args = parser.parse_args()  # Create object args from parser

class SERVERTECH_PDU:

    def __init__(self, ip):
        self.ip = ip


    def spawn_ssh(self):
        try:
            self.exp = pexpect.spawn("ssh " + args.username + "@" + self.ip, timeout=15)
            self.exp.setecho(False)
            file_log = open("Servertech_configurator_log_" + self.ip, "w")
            self.exp.logfile = file_log
            connected = False
            login_attempts = 0
            while connected == False:
                i = self.exp.expect(["Password: ", "Are you sure you want to continue connecting (yes/no)?", "DU:"])
                if login_attempts >= 2:
                    connected = False
                    print "Wrong admn password, tried logging in " + str(login_attempts) + " times."
                    break
                if i == 0:
                    self.exp.send(args.current_super_password + "\r")
                    login_attempts += 1
                elif i == 1:
                    self.exp.send("yes" + "\r")
                    self.exp.expect("Password: ")
                    self.exp.send(args.current_super_password + "\r")
                    login_attempts += 1
                elif i == 2:
                    connected = True
                else:
                    connected = False
                    login_attempts += 1
            if connected:
                return True
            else:
                return False
        except:
            tb = traceback.format_exc()
            file_log.write(tb)
            self.exp.close(force=True)
            return False


    def get_firmware_version(self):
        self.exp.send("\r")
        i = self.exp.expect(["Smart CDU:", "Smart PDU:"])
        if i == 0:
            self.exp.send("show system" + "\r")
            self.exp.expect("Smart CDU:")
            self.firmware = re.search('F/W Version:\s*Sentry Smart CDU Version ([.a-z0-9])*', self.exp.before).group(0).split("DU Version")[1].strip()
            print "Firmware Version: " + self.firmware
        elif i == 1:
            self.exp.send("show system" + "\r")
            self.exp.expect("Smart PDU:")
            self.firmware = re.search('Firmware:\s*Sentry Smart PDU Version ([.a-z0-9])*', self.exp.before).group(0).split("DU Version")[1].strip()
            print "Firmware Version: " + self.firmware
        else:
            print "Could not get firmware."
            return
        return


    def set_password(self, new_super_password):
        self.exp.send("password" + '\r')
        i = self.exp.expect(["Enter Current Password:", "Current Password:"])
        if i == 0:
            self.exp.send(args.current_super_password + '\r')
            self.exp.expect("Enter New Password:")
            self.exp.send(new_super_password + '\r')
            self.exp.expect("Verify Password:")
            self.exp.send(new_super_password + '\r')
            self.exp.expect("Smart CDU:")
            print "Set new admn password for " + self.ip
        elif i == 1:
            self.exp.send(args.current_super_password + '\r')
            self.exp.expect("New Password:")
            self.exp.send(new_super_password + '\r')
            self.exp.expect("Verify Password:")
            self.exp.send(new_super_password + '\r')
            self.exp.expect("Smart PDU:")
            print "Set new admn password for " + self.ip
        else:
            print "Could not set password."
            return
        return


    def set_hostname(self, hostname, master):
        self.exp.send("\r")
        i = self.exp.expect(["Smart CDU:", "Smart PDU:"])
        if i == 0:
            if master:
                self.exp.send("set tower name .a " + hostname + '\r')
                self.exp.expect("Smart CDU:")
                print "Set master hostname " + hostname
            else:
                self.exp.send("set tower name .b " + hostname + '\r')
                self.exp.expect("Smart CDU:")
                print "Set slave hostname " + hostname
        if i == 1:
            if master:
                self.exp.send("set unit name a " + hostname + '\r')
                self.exp.expect("Smart PDU:")
                print "Set master hostname " + hostname
            else:
                self.exp.send("set unit name b " + hostname + '\r')
                self.exp.expect("Smart PDU:")
                print "Set slave hostname " + hostname
        return


    def logout(self):
        self.exp.send("exit" + "\r")
        self.exp.close(force=True)
        self.exp.logfile.close()
        print "Logged out of " + self.ip + "\n"
        return

def password_checker():
    mismatch = True
    while mismatch:
        password1 = getpass.getpass("Enter new admn password:")
        password2 = getpass.getpass("Enter new admn password again:")
        if password1 == password2:
            mismatch = False
            return password1
        else:
            print "Passwords do not match. Please enter again."


def main():
    pdu_ip_file = open("{textfile}")
    ip_list = pdu_ip_file.read().splitlines()   # strip \n

    args.password_ldap = getpass.getpass("Enter LDAP password:")

    # Set LDAP DN if not given
    if args.ldapdn == None:
        args.ldapdn = "user=%s,ou=users,dc=,dc=" % getpass.getuser()

    #  Auth LDAP
    print "Accessing LDAP..."
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    l = ldap.initialize(args.ldapurl)
    l.start_tls_s()
    try:
        l.simple_bind_s(args.ldapdn, args.password_ldap)
    except ldap.INVALID_CREDENTIALS:
        print "LDAP password incorrect."
        sys.exit()
    sys.stdout.write("Searching locations...")
    locations = l.search_s(OU_LOCATIONS, ldap.SCOPE_SUBTREE,'(objectClass=location)', ['parent', 'section', 'location', 'interface'])
    print "Done"
    
    #  Search LDAP
    servertech_pdus = []
    if args.regex_pdu:
        for dn, attr in locations:
            m = re.match(args.regex_pdu, attr['location'][0])  # Get IP address of master PDU
            if m and 'interface' in attr:
                for i in attr['interface']:
                    name, address = i.split("=")
                    if name == "eth0":
                        servertech_pdus.append((attr['location'][0], address))
            m2 = re.match(args.regex_pdu, attr['location'][0])  # Get hostname of master PDU
            if m2 and 'section' in attr:
                for i in attr['section']:
                    servertech_pdus.append((attr['location'][0], i))

    #  Print LDAP search
    print "Amount of entries found: " + str(len(servertech_pdus))
    for hostname, ip in servertech_pdus:
        print hostname + " " + ip

    good_search = raw_input("Good to go?[Y/N]: ")
    if good_search == 'N' or good_search == 'n':
        sys.exit(0)

    if args.current_super_password:
        args.current_super_password = getpass.getpass("Enter current admn password:")

    if args.change_super_password:
        new_super_password = password_checker()

    #  Find IPs in list and set hostnames
    for hostname, ip in servertech_pdus:
        master = False
        if re.match("\\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\\b", ip):
            master = True
            pdu = SERVERTECH_PDU(ip)
            print "Trying to connect to " + ip
            connected = pdu.spawn_ssh()
            if connected:
                print "Configuring " + ip
                if args.set_hostname:
                    pdu.set_hostname(hostname, master)
                pdu.get_firmware_version()
                if args.change_super_password:
                    pdu.set_password(new_super_password)
                pdu.logout()
            else:
                print "Can't connect to " + ip + ", check log."
                continue
        else:  # Used to set slave hostname
            print hostname + " connected to master " + ip
            master_hostname = ip
            slave_hostname = hostname
            master = False
            for hostname2, ip in servertech_pdus:
                if hostname2 == master_hostname:
                    pdu = SERVERTECH_PDU(ip)
                    print "Trying to connect to " + ip
                    connected = pdu.spawn_ssh()
                    if connected:
                        print "Setting slave hostname for " + slave_hostname + ", which is connected to " + master_hostname
                        if args.set_hostname:
                            pdu.set_hostname(hostname, master)
                        pdu.logout()
                    else:
                        print "Can't connect to " + ip + ", check log."
                        continue

    print("Done")

    sys.exit(0)


if __name__ == "__main__":
    main()
