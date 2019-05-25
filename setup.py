"""
Flask-ErrorsHandler
-------------

Customizable errors handler for flask application and blueprints
"""
import sys
import pytest

from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test

from flask_errors_handler import __version__
from flask_errors_handler import __author__


author, email = __author__.split()
email = email.lstrip('<').rstrip('>')

with open("README.rst", "r") as fh:
    long_description = fh.read()


class PyTest(test):
    def finalize_options(self):
        test.finalize_options(self)

    def run_tests(self):
        sys.exit(pytest.main(['tests']))


setup(
    name='Flask-ErrorsHandler',
    version=__version__,
    url='https://github.com/cs91chris/flask_errors_handler',
    license='MIT',
    author='cs91chris',
    author_email='cs91chris@voidbrain.me',
    description='Customizable errors handler for flask application and blueprints',
    long_description=long_description,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask==1.0.2'
    ],
    tests_require=[
        'pytest==4.5.0',
        'pytest-cov==2.7.1'
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
