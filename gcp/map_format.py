#!/usr/bin/env python
import collections

def main():
    TEXT_FILE = "master_product.txt"
    d = {}
    with open(TEXT_FILE) as f:
        for line in f:
           (key, val) = line.split('=',1)  # Change = to - for cost_centers.txt
           d[key.lower()] = val.lower().replace(' -', '').replace('&','and').strip('\n')
    for key, value in d.items():
        d[key] = value.replace(' ', '_').replace('(','').replace(')','').replace('-','_').replace('/','_')

    od = collections.OrderedDict(sorted(d.items()))

    for key, value in od.items():
        print "\"" + key + "\"" + " = " + "\"" + d[key] + "\","

if __name__ == "__main__":
    main()
