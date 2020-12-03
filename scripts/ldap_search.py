#!/usr/bin/python

import ldap
ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
import os
import getpass
import sys
import re

# constants
OU_LOCATIONS = "ou=locations,dc=,dc="
LDAP_URI = "ldap://{uri}"

# LDAP helpers
def create_ldap_sess():
    """ Initialize and authenticate an LDAP session """
    ldap_sess = ldap.initialize(LDAP_URI)
    ldap_sess.start_tls_s()
    ldap_pw = check_password("LDAP password: ", "LDAP password again: ")
    ldap_user = "user={},ou=users,dc=,dc=".format(getpass.getuser())

    try:
        ldap_sess.simple_bind_s(ldap_user, ldap_pw)
    except ldap.INVALID_CREDENTIALS:
        print("Invalid LDAP password. Try again.")
        sys.exit()

    return ldap_sess

def search_ldap(site):
    """ Connect to the LDAP server and search for some location entries.

    Use regex or straight pattern matching in the options argument to
    match location entries with hostnames
    """
    print(site)
    regex_os_ccn_sql = site + "{compute}"
    ldap_sess = create_ldap_sess()
    locations = None
    matched_locations = []

    # Queries LDAP for the proper regex, returning a list of tuples
    # structured like: (location_dn, location_properties)
    locations = ldap_sess.search_s(OU_LOCATIONS, ldap.SCOPE_SUBTREE, '(objectClass=location)', ['parent','section','location','interface'])
    
    for dn, attr in locations:
        m = re.match(regex_os_ccn_sql, attr['location'][0])
        if m:
            print(m)
            matched_locations.append(attr['location'][0])
    
    ldap_sess.unbind_s()

    return matched_locations

def check_password(string1, string2):
    """ Checks if both typed passwords are the same. Else, ask again. """

    mismatch = True
    password1=password2 = ""
    while mismatch == True:
        password1 = getpass.getpass(string1)
        password2 = getpass.getpass(string2)
        if password1 == password2:
            mismatch = False
        else:
            print("Password mismatch. Try again.")
    return password1

def create_host_file(matched_locations):
    """ Creates a text file from the matched list of locations """

    with open('hosts.txt', 'w') as f:
        for location in matched_locations:
            print >> f, location

    f.close()

def main():

    #print(os.environ['site'])
    matched_locations = search_ldap(os.environ["site"])

    print(matched_locations)

    create_host_file(matched_locations)

    sys.exit(0)

if __name__=="__main__":
    main()
