# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='preseries_api',
    version='0.1.0',
    description='Preseries API for Python & Examples',
    long_description=readme,
    author='Javier Alperte',
    author_email='alperte@preseries.com',
    url='https://github.com/preseries/api_examples',
    license=license,
    setup_requires=[],
    namespace_packages=['preseries'],
    packages=find_packages('src', exclude=['tests', 'docs']),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'openpyxl==2.4.8',
        'python-Levenshtein==0.12.0',
        'requests==2.18.4',
        'httplib2==0.10.3',
        'xlrd==1.1.0',
        'xlwt==1.3.0'
    ]
)