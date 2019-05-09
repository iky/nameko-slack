#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup


setup(
    name="nameko-slack",
    version="0.0.6",
    description="Nameko extension for interaction with Slack APIs",
    long_description=open("README.rst").read(),
    author="Ondrej Kohout",
    author_email="ondrej.kohout@gmail.com",
    url="http://github.com/iky/nameko-slack",
    packages=find_packages(exclude=["test", "test.*"]),
    install_requires=["nameko>=2.7.0", "slackclient>=1.0.4,<2"],
    extras_require={"dev": ["coverage", "pre-commit", "pylint", "pytest"]},
    dependency_links=[],
    zip_safe=True,
    license="Apache License, Version 2.0",
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
)
