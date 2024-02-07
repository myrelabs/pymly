# Copyright 2024, EMCORE Sp. z o.o.
# SPDX-License-Identifier: MIT

from ._utils import deep_format, deep_split
from .process import process_stream, process_file

__version__ = '0.1a'

__all__ = (
    'deep_format',
    'deep_split',
    'process_stream',
    'process_file',
)
