#!/usr/bin/env python3
# ===- all.py -------------------------------------------------------------===//
# *        _ _  *
# *   __ _| | | *
# *  / _` | | | *
# * | (_| | | | *
# *  \__,_|_|_| *
# *             *
# ===----------------------------------------------------------------------===//
#  Distributed under the MIT License.
#  SPDX-License-Identifier: MIT
# ===----------------------------------------------------------------------===//
"""
A simple utility which applies a standard "boilerplate" to an entire directory tree of files. Only
files whose names match one of a set of globbing patterns will be modified.
"""

from __future__ import print_function

import fnmatch
import glob
import itertools
import os
import sys

import boilerplate


def main():
    """
    Applies a standard "boilerplate" to an entire directory tree of files. Only files whose names
    match one of a set of globbing patterns will be modified.
    """

    base_path = os.getcwd()
    patterns = [
        '*.cmake',
        '*.cpp',
        '*.h',
        '*.hpp',
        '*.hpp.in',
        '*.js',
        '*.py',
        'CMakeLists.txt',
        'Doxyfile.in'
    ]

    # The collection of directories into which this utility will not descend.
    exclude_dirs = frozenset(itertools.chain(['.git', 'node_modules'], glob.iglob('build_*')))
    exclude_files = frozenset([])

    all_paths = []
    for root, dirs, files in os.walk(base_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for pattern in patterns:
            all_paths += [os.path.join(root, file_name) for file_name in files if
                          fnmatch.fnmatch(file_name, pattern) and file_name not in exclude_files]

    for path in all_paths:
        boilerplate.boilerplate_out(path=path, base_path=base_path, inplace=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
