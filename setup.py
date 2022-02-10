#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 8):
    raise ValueError("Requires Python 3.8 or superior")

from ees_networkdrive import __version__  # NOQA

install_requires = [
    "requests_ntlm",
    "elastic_enterprise_search",
    "pyyaml",
    "tika",
    "ecs_logging",
    "cerberus",
    "pytest",
    "pysmb",
    "wcmatch",
    "pytest-cov",
    "cached_property"
]

description = ""

with open("README.rst") as readme_file:
    description += readme_file.read() + "\n\n"


classifiers = [
    "Programming Language :: Python",
    "Development Status :: 5 - Production/Stable",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
]


setup(
    name="ees-networkdrive",
    version=__version__,
    url="someurl",
    packages=find_packages(),
    long_description=description.strip(),
    description=("Some connectors"),
    author="author",
    author_email="email",
    include_package_data=True,
    zip_safe=False,
    classifiers=classifiers,
    install_requires=install_requires,
    data_files=[("config", ["network_drive_connector.yml"])],
    entry_points="""
      [console_scripts]
      ees_networkdrive = ees_networkdrive.cli:main
      """,
)
