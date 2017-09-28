# -*- coding: utf-8 -*-
import silverchain
from setuptools import setup, find_packages

long_description = """\
A fluent API generator.
See detail at http://github.com/tomokinakamaru/silverchain.
Copyright (c) 2017, Tomoki Nakamaru.
License: MIT
"""

setup(
    author='Tomoki Nakamaru',
    author_email='nakamaru@csg.ci.i.u-tokyo.ac.jp',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Code Generators'
    ],
    description='A fluent API generator',
    entry_points={'console_scripts': 'silverchain = silverchain.cli:main'},
    install_requires=[
        'networkx==1.11',
        'pyparsing==2.2.0'
    ],
    license='MIT',
    long_description=long_description,
    name='silverchain',
    packages=find_packages(),
    platforms='any',
    url='http://github.com/tomokinakamaru/silverchain',
    version='0.2.0'
)
