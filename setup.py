# !/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = [
    "MySQL-python==1.2.5",
    "dnspython==1.16.0",
    "idna==2.8",
    "psutil==5.6.3",
    "sentry-sdk==0.10.2",
    "spoon==1.0.6",
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name="se-rabl",
    version="1.1.0",
    description="SpamExperts RABL",
    long_description=readme,
    author="SolarWinds",
    author_email="mail-plg-engineering@solarwinds.com",
    url="https://github.com/spamexperts/se-rabl",
    packages=["rabl"],
    scripts=["rabl/write_to_rbldnsd.py"],
    package_dir={"rabl": "rabl"},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords="rabl,spam,spamexperts",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    test_suite="tests",
    tests_require=test_requirements,
)
