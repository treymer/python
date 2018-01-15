#! /usr/bin/python3
# pw.py - An insecure password locker program

import sys
import pyperclip

PASSWORDS = {'email': 'F83Mhdiwn728eEHDUm38DE8e00281',
             'blog': 'B0389f8Sjd7402mdyenm276s',
             'luggage': '12345'}

if len(sys.argv) < 2:    # the first sys.argv is the ./pw.py
    print ('Usage: python pw.py [account] - copy account password')
    sys.exit()

account = sys.argv[1]    # first command line arg is the account name

#print(sys.argv[0])

if account in PASSWORDS:
    pyperclip.copy(PASSWORDS[account])
    print ('Password for ' + account + ' copied to clipboard.')
else:
    print ('There is no account named ' + account + '.')
