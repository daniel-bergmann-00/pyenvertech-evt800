#!/usr/bin/env python
"""pyevertechevt800 library setup."""

from pathlib import Path

from setuptools import setup

VERSION = "0.1.0"
URL = "https://github.com/daniel-bergmann-00/pyevertechevt800"

setup(
    name="pyevertechevt800",
    version=VERSION,
    description="Library to interface an Envertech EVT-800 device",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    url=URL,
    download_url="{}/tarball/{}".format(URL, VERSION),
    author="Daniel Bergmann",
    author_email="daniel.bergmann00+evertec_evt800@gmail.com",
    license="MIT",
    packages=["pyevertechevt800"],
    python_requires=">=3.9",
    install_requires=[],
    zip_safe=True,
)
