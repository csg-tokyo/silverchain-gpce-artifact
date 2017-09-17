# -*- coding: utf-8 -*-
import pytest
from silverchain.errors import *
from silverchain.translator import _parse


def test_parse_1():
    text = """
    # IDoc, DSL for itemized documents
    START = idoc ;
    idoc -> list* ;
    list -> "begin" item+ "end" ;
    item -> text list? ;
    text@java : "String" ;
    EVAL@java = "Eval.evaluate(context);" ;
    """
    _parse(text, 'java')


def test_parse_2():
    text = """
    START = A ;
    A -> "a" * ;
    B -> "b" + ;
    C -> "c" ? ;
    D -> "d" {1} ;
    E -> "e" {2,} ;
    F -> "f" {3,4} ;
    F -> "f" {6,7} ;
    """
    _parse(text, 'java')


def test_parse_err_1():
    text = """
    START = A ;
    A -> "a" {1,0} ;
    """
    pytest.raises(InvalidQuantifier, _parse, text, 'java')


def test_parse_err_2():
    text = """
    A -> "a" ;
    B -> "b" ;
    """
    pytest.raises(NoStartSymbol, _parse, text, 'java')


def test_parse_err_3():
    text = """
    START = A ;
    START = B ;
    A -> "a" ;
    B -> "b" ;
    """
    pytest.raises(MultipleStartSymbol, _parse, text, 'java')


def test_parse_err_4():
    text = """
    START = A ;
    A -> B ;
    B : "int" ;
    B : "String" ;
    """
    pytest.raises(MultipleTypeDefinition, _parse, text, 'java')


def test_parse_err_5():
    text = """
    START = A ;
    A -> "a" ;
    EVAL = "Eval1.evaluate();" ;
    EVAL@java = "Eval2.evaluate();" ;
    """
    pytest.raises(MultipleEvalCode, _parse, text, 'java')
