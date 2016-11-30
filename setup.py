# !/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    "MySQL-python==1.2.5",
    "dnspython==1.15.0",
    "idna==2.1",
    "ipaddr==2.1.11",
    "psutil==2.1.3",
    "raven==5.27.1",
    "spoon==1.0.5",
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='se-rabl',
    version='0.1.0',
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
