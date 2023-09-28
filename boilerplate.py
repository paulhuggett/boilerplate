#!/usr/bin/env python3
# ===- boilerplate.py -----------------------------------------------------===//
# *  _           _ _                 _       _        *
# * | |__   ___ (_) | ___ _ __ _ __ | | __ _| |_ ___  *
# * | '_ \ / _ \| | |/ _ \ '__| '_ \| |/ _` | __/ _ \ *
# * | |_) | (_) | | |  __/ |  | |_) | | (_| | ||  __/ *
# * |_.__/ \___/|_|_|\___|_|  | .__/|_|\__,_|\__\___| *
# *                           |_|                     *
# ===----------------------------------------------------------------------===//
#  Distributed under the MIT License.
#  SPDX-License-Identifier: MIT
# ===----------------------------------------------------------------------===//

"""
 A small utility tool to stamp boilerplate text onto source files. It uses
 the pyfiglet library to generate banner text (although this can be disabled).
"""

from typing import Optional
import argparse
import os.path
import re
import subprocess
import sys

# 3rd party
import pyfiglet

def strip_lines(lines, index, comment_str):
    """Removes leading and trailing comment lines from the file."""

    is_blank = lambda x: x == '' or x == '\n'

    # Remove blank lines
    while len(lines) > 0 and is_blank(lines[index]):
        del lines[index]

    # Remove comment lines.
    stop_str = comment_str + comment_str[0]
    is_deletable = lambda x: x.startswith(comment_str)
    while len(lines) > 0 and is_deletable(lines[index]) and not lines[index].startswith(stop_str):
        del lines[index]

    return lines


def strip_leading_and_trailing_lines(lines, comment):
    """
    Removes and leading and trailing blank lines and comments.

    :param lines: An array of strings containing the lines to be stripped.
    :param comment: The block comment character string.
    :return: An updated array of lines.
    """

    comment = comment.strip()
    return strip_lines(strip_lines(lines, 0, comment), -1, comment)


def remove_string_prefix(s:str, prefix:str) -> str:
    if s.startswith(prefix):
        s = s[len(prefix):]
    return s


def remove_string_suffix(s:str, suffix:str) -> str:
    if s.endswith(suffix):
        s = s[:-len(suffix)]
    return s


def split_extension(path:str) -> tuple[str,str]:
    """A wrapper around splitext() which will delete a '.in' extension. This convention is used for files
    being fed as the template file to cmake's configure_file() command; the resulting file has the same
    name but without the .in part."""

    result = os.path.splitext(path)
    if result[1] == '.in':
        result = os.path.splitext(result[0])
    return result


def tu_name_from_path(path:str) -> str:
    bn = os.path.basename(path)
    name = split_extension(bn)[0]
    name = remove_string_prefix(name, 'test_') # snake_case
    name = remove_string_prefix(name, 'Test') # CamelCase.
    name = remove_string_suffix(name, '_win32')
    name = remove_string_suffix(name, '_posix')

    if bn != 'CMakeLists.txt':
        # In CamelCase, a lower-to-upper transition is a space.
        name = re.sub (r'([a-z])([A-Z])', r'\1 \2', name)

    # In snake_case, an underscore is a space.
    return name.replace('_', ' ')


def figlet(name:str, comment_char:str) -> list[str]:
    out = pyfiglet.figlet_format(name)
    return [comment_char + '* ' + l + ' *' + '\n' for l in out.splitlines(False)]


LANGUAGE_MAPPING = {
    '.h': 'C++',
    '.hpp': 'C++',
}


def get_path_line(path:str, comment_char:str) -> list[str]:
    path_line_suffix = '===//'

    (_, ext) = split_extension(path)
    language = LANGUAGE_MAPPING.get (ext, '')
    if len(language) > 0:
        path_line_suffix = '*- mode: {0} -*-'.format (language) + path_line_suffix

    path_line = comment_char + '===- ' + path + ' '
    path_line += '-' * (80 - len(path_line) - len(path_line_suffix)) + path_line_suffix
    return [path_line + '\n']


