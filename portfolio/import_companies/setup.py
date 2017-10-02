# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('../../README.md') as f:
    readme = f.read()

with open('../../LICENSE') as f:
    license = f.read()

setup(
    name='import_companies',
    version='0.1.0',
    description='Import Companies into a new or existent Portfolio',
    long_description=readme,
    author='Javier Alperte',
    author_email='alperte@preseries.com',
    url='https://github.com/preseries/api_examples',
    license=license,
    packages=find_packages('src', exclude=('tests', 'docs')),
    install_requires=[
        'openpyxl==2.4.8',
        'python-Levenshtein==0.12.0',
        'requests==2.18.4',
        'xlrd==1.1.0',
        'xlwt==1.3.0'
    ]
)