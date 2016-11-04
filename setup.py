#!/usr/bin/env python
from setuptools import setup, find_packages

VERSION = '0.0'

entry_points = {
    'console_scripts': [
        'nti_sync_library = nti.deploymenttools.library.sync_library:main',
    ]
}

setup(
    name = 'nti.deploymenttools.library',
    version = VERSION,
    keywords = 'deployment tools',
    author = 'Sean Jones',
    author_email = 'sean.jones@nextthought.com',
    description = 'NextThought Platform Library Deployment Tools',
    long_description = 'Dataserver README',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers :: Education",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Framework :: Pylons :: ZODB :: Pyramid",
        "Internet :: WWW/HTTP",
        "Natural Language :: English",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    install_requires = [
        'setuptools',
        'dnspython',
        'requests',
    ],
    packages = find_packages( 'src' ),
    package_dir = {'': 'src'},
    namespace_packages=['nti', 'nti.deploymenttools'],
    zip_safe = False,
    entry_points = entry_points
    )
