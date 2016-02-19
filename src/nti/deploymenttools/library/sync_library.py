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

reverse_site_map = {
    'alpha.nextthought.com': 'alpha.nextthought.com',
    'augsfluoroscopy-alpha.nextthought.com': 'augsfluoroscopy.nextthought.com',
    'beta.nextthought.com': 'alpha.nextthought.com',
    'columbia-alpha.nextthought.com': 'columbia.nextthought.com',
    'connect-alpha.nextthought.com': 'connect.nextthought.com',
    'demo-alpha.nextthought.com': 'demo.nextthought.com',
    'ihs-alpha.nextthought.com': 'ihs.nextthought.com',
    'k20-alpha.nextthought.com': 'k20.nextthought.com',
    'litworld-alpha.nextthought.com': 'litworld.nextthought.com',
    'mathcounts-alpha.nextthought.com': 'mathcounts.nextthought.com',
    'oc-alpha.nextthought.com': 'oc.nextthought.com',
    'okstate-alpha.nextthought.com': 'okstate.nextthought.com',
    'ou-alpha.nextthought.com': 'platform.ou.edu',
    'prmia-alpha.nextthought.com': 'prmia.nextthought.com',
    'spurstartup-alpha.nextthought.com': 'spurstartup.nextthought.com',
    'symmys-alpha.nextthought.com': 'symmys.nextthought.com',
    'augsfluoroscopy-test.nextthought.com': 'augsfluoroscopy.nextthought.com',
    'columbia-test.nextthought.com': 'columbia.nextthought.com',
    'connect-test.nextthought.com': 'connect.nextthought.com',
    'demo-test.nextthought.com': 'demo.nextthought.com',
    'ihs-test.nextthought.com': 'ihs.nextthought.com',
    'k20-test.nextthought.com': 'k20.nextthought.com',
    'litworld-test.nextthought.com': 'litworld.nextthought.com',
    'mathcounts-test.nextthought.com': 'mathcounts.nextthought.com',
    'oc-test.nextthought.com': 'oc.nextthought.com',
    'okstate-test.nextthought.com': 'okstate.nextthought.com',
    'ou-test.nextthought.com': 'platform.ou.edu',
    'prmia-test.nextthought.com': 'prmia.nextthought.com',
    'spurstartup-test.nextthought.com': 'spurstartup.nextthought.com',
    'symmys-test.nextthought.com': 'symmys.nextthought.com',
    'augsfluoroscopy.nextthought.com': 'augsfluoroscopy.nextthought.com',
    'columbia.nextthought.com': 'columbia.nextthought.com',
    'connect.nextthought.com': 'connect.nextthought.com',
    'demo.nextthought.com': 'demo.nextthought.com',
    'ihs.nextthought.com': 'ihs.nextthought.com',
    'janux.ou.edu': 'platform.ou.edu',
    'k20.nextthought.com': 'k20.nextthought.com',
    'lab.symmys.com': 'symmys.nextthought.com',
    'learnonline.okstate.edu': 'okstate.nextthought.com',
    'litworld.nextthought.com': 'litworld.nextthought.com',
    'mathcounts.nextthought.com': 'mathcounts.nextthought.com',
    'oc.nextthought.com': 'oc.nextthought.com',
    'okstate.nextthought.com': 'okstate.nextthought.com',
    'platform.ou.edu': 'platform.ou.edu',
    'prmia.nextthought.com': 'prmia.nextthought.com',
    'spurstartup.nextthought.com': 'spurstartup.nextthought.com',
    'symmys.nextthought.com': 'symmys.nextthought.com'
}

