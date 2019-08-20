#!/usr/bin/env python

from setuptools import setup, find_packages

def requirements():
    requirements = []
    with open('requirements.txt') as file:
        for line in file:
            requirements.append(line.strip())
    return requirements

setup(
    name='unimonapi',
    version='0.1.0',
    description='Universal monitoring API for different monitoring systems',
    author='Max Grechnev',
    author_email='max.grechnev@gmail.com',
    license='MIT',
    packages=find_packages(exclude=['tests*']),
    install_requires=requirements(),
    scripts=['bin/zabbix_cli.py'],
)
