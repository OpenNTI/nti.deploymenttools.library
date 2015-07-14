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

    def _handle_error_code(response):
        if response.status_code == requests.codes.internal_server_error:
            _analyze_response(response)
            logger.error('The server had an error while syncing the libary.')
        else:
            logger.error('Sync of %s libraries failed' % host)
            if response.status_code == requests.codes.unauthorized:
                logger.error('Unknown user or incorrect password.')
            else:
                logger.error('Unknown error %s occurred' % response.status_code)

    url = 'https://%s/dataserver2/@@SyncAllLibraries' % host
    headers = {
        'Content-Type': 'application/json',
        'user-agent': 'nti-sync-tool',
        'X-Requested-With': 'XMLHttpRequest'
    }

    body = {}
    body['requestTime'] = time()
    if flags['remove-content']:
        body['allowRemoval'] = 'true'

    logger.info('Syncing %s libraries' % host)
    response = requests.get(url, headers=headers, data=json.dumps(body), auth=(user, password))

    if response.status_code == requests.codes.ok:
        _analyze_response(response)
        if flags['dry-run']:
            logger.info('Dry-run sync of %s libraries succeeded.' % host)
        else:
            response = requests.post(url, headers=headers, data=json.dumps(body), auth=(user, password))
            if response.status_code == requests.codes.ok:
                logger.info('Sync of %s libraries succeeded.' % host)
            else:
                _handle_error_code(response)
    else:
        _handle_error_code(response)

def _parse_args():
    # Parse command line args
    arg_parser = argparse.ArgumentParser( description="Content Library Mangement Utility" )
    arg_parser.add_argument( '-s', '--server', dest='host', 
                             help="The server to be synced." )
    arg_parser.add_argument( '-u', '--user', dest='user', 
                             help="User to authenticate with the server." )
    arg_parser.add_argument( '--remove-content', dest='remove_content', action='store_true', 
                             help="Flag to permit the sync to remove content from the server." )
    arg_parser.add_argument( '--dry-run', dest='dry_run', action='store_true', 
                             help="Test sync the server." )
    return arg_parser.parse_args()

def main():
    args = _parse_args()

    flags = {}
    flags['remove-content'] = args.remove_content
    flags['dry-run'] = args.dry_run

    password = getpass('Password for %s: ' % args.user)

    sync_library(args.host, args.user, password, flags)

if __name__ == '__main__': # pragma: no cover
        main()
