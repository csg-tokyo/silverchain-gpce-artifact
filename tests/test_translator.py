# -*- coding: utf-8 -*-
from silverchain.translator import translate


def test_translate():
    text = """
    START = idoc ;
    idoc -> list* ;
    list -> "begin" item+ "end" ;
    item -> text list? ;
    text@java : "String" ;
    EVAL@java = "Eval.evaluate(context);" ;
    """
    translate(text, 'java')
