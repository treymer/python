#! /usr/bin/env python

import base64
import sys
import time
from pprint import pprint
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from googleapiclient.errors import HttpError

def peerUpdate(service):
    try:
        peering_request = service.networks().updatePeering(project=project, network=dev_network, body=networks_update_peering_request_body)
        peering_response = peering_request.execute()
        print("Peering update sent: {}".format(peering_response))
    except HttpError as err:
        if err.resp.status == 400:
            print("Object busy, trying again..")
            peerUpdate(service)

def main():
    credentials = GoogleCredentials.get_application_default()

    service = discovery.build('compute', 'v1', credentials=credentials)
    project = ''
    dev_network = ''
    try:
        request = service.networks().list(project=project)
        while request is not None:
            response = request.execute()
            for network in response['items']:
                for peer in network['peerings']:
                    print('{} export custom routes: {}'.format(peer['name'],peer['exportCustomRoutes']))
                    if peer['exportCustomRoutes'] is False and (peer['name'].startswith('gke-') or peer['name'].startswith('cloudsql-')):
                        networks_update_peering_request_body = {
                           "networkPeering": {
                               "name": peer['name'],
                               "exportCustomRoutes": True
                           }
                        }
                        peerUpdate(service)
                request = service.networks().list_next(previous_request=request, previous_response=response)
                pprint(request)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    sys.exit(main())
