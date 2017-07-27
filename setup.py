#!/usr/bin/env python

from setuptools import setup


setup(
    name='nameko-slack',
    version='0.0.3',
    description='Nameko extension for interaction with Slack APIs',
    author='Ondrej Kohout',
    author_email='ondrej.kohout@gmail.com',
    url='http://github.com/iky/nameko-slack',
    packages=['nameko_slack'],
    install_requires=[
        "nameko>=2.4.4",
        "slackclient>=1.0.4",
    ],
    extras_require={
        'dev': [
            "coverage",
            "flake8",
            "pylint",
            "pytest",
        ]
    },
    dependency_links=[],
    zip_safe=True,
    license='Apache License, Version 2.0',
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ]
)
