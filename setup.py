"""
Flask-ErrorsHandler
-------------------
"""
import os
import re
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test

BASE_PATH = os.path.dirname(__file__)
VERSION_FILE = os.path.join('flask_errors_handler', 'version.py')


def read(file):
    with open(os.path.join(BASE_PATH, file)) as f:
        return f.read()


def grep(file, name):
    strval, = re.findall(fr"{name}\W*=\W*'([^']+)'", read(file))
    return strval


def readme(file):
    try:
        return read(file)
    except OSError as exc:
        print(str(exc), file=sys.stderr)


class PyTest(test):
    def finalize_options(self):
        test.finalize_options(self)

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(['tests']))


setup(
    name='Flask-ErrorsHandler',
    version=grep(VERSION_FILE, '__version__'),
    url='https://github.com/cs91chris/flask_errors_handler',
    license='MIT',
    author=grep(VERSION_FILE, '__author_name__'),
    author_email=grep(VERSION_FILE, '__author_email__'),
    description='Customizable errors handler for flask application and blueprints',
    long_description=readme('README.rst'),
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask >= 1.0.4',
    ],
    tests_require=[
        'pytest >= 5',
        'pytest-cov >= 2'
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
