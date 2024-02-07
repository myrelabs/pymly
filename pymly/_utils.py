# Copyright 2024, EMCORE Sp. z o.o.
# SPDX-License-Identifier: MIT

from functools import singledispatch
from typing import Any, Dict, List, Optional, Union

ParentType = Optional[Union[Dict, List]]
KeyType = Optional[Union[str, int]]


@singledispatch
def deep_format(obj: Any, globals: Dict[str, Any], parent: ParentType = None, key: KeyType = None):
    """
    Run `str.format_map(globals)` on all leaf strings within `obj`,
    traversing dicts and lists. Modifies the object in-place if possible
    and returns the final, modified value (e.g. if provided with a string,
    returns just the new string).
    """
    # skip other data types
    return obj


@deep_format.register
def _(obj: dict, globals: Dict[str, Any], parent: ParentType = None, key: KeyType = None):
    for k, v in obj.items():
        deep_format(v, globals, obj, k)
    return obj


@deep_format.register
def _(obj: list, globals: Dict[str, Any], parent: ParentType = None, key: KeyType = None):
    for k, v in enumerate(obj):
        deep_format(v, globals, obj, k)
    return obj


@deep_format.register
def _(obj: str, globals: Dict[str, Any], parent: ParentType = None, key: KeyType = None):
    obj = obj.format_map(globals)
    if parent is not None:
        parent[key] = obj
    return obj


def _deep_split_split(_str: str, sep: str):
    return tuple(p.strip() for p in _str.split(sep))


@singledispatch
def deep_split(obj: Any, parent: ParentType = None, key: KeyType = None, sep=','):
    """
    Split all leaf strings within `obj` by `sep`, attempting to modify them in-place.
    The function recursively traverses all dicts and lists and the results
    are re-inserted as tuples s.t. they can still be used as dictionary keys.

    E.g.: deep_split({
        'foo, 17': ['a,b,c', 'd,e,f']
    }) = {
        ('foo', '17'): [('a', 'b', 'c'), ('d', 'e', 'f')]
    }
    """
    # skip other data types
    return obj


@deep_split.register
def _(obj: dict, parent: ParentType = None, key: KeyType = None, sep=','):
    for k, v in list(obj.items()):
        if ',' in k:
            tmp = _deep_split_split(k, sep)
            del obj[k]
            obj[tmp] = v
            k = tmp
        deep_split(v, obj, k, sep)
    return obj


@deep_split.register
def _(obj: list, parent: ParentType = None, key: KeyType = None, sep=','):
    for k, v in enumerate(obj):
        deep_split(v, obj, k, sep)
    return obj


@deep_split.register
def _(obj: str, parent: ParentType, key: KeyType, sep=','):
    if ',' in obj:
        obj = _deep_split_split(obj, sep)
        if parent is not None:
            parent[key] = obj
    return obj
