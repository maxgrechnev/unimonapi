from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

def requirements():
    requirements = []
    with open('requirements.txt') as file:
        for line in file:
            requirements.append(line.strip())
    return requirements

setup(
    name='unimonapi',
    version='0.0.1',
    description='Universal API for different monitoring systems',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Max Grechnev',
    author_email='max.grechnev@gmail.com',
    license='MIT',
    url='https://github.com/maxgrechnev/unimonapi',
    packages=find_packages(exclude=['tests*']),
    install_requires=requirements(),
    scripts=['bin/zabbix_cli.py'],
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
