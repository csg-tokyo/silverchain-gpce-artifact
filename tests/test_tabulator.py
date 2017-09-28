# -*- coding: utf-8 -*-
from textwrap import dedent
from silverchain.parser import parse
from silverchain.tabulator import tabulate as _tabulate


def tabulate(text):
    grammar = parse(text, 'java')
    return _tabulate(grammar)


def test_tabulate_1():
    text = """
    START = idoc ;
    idoc -> list* ;
    list -> "begin" item+ "end" ;
    item -> text list? ;
    text@java : "String" ;
    EVAL@java = "Eval.evaluate(context);" ;
    """

    tablestr = dedent("""
    START = idoc
    EVAL = "Eval.evaluate(context);"
    idoc[0]*  -list->  idoc[0]*
    item[0]  -text(String)->  item[1]*
    item[1]*  -list->  item[2]*
    list[0]  -"begin"->  list[1]
    list[1]  -item->  list[2]
    list[2]  -item->  list[2]
    list[2]  -"end"->  list[3]*
    """)

    assert str(tabulate(text)).strip() == tablestr.strip()
