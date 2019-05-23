"""
Flask-ErrorsHandler
-------------

Customizable errors handler for flask application and blueprints
"""
from setuptools import setup
from setuptools import find_packages

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name='Flask-ErrorsHandler',
    version='1.0.0',
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
