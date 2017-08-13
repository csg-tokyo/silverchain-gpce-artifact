# -*- coding: utf-8 -*-
from importlib import import_module
from pkgutil import walk_packages


languages = []
for _, name, _ in sorted(walk_packages(__path__)):
    if '_encoder' in name:
        lang = name.split('_', 1)[0]
        languages.append(lang)


def get_encode_func(lang):
    name = '{}.{}_encoder'.format(__name__, lang)
    module = import_module(name)
    return module.encode
