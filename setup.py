# !/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    "MySQL-python==1.2.5",
    "dnspython==1.16.0",
    "idna==2.8",
    "ipaddr==2.2.0",
    "psutil==5.4.8",
    "sentry-sdk==0.6.3",
    "spoon==1.0.6",
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='se-rabl',
    version='0.3.2',
    description="SpamExperts RABL",
    long_description=readme,
    author="SpamExperts B.V.",
    author_email='support@spamexperts.com',
    url='https://github.com/spamexperts/se-rabl',
    packages=[
        'rabl',
    ],
    scripts=[
        "rabl/write_to_rbldnsd.py"
    ],
    package_dir={'rabl':
                 'rabl'},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='rabl,spam,spamexperts',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
