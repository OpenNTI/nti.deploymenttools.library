#!/usr/bin/env python

from __future__ import unicode_literals, print_function

from getpass import getpass
from time import time

import argparse
import json
import requests

import logging
logger = logging.getLogger('nti.deploymenttools.library')
logger.setLevel(logging.INFO)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s'))
log_handler.setLevel(logging.INFO)
logger.addHandler(log_handler)
logging.captureWarnings(True)

def sync_library(host, user, password, flags):
    def _analyze_response(response):
        #    print(json.dumps(response.json(), indent=4, separators=(',', ': '), sort_keys=True))
        pass

    def _analyze_response_body(response, status_code):
        if 'json' in response.headers['content-type']:
            if response.status_code == requests.codes.ok:
                results = response.json()['Results']['Items']
                _sites = []
                _courses = []
                for result in results:
                    if result['Class'] == 'LibrarySynchronizationResults':
                        if not (result['Added'] == result['Modified'] == result['Removed'] == None):
                            _sites.append(result)
                    elif result['Class'] == 'CourseSynchronizationResults':
                        _courses.append(result)
                return {'sites': _sites, 'courses': _courses}
            else:
#                print(json.dumps(response.json(), indent=4, separators=(',', ': '), sort_keys=True))
                return(response.json())
        else:
            if status_code == requests.codes.unauthorized:
                return {'message': 'Unknown user or incorrect password.'}
            elif status_code == requests.codes.bad_gateway:
                return {'message': 'The server is returning garbage. Please try again later.'}
            elif status_code == requests.codes.service_unavailable:
                return {'message': 'The server is down. Please try again later.'}
            elif status_code == requests.codes.gateway_timeout:
                return {'message': 'The server took too long to respond. The sync is still running, however you will have to splunk for the result.'}
            else:
                return {'message': 'Unknown error %s occurred' % status_code}

    url = 'https://%s/dataserver2/@@SyncAllLibraries' % host
    headers = {
        'Content-Type': 'application/json',
        'user-agent': 'NextThought Library Sync Utility',
        'X-Requested-With': 'XMLHttpRequest'
    }

    body = {}
    body['requestTime'] = time()
    if flags['remove-content']:
        body['allowRemoval'] = 'true'

    logger.info('Syncing %s libraries' % host)
    try:
        response = requests.get(url, headers=headers, data=json.dumps(body), auth=(user, password))
        response_body = _analyze_response_body(response, response.status_code)
        response.raise_for_status()
        if response.status_code == requests.codes.ok:
            if flags['dry-run-only']:
                logger.info('Dry-run sync of %s libraries succeeded. Exiting.' % host)
            else:
                logger.info('Dry-run sync of %s libraries succeeded. Performing real sync.' % host)
                response = requests.post(url, headers=headers, data=json.dumps(body), auth=(user, password))
                response_body = _analyze_response_body(response, response.status_code)
                response.raise_for_status()
                if response.status_code == requests.codes.ok:
                    logger.info('Sync of %s libraries succeeded.' % host)
    except requests.HTTPError:
        logger.error(response_body['message'])

def _parse_args():
    # Parse command line args
    arg_parser = argparse.ArgumentParser( description="Content Library Mangement Utility" )
    arg_parser.add_argument( '-s', '--server', dest='host', 
                             help="The server to be synced." )
    arg_parser.add_argument( '-u', '--user', dest='user', 
                             help="User to authenticate with the server." )
    arg_parser.add_argument( '--password', dest='password', default=None,
                             help="User password. This option should only be used when calling this utility via a script." )
    arg_parser.add_argument( '--remove-content', dest='remove_content', action='store_true', 
                             help="Flag to permit the sync to remove content from the server." )
    arg_parser.add_argument( '--dry-run', dest='dry_run', action='store_true', 
                             help="Test sync the server." )
    return arg_parser.parse_args()

def main():
    args = _parse_args()

    flags = {}
    flags['remove-content'] = args.remove_content
    flags['dry-run-only'] = args.dry_run

    password = args.password
    if password is None:
        password = getpass('Password for %s: ' % args.user)

    sync_library(args.host, args.user, password, flags)

if __name__ == '__main__': # pragma: no cover
        main()