def sync_library(host, user, password, flags):
    def _resolve_object(ntiid, host, auth):
        url = 'https://%s/dataserver2/Objects/%s' % (host, ntiid)
        headers = {
            'user-agent': 'NextThought Library Sync Utility'
        }

        try:
            response = requests.get(url, headers=headers, auth=auth)
            response.raise_for_status()
            _o = response.json()
        except requests.HTTPError as e:
            print(url)
            print(e)
            logger.warning('Unable to resolve %s' % ntiid)
            _o = { 'NTIID': ntiid, 'title': ntiid }
        return _o

    def _get_object(href, host, auth):
        url = 'https://%s%s' % (host, href)
        headers = {
            'user-agent': 'NextThought Library Sync Utility'
        }

        try:
            response = requests.get(url, headers=headers, auth=auth)
            response.raise_for_status()
            _o = response.json()
        except requests.HTTPError as e:
            print(url)
            print(e)
            logger.warning('Unable retrieve object at %s' % url)
            _o = { 'href': href }
        return _o

    def _analyze_site(site, host, auth):
        message = u"\n"
        if site['Added'] is not None:
            message += u"Courses Added:\n"
            for course in site['Added']:
                message += u"%s\n" % _resolve_object(course, host, auth)['title']
        if site['Modified'] is not None:
            message += u"Courses Modified:\n"
            for course in site['Modified']:
                message += u"%s\n" % _resolve_object(course, host, auth)['title']
        if site['Removed'] is not None:
            message += u"Courses Removed:\n"
            for course in site['Removed']:
                message += u"%s\n" % _resolve_object(course, host, auth)['title']
        return message

    def _analyze_response_body(response, status_code, host, auth):
        def _is_course_updated(course):
            non_booleans = [
                "Class",
                "Lessons",
                "MimeType",
                "NTIID",
                "Site"
            ]

            is_updated = False
            for key in course:
                if key not in non_booleans:
                    if course[key] is True:
                        is_updated = True
            if course['Lessons'] is not None:
                if course['Lessons']['LessonsUpdated'] is not []:
                    is_updated = True
            return is_updated

        if 'json' in response.headers['content-type']:
            if response.status_code == requests.codes.ok:
                results = response.json()['Results']['Items']
                _sites = []
                _courses = []
                _packages = []
                for result in results:
                    if result['Class'] == 'LibrarySynchronizationResults':
                        _sites.append(result)
                    elif result['Class'] == 'CourseSynchronizationResults':
                        if _is_course_updated(result):
                            _courses.append(result)
                    elif result['Class'] == 'ContentPackageSyncResults':
                        if not (result['AssessmentsUpdated'] == result['AssetsUpdated'] == None):
                            _packages.append(result)
                    else:
                        logger.warn('Unhandled type: %s' % result['Class'])
                for course in _courses:
                    for site in _sites:
                        if site['Name'] == course['Site']:
                            try:
                                course_entry = _resolve_object(course['NTIID'], host, auth)
                                for link in course_entry['Links']:
                                    if link['rel'] == 'CourseInstance':
                                        course_instance = _get_object(link['href'],host, auth)
                                for content_package in course_instance['ContentPackageBundle']['ContentPackages']:
                                    if content_package['NTIID'] in site['Modified']:
                                        site['Modified'].remove(content_package['NTIID'])
                                site['Modified'].append(course['NTIID'])
                            except AttributeError:
                                site['Modified'] = []
                                site['Modified'].append(course['NTIID'])
                            except TypeError:
                                site['Modified'] = []
                                site['Modified'].append(course['NTIID'])
                            except KeyError:
                                logger.warning(json.dumps(course_instance, indent=4, separators=(',', ': '), sort_keys=True))
                for site in _sites:
                    if (site['Added'] == site['Modified'] == site['Removed'] == None):
                        _sites.remove(site)
                return {'sites': _sites, 'courses': _courses, 'packages': _packages}
            else:
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
        'user-agent': 'NextThought Library Sync Utility'
    }

    body = {}
    body['requestTime'] = time()
    body['site'] = reverse_site_map[host]
    if flags['remove-content']:
        body['allowRemoval'] = 'true'

    logger.info('Syncing %s site-library on %s' % (reverse_site_map[host], host))
    try:
        response = requests.get(url, headers=headers, data=json.dumps(body), auth=(user, password))
        response_body = _analyze_response_body(response, response.status_code, host, (user, password))
        response.raise_for_status()
        if response.status_code == requests.codes.ok:
            if response_body['sites'] == []:
                logger.info('Dry-run sync of %s site-library succeeded. No changes detected. Exiting.' % reverse_site_map[host])
            elif flags['dry-run-only']:
                logger.info('Dry-run sync of %s site-library succeeded. The following changes were noted:' % reverse_site_map[host])
                logger.info(_analyze_site(response_body['sites'][0], host, (user, password)))
            else:
                logger.info('Dry-run sync of %s site-library succeeded. Performing real sync.' % reverse_site_map[host])
                response = requests.post(url, headers=headers, data=json.dumps(body), auth=(user, password))
                response_body = _analyze_response_body(response, response.status_code, host, (user, password))
                response.raise_for_status()
                if response.status_code == requests.codes.ok:
                    logger.info('Sync of %s site-library succeeded.' % reverse_site_map[host])
                    logger.info(_analyze_site(response_body['sites'][0], host, (user, password)))
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
