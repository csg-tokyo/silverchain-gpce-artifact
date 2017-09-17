# -*- coding: utf-8 -*-
import os
import sys
from argparse import Action, ArgumentParser, FileType

__version__ = '0.1.0'


def main():
    from . import encoders, hooks, translator
    aparser = ArgumentParser(description='Fluent API generator')
    aparser.add_argument('l', type=str, choices=encoders.languages,
                         help='output language')
    aparser.add_argument('-i', metavar='FILE', type=FileType('r'),
                         default=sys.stdin, help='input grammar')
    aparser.add_argument('-o', metavar='DIR', action=OutdirAction,
                         default=os.getcwd(), help='output directory')
    aparser.add_argument('-v', action='version',
                         version='silverchain {}'.format(__version__))

    args = aparser.parse_args()
    files = translator.translate(
        args.i.read(),
        args.l,
        hooks.post_parse,
        hooks.post_tabulate
    )

    for name, content in files.items():
        fpath = os.path.join(args.o, name)
        with open(fpath, 'w') as f:
            f.write(content)


class OutdirAction(Action):
    def __init__(self, *args, **kwargs):
        super(OutdirAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, value, option_string):
        if not os.path.exists(value):
            raise Exception('{} does not exist.'.format(value))
        if not os.path.isdir(value):
            raise Exception('{} is not a directory.'.format(value))
        setattr(namespace, 'o', value)
