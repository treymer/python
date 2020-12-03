#! /usr/bin/env python

import boto3
import sys
import os
import getpass
from boto3.session import Session

def assume_role(arn, session_name, account_name):
    """aws sts assume-role --role-arn arn:aws:iam::00000000000000:role/example-role --role-session-name example-role"""

    count = 0
    print(account_name)
    client = boto3.client('sts')
    account_id = client.get_caller_identity()["Account"]
    print(account_id)
    session = ""
    
    try:
        response = client.assume_role(RoleArn=arn, RoleSessionName=session_name)
     
        session = Session(aws_access_key_id=response['Credentials']['AccessKeyId'],
                      aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                      aws_session_token=response['Credentials']['SessionToken'])
    
        client = session.client('sts')
        account_id = client.get_caller_identity()
        #print(account_id)
        print("Connected")
        print("--------------------------")
    except Exception as e:
        print(e)
        print("--------------------------")
        count += 1

    return count, session

def list_accounts():
    """ List accounts in org """

    client = boto3.client('organizations')
    paginator = client.get_paginator('list_accounts')
    response_iterator = paginator.paginate(
    PaginationConfig={
        'MaxItems': 123,
        'PageSize': 123,
        'StartingToken': 'string'
    }
)
    account_list = {}
    for page in paginator.paginate():
        for key, accounts in page.items():
            if key == "Accounts":
                for account in accounts:
                    account_id = ""
                    account_name = ""
                    for k, v in account.items():
                        if k == "Name":
                            account_name = v
                        if k == "Id":
                            account_id = v
                        if account_name != "" and account_id != "":
                            account_list.update({account_id : account_name})

    return account_list

def list_handshakes(arn, session_name, account_name):

    request_id = ""
    accepted = False

    count, session = assume_role(arn, session_name, account_name)

    if session != "":
        client = session.client('organizations')

        response = client.list_handshakes_for_account(
            Filter={
            'ActionType': 'APPROVE_ALL_FEATURES',
        },
        MaxResults=15)
        print("")
        for key, value in response.items():
            if key == "Handshakes":
                print(value)
                for item in value:
                    for k, v in item.items():
                        if k == "Id":
                            print(v)
                            request_id = v
                            accepted = accept_handshake(client, request_id)
        if accepted:
            print("Handshake accepted, all features enabled!")
        else:
            print("Handshake denied.")
    else:
        print("No access to {}".format(account_name))
        print("")
    return request_id

def accept_handshake(client, request_id):

    accepted = False
    try:
        response = client.accept_handshake(
        HandshakeId=request_id
    )
        accepted = True
    except Exception as e:
        print(e)
        print("Could not send handshake acception.")
    return accepted

def main():

    accounts = {}
    no_access_accounts = []
    no_access = 0
    filename = "accounts.txt"
    request_id = ""

    org_accounts = list_accounts()
    print("Organization accounts: {}".format(org_accounts))
    print("Number of accounts in org: {0}".format(len(org_accounts)))

    with open(filename) as f:
        for line in f:
            (value, key) = line.split()
            accounts[key] = value

    print(accounts)
    print("Ammount of accounts in list: " + str(len(accounts)) + "\n")

    missing_accounts = set(org_accounts.keys()) - set(accounts.keys())
    print("Accounts that exist in AWS that are not in Confluence:")
    print(missing_accounts)
    for account in missing_accounts:
        if account in org_accounts:
            print("{0} {1}".format(org_accounts[account], account))
    print("")
    for account_id, account_name in accounts.items():
        count, session = assume_role("arn:aws:iam::{}:role/{role}".format(account_id), "session_share", account_name)
        request_id = list_handshakes("arn:aws:iam::{}:role/{role}".format(account_id), "session_share", account_name)
        if count > 0:
            no_access += 1
            no_access_accounts.append(account_name)

    print("Accounts we cannot access: {0} {1}".format(no_access, no_access_accounts))

if __name__ == '__main__':
    sys.exit(main())
