#! /usr/bin/env python

#TODO: Check to see if email tag exists, if so skip it

import boto3
import sys
import ldap
ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
import os
import getpass

# constants
LDAP_URI = "ldap://ldapmaster.battle.net"
OU_USERS = "ou=users,dc=battle,dc=net"

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

def search_ldap():
    """ Connect to the LDAP server and search for some location entries.
    Use regex or straight pattern matching in the options argument to
    match location entries with hostnames
    """
    ldap_sess = create_ldap_sess()
    locations = None

    # Queries LDAP for the proper regex, returning a list of tuples
    # structured like: (users_dn, users_properties)
    ldap_users = ldap_sess.search_s(OU_USERS, ldap.SCOPE_SUBTREE, '(objectClass=user)', ['user','email'])
    
    ldap_sess.unbind_s()

    return ldap_users

def tag_user(iam, user, email):
    """ Add an email key/value tag to the users IAM account """
    try:
        response = iam.tag_user(
            UserName=user,
            Tags=[
                {
                    'Key': 'Email',
                    'Value': email
                },
            ]
        )
        print(response)
    except Exception as e:
        print(e)

def get_user_tags(iam, user):
    """ Get current user tags """
    try:
        response = iam.list_user_tags(
        UserName = user
        )
        print(response['Tags'])
        if response['Tags']:
            return True
        else:
            return False
    except Exception as e:
        print(e)

def main():

    iam = boto3.client('iam')
    response = iam.list_users(MaxItems=800)
    iam_usernames = []
    for user in response['Users']:
        iam_usernames.append(user['UserName'])

    matched_users = search_ldap()

    ldap_users ={}
    for dn, attr in matched_users:
        ldap_users.update({attr['user'][0] : attr['email'][0]})

    missing_users = set(iam_usernames) - set(ldap_users.keys())
    existing_users = set(iam_usernames) & set(ldap_users.keys())

    for username in ldap_users:
        if username in existing_users:
            if get_user_tags(iam, username) == False:
                print("Tagging {0}".format(username))
                tag_user(iam, username, ldap_users[username])
            else:
                print("{0} already has email tag.".format(username))

    print("IAM Users that are not currently in LDAP: {0}".format(missing_users))
    print("Users that exist in both IAM and LDAP: {0}".format(existing_users))

    return

if __name__ == '__main__':
    sys.exit(main())
