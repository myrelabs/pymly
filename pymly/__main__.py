# Copyright 2024, EMCORE Sp. z o.o.
# SPDX-License-Identifier: MIT

import argparse
import sys

from .process import process_file, process_stream


def main():
    parser = argparse.ArgumentParser('pymly')
    parser.add_argument('input', help="Input file.", default='-', nargs='?')
    parser.add_argument('--verbose',
                        '-v',
                        help="Verbose output. Includes i.a. processed Python input.",
                        default=False,
                        action='store_true')
    parser.add_argument('--encoding', help="Change input file encoding; see Python builtin 'open'.")

    args = parser.parse_args()

    if args.input == '-':
        process_stream(sys.stdin, {'__file__': args.input})
    else:
        process_file(args.input)


if __name__ == '__main__':
    main()
