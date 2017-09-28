# -*- coding: utf-8 -*-
from . import core, encoders, parser, tabulator
from .data import Symbol


def translate(text, lang):
    grammar = parser.parse(text, lang)

    unexpanded = core.post_parse(grammar)
    unexpanded = {Symbol.nonterm(t.text) for t in unexpanded}

    grammar.validate()

    table = tabulator.tabulate(grammar)
    core.post_tabulate(table, unexpanded)

    encode_func = encoders.get_encode_func(lang)
    return encode_func(table)
