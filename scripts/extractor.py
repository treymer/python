#!/usr/bin/env python3

from os.path import split
import sys
import os
import argparse
from ruamel.yaml import YAML     # Might need to pip install this
import tarfile

# Constants
YML_DIR = "ansible-openstack/inventory/"
YML_DIR_VARS = [
    "managed_vms/host_vars",
    "projects/host_vars",
    "projects/group_vars",
    "managed_vms/group_vars"

]
SG_RULES = "vm_openstack_security_group_rules"
SG_RULES_BULK = "vm_openstack_security_group_rules_bulk"
SG_RULES_KEYS = [
    "vm_openstack_security_group_rules_bulk",
    "vm_openstack_security_group_rules",
    "project_shared_security_groups",
    "domain_shared_security_groups",
    "vm_extra_security_groups"
]
ARCHIVE_YML = "host_var.tar"
CWD = os.getcwd()

### Helpers ###
def archive_yml(dir_list: list, path: str, tar) -> list:
    """ Create archive of current host_vars """
    print(f"Archiving {path} in {CWD}/{ARCHIVE_YML}")
    print(dir_list)
    for file in dir_list:
        print(f"Adding {file} to archive...")
        tar.add(YML_DIR + path + '/' + file)
    return dir_list

def write_yml(full_path: str, host_yaml: str):
    """ Write new yaml files """
    yaml=YAML()
    yaml.width = 800
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(full_path, 'w') as file:
        try:
            print(f"Writing new {full_path}")
            yaml.dump(host_yaml, file)
        except:
            print(f"Could not write {full_path}")
            print(sys.exc_info())

def get_directories(full_path: str) -> list:
    return os.listdir(full_path)

def delete_yml(file: str):
    """ Deletes existing yaml files in host_vars """
    file_path = CWD + '/' + YML_DIR + file
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted {file}")
    else:
        print(f"{file_path} does not exist...")
### eof Helpers ###

def remove_sgs(dir_list: list, path: str, tar):
    """ Archives existing host_vars dir, deletes both 
    SG_RULES_BULK and SG_RULES keys from yml, deletes
    current host_vars yamls, and finally writes new yamls 
    from host_yaml dir.
    """
    # Archive directory
    try:
        dir_list = archive_yml(get_directories(YML_DIR + path), path, tar)
    except:
        print(sys.exc_info())
        sys.exit("Could not archive directory - Exiting...")
    
    # Loop through each file in dir amd remove security group keys
    for file in dir_list:
        full_path = YML_DIR + path + '/' + file
        opened_file = False
        statinfo = os.stat(full_path)
        if statinfo.st_size > 0:
            try:
                yaml=YAML()
                yaml.width = 800
                yaml.preserve_quotes = True
                open_yaml = open(full_path, 'r')
                host_yaml = yaml.load(open_yaml)
                open_yaml.close()
                opened_file = True
            except:
                print(sys.exc_info())
                print(f"Could not open file {full_path} - Skipping")
                continue
            if opened_file:
                found_key = False
                for key in SG_RULES_KEYS:
                    if key in host_yaml:
                        found_key = True
                        print(f"Deleting - {key} in {full_path}") 
                        del host_yaml[key]
                    else:
                        print(f"Skipping - No {key} in {full_path}")
                if found_key:
                    try:
                        print(f"Security groups removed, deleting {file}")
                        delete_yml(path + '/' + file)
                    except:
                        print(f"Could not delete {file}")
                    try:
                        write_yml(full_path, host_yaml)
                    except:
                        print(f"Could not write new file for {file}")
                else:
                    host_yaml = None
                    print(f"Not writing/deleting new {file}")

def main():

    try:
        tar = tarfile.open(ARCHIVE_YML, "w")
        for path in YML_DIR_VARS:
            remove_sgs(get_directories(YML_DIR + path), path, tar)
        tar.close()
    except:
        print(sys.exc_info())

    print("Done...")

    return

if __name__ == '__main__':
    sys.exit(main())
