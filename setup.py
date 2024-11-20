# -*- coding: utf-8 -*-
# Copyright (c) 2013-2022 The tektronix developers. All rights reserved.
# Project site: https://github.com/questrail/tektronix
# Use of this source code is governed by a MIT-style license that
# can be found in the LICENSE.txt file for the project.
"""Dynamic setup file."""

# Standard module imports
import codecs
import os
import re

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """Read parts of a file

    Taken from pip's setup.py
    intentionally *not* adding an encoding option to open
    see: https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    """
    return codecs.open(os.path.join(here, *parts), "r").read()


def find_version(*file_paths):
    """Find version in source file

    Read the version number from a source file.
    Code taken from pip's setup.py
    """
    version_file = read(*file_paths)
    # The version line must have the form:
    # __version__ = 'ver'
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setuptools.setup(
    name="tektronix",
    version=find_version("src", "tektronix", "__init__.py"),
    author="Matthew Rankin",
    author_email="matthew@questrail.com",
    description="Package for working with Keysight/Agilent/HP test equipment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/questrail/tektronix",
    project_urls={
        "Bug Tracker": "https://github.com/questrail/tektronix/issues",
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.9",
    requires=["numpy (>=1.6.0)"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
