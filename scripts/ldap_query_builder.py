#!/usr/bin/env python

# Purpose: Build an LDAP query for Apache from excel column
# Author: Tyler Reymer
# Date: 5/17/2019

import sys
import getpass
import xlrd

USER = getpass.getuser()

def main():

    book = xlrd.open_workbook("/home/" + USER + "/ldap_query.xlsx")
    first_sheet = book.sheet_by_index(0)
    number_of_rows = first_sheet.nrows
    row_one = first_sheet.row_values(0)
    
    f = open("ldap_query.txt", "w")
    sys.stdout = f

    print("(|")

    for i in range (1, number_of_rows):
        next_row = first_sheet.row_values(i)
        device = ""
        for key, value in zip(row_one,next_row):
            if key == "device":
                device = str(value)
        print("(device=" + device + ")")

    print(")")
    f.close()
    sys.stdout = sys.__stdout__
    
    print("Done")

    sys.exit(0)

if __name__ == "__main__":
    main()
