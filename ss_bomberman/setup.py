# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 20:22:26 2024

@author: nanashi
"""

from distutils.core import setup, Extension

setup (name = 'ss_bomberman_tools',
       version = '0.4',
       description = 'Sega Saturn Bomberman translation tools',
       packages=['ss_bomberman'],
       install_requires=['pillow'])