def get_license(comment_char:str, license_text:list[str]) -> list[str]:
    out_lines = [comment_char + ' ' + l for l in license_text]
    return [l.rstrip(' ') for l in out_lines]


COMMENT_MAPPING = {
    '.cpp': '//',  # C++
    '.c': '//',    # C
    '.C': '//',    # C++
    '.cxx': '//',  # C++
    '.js': '//',   # JavaScript
    '.txt': '#',   # for CMake!
    '.h': '//',    # C/C++
    '.hpp': '//',  # C++
    '.py': '# ',   # Python
}


def boilerplate(path:str, base_path:str, license_text:list[str], 
                comment_char:Optional[str]=None, figlet_enabled:bool=True) -> list[str]:
    path = os.path.abspath(path)
    base_path = os.path.abspath(base_path)

    if comment_char is None:
        ext = split_extension(path)[1]
        comment_char = COMMENT_MAPPING.get(ext, '#')

    if not os.path.isdir(base_path):
        raise RuntimeError('base path must be a directory')

    if base_path[-1] != os.sep and base_path[-1] != os.altsep:
        base_path += os.sep

    if path[:len(base_path)] != base_path:
        raise RuntimeError('path (%s) was not inside base-path (%s)' % (path, base_path))

    subpath = path[len(base_path):]

    # files that are input to CMake's configure_files() sometimes end with 
    # '.in'. Remove them.
    if subpath.endswith('.in'):
        subpath = subpath[:-len('.in')]

    with open(path) as f:
        lines = f.readlines()

    shebang = lines[0] if len(lines) > 0 and lines[0].startswith ('#!') else None
    if shebang is not None:
        del lines[0]

    # Remove any leading and trailing blank lines and comments
    lines = strip_leading_and_trailing_lines(lines, comment_char)

    tu_name = tu_name_from_path(subpath)
    prolog = []
    if shebang is not None:
        prolog += [shebang]

    prolog += get_path_line(subpath, comment_char)

    line_of_dashes = comment_char + '===----------------------------------------------------------------------===//\n'
    if figlet_enabled:
        prolog += figlet(tu_name, comment_char)
        prolog += [ line_of_dashes ]

    prolog += get_license(comment_char, license_text)
    prolog += [ line_of_dashes ]
    return prolog + lines


def find_boilerplate ():
    # Start in the current directory and work up the tree from there.
    path = os.getcwd()
    while True:
        try:
            return open(os.path.join (path, ".boilerplate.txt"))
        except IOError:
            # Try again with the parent directory if there is one.
            newpath = os.path.abspath (os.path.join (path, os.path.pardir))
            if path == newpath:
                # We reached the top of the directory tree.
                raise
            path = newpath


def boilerplate_out(path:str, base_path:str, comment_char:Optional[str]=None, inplace:bool=False, figlet_enabled:bool=True) -> None:
    with find_boilerplate () as f:
        license_text = f.readlines() if f is not None else ["license text"]

    lines = boilerplate(path, base_path, license_text, comment_char, figlet_enabled)
    outfile = open(path, 'w') if inplace else sys.stdout
    for l in lines:
        print(l, end='', file=outfile)


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='Generate source file license boilerplate')
    parser.add_argument('source_file', help='The source file to be processed')
    parser.add_argument('--base-path', help='The base path to which path names are relative', default=os.getcwd())
    parser.add_argument('--comment-char', help='The character(s) used to begin a comment.')
    parser.add_argument('--no-figlet',
                        help='Disables generation of the TU banner name (using the external "figlet" utility',
                        dest='figlet_enabled', action='store_false')
    parser.add_argument('-i', dest='inplace', action='store_true', help='Inplace edit file.')
    options = parser.parse_args(args)

    boilerplate_out(options.source_file, options.base_path, options.comment_char, options.inplace,
                    options.figlet_enabled)
    return 0


if __name__ == '__main__':
    sys.exit(main())
