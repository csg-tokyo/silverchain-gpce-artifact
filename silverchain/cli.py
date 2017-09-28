# -*- coding: utf-8 -*-
import os
import sys
from argparse import Action, ArgumentParser, FileType
from . import encoders, version
from . import translator


# Argument Action -------------------------------------------------------------
class _OutdirAction(Action):
    def __init__(self, *args, **kwargs):
        super(_OutdirAction, self).__init__(*args, **kwargs)
        self._dest = kwargs['dest']

    def __call__(self, parser, namespace, value, option_string):
        if not os.path.exists(value):
            raise Exception('{} does not exist.'.format(value))

        if not os.path.isdir(value):
            raise Exception('{} is not a directory.'.format(value))

        setattr(namespace, self._dest, value)


# Argument Parser -------------------------------------------------------------
_aparser = ArgumentParser(description='Fluent API generator')

_aparser.add_argument(
    'language',
    choices=encoders.languages,
    help='output language',
    type=str
)

_aparser.add_argument(
    '-i', '--input',
    default=sys.stdin,
    dest='input',
    help='input grammar',
    metavar='FILE',
    type=FileType('r')
)

_aparser.add_argument(
    '-o', '--output',
    action=_OutdirAction,
    default=os.getcwd(),
    dest='output',
    help='output directory',
    metavar='DIR'
)

_aparser.add_argument(
    '-v', '--version',
    action='version',
    version='silverchain {}'.format(version.__version__)
)


# Main ------------------------------------------------------------------------
def main():
    args = _aparser.parse_args()
    files = translator.translate(args.input.read(), args.language)
    for name, content in files.items():
        fpath = os.path.join(args.output, name)
        with open(fpath, 'w') as f:
            f.write(content)
