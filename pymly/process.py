# Copyright 2024, EMCORE Sp. z o.o.
# SPDX-License-Identifier: MIT

import ast
import os
import sys
import yaml

from functools import singledispatch
from typing import Any, Dict

try:
    from yaml import CLoader as default_loader
except ImportError:
    from yaml import Loader as default_loader

if sys.version_info >= (3, 12):
    from collections.abc import Buffer
else:
    from collections.abc import ByteString as Buffer


@singledispatch
def process_stream(f, g: Dict[str, Any] = None, **kwargs):
    """
    Process file or string or buffer `f` as pyml file.
    """
    return process_stream(f.read(), g, **kwargs)


@process_stream.register
def _(f: Buffer, g: Dict[str, Any] = None, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    return process_stream(f.decode(encoding), g, **kwargs)


@process_stream.register
def _(f: str, g: Dict[str, Any] = None, **kwargs):
    Loader = kwargs.get('Loader', default_loader)
    verbose = kwargs.get('verbose', False)

    if g is None: g = {}
    y = yaml.load(f, Loader=Loader)
    if y is None:
        y = {}
    elif isinstance(y, list):
        y = dict(enumerate(y))
    elif not isinstance(y, dict):
        raise ValueError(f"Root YAML object must be a list, a dict or null; got {type(y)}.")
    g |= y
    g['__root__'] = g

    def cexec():
        try:
            filename = g['__file__']
        except KeyError:
            filename = f'<pyml:{stmtline}>'
        try:
            cast = ast.parse(stmt, filename, mode='exec')
        except SyntaxError as e:
            e.lineno += stmtline - 1
            e.text = stmt  # override the file line
            raise
        ast.increment_lineno(cast, stmtline - 1)
        code = compile(cast, filename, mode='exec')
        exec(code, g)

    stmt = ""
    skip = 0
    stmtline = 0
    currline = 0
    for line in f.splitlines():
        currline += 1
        if line.startswith("#!>"):
            if stmt: cexec()
            tmp = line[3:].lstrip()
            skip = len(line) - len(tmp)
            tmp = tmp.rstrip()
            stmt = (tmp + "\n")
            stmtline = currline
            if verbose: print("#!>", tmp)
        elif line.startswith("#!."):
            if not stmt:
                raise SyntaxError("#!. line preceeding any #!> line (no active statement to continue")
            tmp = line[skip:].rstrip()
            stmt += (tmp + "\n")
            if verbose: print("#!.", tmp)
    if stmt: cexec()

    del g['__root__']
    return g


def process_file(fname: str, g: Dict[str, Any] = None, **kwargs):
    if g is None: g = {}
    g['__file__'] = os.path.realpath(fname)
    encoding = kwargs.get('encoding', None)
    with open(fname, 'r', encoding=encoding) as f:
        g = process_stream(f, g, **kwargs)
    del g['__file__']
    return g
