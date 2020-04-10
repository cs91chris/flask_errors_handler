"""
Flask-ErrorsHandler
-------------
"""
import sys

import pytest
from setuptools import setup, find_packages
from setuptools.command.test import test

from flask_errors_handler import __author_info__, __version__

with open("README.rst") as fh:
    long_description = fh.read()


class PyTest(test):
    def finalize_options(self):
        """

        """
        test.finalize_options(self)

    def run_tests(self):
        """

        """
        sys.exit(pytest.main(['tests']))


setup(
    name='Flask-ErrorsHandler',
    version=__version__,
    url='https://github.com/cs91chris/flask_errors_handler',
    license='MIT',
    author=__author_info__['name'],
    author_email=__author_info__['email'],
    description='Customizable errors handler for flask application and blueprints',
    long_description=long_description,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask==1.1.*'
    ],
    tests_require=[
        'pytest==5.4.*',
        'pytest-cov==2.8.*'
    ],
    cmdclass={'test': PyTest},
    test_suite='tests',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
