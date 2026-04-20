from setuptools import setup
import subprocess
import re
from packaging.tags import sys_tags
import os

tag = next(sys_tags())

setup(
    name = 'mstx',
    version = os.environ.get('WHL_VERSION', '26.0.0'),
    author =' mstx',
    author_email = 'mstx',
    description = 'mstx',
    long_description = open('README.md', encoding='utf-8').read(),
    long_description_content_type = 'text/markdown',
    url = 'https://gitcode.com/Ascend/mstx',
    options={
        'bdist_wheel':{
            'plat_name': tag.platform}},
    packages = ['lib64', 'include'],
    include_package_data = True,
    license= 'MIT',
    classifiers = [
        'Programming Language :: Python :: 3',
        'Operating System :: Linux',
    ],
    python_requires = '>=3.7'
)
