#!/usr/bin/env python3
from distutils.core import setup
import subprocess
import os

ver = os.environ.get("PKGVER") or subprocess.run(['git', 'describe', '--tags'],
      stdout=subprocess.PIPE).stdout.decode().strip()

setup(
  name = 'broca',
  packages = ['broca'],
  version = ver,
  description = 'bittorrent RPC babelfish',
  author = 'Drew DeVault',
  author_email = 'sir@cmpwn.com',
  url = 'https://git.sr.ht/~sircmpwn/broca',
  install_requires = ['srht', 'flask-login'],
  license = '3-Clause BSD',
  scripts = ['broca-daemon']
)
