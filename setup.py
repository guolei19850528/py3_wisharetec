#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
=================================================
作者：[郭磊]
手机：[15210720528]
Email：[174000902@qq.com]
Github：https://github.com/guolei19850528/py3_wisharetec
=================================================
"""

import setuptools
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()
setup(
    name="py3-wisharetec",
    version="1.1.1",
    description="The Python3 Wisharetec Library Developed By Guolei",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/guolei19850528/py3_wisharetec",
    author="guolei",
    author_email="174000902@qq.com",
    license="MIT",
    keywors=["wisharetec", "慧享科技", "绿城", "物业管理", "物管", "智慧社区", "智慧社区全域服务平台","guolei","郭磊"],
    packages=setuptools.find_packages('./'),
    install_requires=[
        "py3-requests",
        "addict",
        "retrying",
        "jsonschema",
        "diskcache",
        "redis",
    ],
    python_requires='>=3.0',
    zip_safe=False
)
