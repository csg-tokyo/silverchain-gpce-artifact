# -*- coding: utf-8 -*-
from pyparsing import alphas, nums, restOfLine
from pyparsing import Forward, Keyword, QuotedString, Word
from pyparsing import OneOrMore, Optional, Or, ZeroOrMore
from pyparsing import ParserElement
from .data import Grammar, Expr, Token
from .encoders import languages
from .errors import InvalidQuantifier
from .errors import MultipleEvalCode
from .errors import MultipleStartSymbol, NoStartSymbol
from .errors import MultipleTypeDefinition


# Parser Elements -------------------------------------------------------------
_nsym = Word(alphas)
_tsym = '"' + Word(alphas) + '"'
_type = QuotedString('"')
_ltag = '@' + Or(languages)

_uops = '{' + Word(nums) + Optional(',' + Optional(Word(nums))) + '}'
_uops = _uops | '*' | '+' | '?'
_expr = Forward()
_elem = _nsym | _tsym | '(' + _expr + ')'
_fact = _elem + Optional(_uops)
_term = OneOrMore(_fact)
_expr << _term + ZeroOrMore('|' + _term)

_sdef = Keyword('START') + '=' + _nsym
_prod = _nsym + '->' + _expr
_tdef = _nsym + Optional(_ltag) + ':' + _type
_edef = Keyword('EVAL') + Optional(_ltag) + '=' + QuotedString('"', '\\')
_cmnt = ('#' + restOfLine).suppress()
_rule = (_sdef | _prod | _tdef | _edef) + ';' + Optional(_cmnt)
_grammar = OneOrMore(_rule | _cmnt)


# Parse Actions ---------------------------------------------------------------
def _nsym_action(result):
    return result[0]


def _tsym_action(result):
    return ''.join(result)


def _type_action(result):
    return result[0]


def _ltag_action(result):
    return result[1]


def _uops_action(result):
    if result[0] == '*':
        return 0, float('inf')
    if result[0] == '+':
        return 1, float('inf')
    if result[0] == '?':
        return 0, 1

    n = int(result[1])
    if result[2] == '}':
        return n, n
    elif result[3] == '}':
        return n, float('inf')
    else:
        return n, int(result[3])


def _elem_action(result):
    return ' '.join(result).strip('()')


def _fact_action(result):
    elem, (n, m) = result[0], (result[1:2] or [(1, 1)])[0]
    if m < n:
        raise InvalidQuantifier(n, m)

    ls = [elem] * n
    if m == float('inf'):
        ls += ['{} *'.format(elem)]
    else:
        ls += ['{} "" |'.format(elem)] * (m - n)

    ls = sum(([e, '&'] for e in ls[1:]), ls[0:1])
    return ' '.join(ls or ['""'])


def _term_action(result):
    return ' '.join(sum(([e, '&'] for e in result[1:]), result[0:1]))


def _expr_action(result):
    return ' '.join(sum(([e, '|'] for e in result[2::2]), result[0:1]))


def _sdef_action(result):
    return result[0], result[2], result[1]


def _prod_action(result):
    return tuple(result[0:1] + result[2].split() + result[1:2])


def _tdef_action(result):
    return tuple(result[:-2]), result[-1], result[-2]


def _edef_action(result):
    return tuple(result[:-2]), result[-1], result[-2]


def _rule_action(result):
    return result[:-1]


def _grammar_action(result):
    return result[:]


for name in dir():
    elem = locals().get(name)
    action = locals().get(name + '_action')
    if isinstance(elem, ParserElement) and action is not None:
        elem.setParseAction(action)


# Main ------------------------------------------------------------------------
def parse(text, lang):
    sdefs, prods, tdefs, edefs = _parse(text, lang)
    _validate_defs(sdefs, tdefs, edefs)
    return _build_objs(sdefs, prods, tdefs, edefs)


def _parse(text, lang):
    sdefs, prods, tdefs, edefs = set(), {}, {}, set()

    for r in _grammar.parseString(text, parseAll=True):
        op = r[-1]
        if op == '=':
            lhs, rhs = r[0], r[1]
            if lhs == 'START':
                sdefs.add(rhs)
            elif len(lhs) == 1 or lhs[1] == lang:
                edefs.add(rhs)

        elif op == '->':
            lhs, rhs = r[0], r[1:-1]
            if lhs in prods:
                prods[lhs] += rhs + ('|',)
            else:
                prods[lhs] = rhs

        elif op == ':':
            lhs, rhs = r[0], r[1]
            if len(lhs) == 1 or lhs[1] == lang:
                tdefs.setdefault(lhs[0], set()).add(rhs)

    return sdefs, prods, tdefs, edefs


def _validate_defs(sdefs, tdefs, edefs):
    if len(sdefs) == 0:
        raise NoStartSymbol()

    if 1 < len(sdefs):
        raise MultipleStartSymbol()

    if 1 < len(edefs):
        raise MultipleEvalCode()

    for lhs, rhs in tdefs.items():
        if 1 < len(rhs):
            raise MultipleTypeDefinition(lhs)


def _build_objs(sdefs, prods, tdefs, edefs):
    _prods = {}
    for lhs, rhs in prods.items():
        toks = []
        for t in rhs:
            if t.isalpha():
                toks.append(Token.nonterm(t))
            elif t.startswith('"'):
                toks.append(Token.term(t.strip('"')))
            elif t == '&':
                toks.append(Token.concat())
            elif t == '|':
                toks.append(Token.alter())
            elif t == '*':
                toks.append(Token.star())
        _prods[Token.nonterm(lhs)] = Expr(toks)
    prods = _prods

    _tdefs = {}
    for lhs, rhs in tdefs.items():
        _tdefs[Token.nonterm(lhs)] = Token.type(next(iter(rhs)))
    tdefs = _tdefs

    start = Token.nonterm(next(iter(sdefs)))
    eval = Token.code(next(iter(edefs), ''))

    grammar = Grammar(start, prods, tdefs, eval)
    grammar.validate()
    return grammar
