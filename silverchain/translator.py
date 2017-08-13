# -*- coding: utf-8 -*-
from pyparsing import alphas, nums, restOfLine
from pyparsing import Forward, Keyword, QuotedString, Word
from pyparsing import OneOrMore, Optional, Or, ZeroOrMore
from .data import Grammar, Expr, Token
from .data import Table, Cell, State, Symbol
from .encoders import get_encode_func, languages
from .errors import InvalidQuantifier
from .errors import MultipleEvalCode
from .errors import MultipleStartSymbol, NoStartSymbol
from .errors import MultipleTypeDefinition
from .utils import to_dfa


def translate(text, lang, post_parse, post_tabulate):
    grammar = _parse(text, lang)
    post_parse(grammar)
    grammar.validate()

    table = _tabulate(grammar)
    post_tabulate(table)

    encode = get_encode_func(lang)
    return encode(table)


def _tabulate(grammar):
    tokens = set()
    transitions = {}
    initials = {}
    finals = {}
    n_states = {}

    eps = Token.term('')
    for lhs, rhs in grammar.prods.items():
        tokens.add(lhs)

        n, stack = 0, []
        for t in rhs:
            if t.is_concat:
                trs_r, ini_r, fin_r = stack.pop()
                trs_l, ini_l, fin_l = stack.pop()
                ini, fin = ini_l, fin_r
                trs = trs_l | trs_r | {(fin_l, eps, ini_r)}
                stack.append((trs, ini, fin))
                tokens.add(eps)

            elif t.is_alter:
                trs_r, ini_r, fin_r = stack.pop()
                trs_l, ini_l, fin_l = stack.pop()
                ini, fin = n, n + 1
                trs = {(ini, eps, ini_r), (fin_r, eps, fin),
                       (ini, eps, ini_l), (fin_l, eps, fin)} | trs_l | trs_r
                stack.append((trs, ini, fin))
                n += 2
                tokens.add(eps)

            elif t.is_star:
                trs, ini, fin = stack.pop()
                trs |= {(n, eps, ini), (fin, eps, n)}
                stack.append((trs, n, n))
                n += 1
                tokens.add(eps)

            else:
                ini, fin = n, n + 1
                trs = {(n, t, fin)}
                stack.append((trs, ini, fin))
                n += 2
                tokens.add(t)

        transitions[lhs], initials[lhs], finals[lhs] = stack.pop()
        n_states[lhs] = n

    symbols = {}
    for tok in tokens:
        if tok.is_term:
            symbols[tok] = Symbol.term(tok.text)
        elif tok.is_nonterm:
            typ = grammar.tdefs.get(tok)
            typ = typ.text if typ else None
            symbols[tok] = Symbol.nonterm(tok.text, typ)

    states = {}
    for tok, n in n_states.items():
        for i in range(n):
            sym = symbols[tok]
            is_ini = (i == initials[tok])
            is_fin = (i == finals[tok])
            states[tok, i] = State(sym, i, is_ini, is_fin)

    cells = set()
    for tok, trs in transitions.items():
        for tr in trs:
            src = states[tok, tr[0]]
            sym = symbols[tr[1]]
            dst = (states[tok, tr[2]],)
            c = Cell(src, sym, dst)
            cells.add(c)

    start = symbols[grammar.start]
    eval = grammar.eval.text
    table = Table(start, cells, eval)
    return to_dfa(table)


def _parse(text, lang):
    nsym = Word(alphas)
    tsym = '"' + Word(alphas) + '"'
    type = QuotedString('"', '\\')
    ltag = '@' + Or(languages)

    uops = '{' + Word(nums) + Optional(',' + Optional(Word(nums))) + '}'
    uops = uops | '*' | '+' | '?'
    expr = Forward()
    elem = nsym | tsym | '(' + expr + ')'
    fact = elem + Optional(uops)
    term = OneOrMore(fact)
    expr << term + ZeroOrMore('|' + term)

    sdef = Keyword('START') + '=' + nsym
    prod = nsym + '->' + expr
    tdef = nsym + Optional(ltag) + ':' + type
    edef = Keyword('EVAL') + Optional(ltag) + '=' + QuotedString('"', '\\')
    cmnt = ('#' + restOfLine).suppress()
    rule = (sdef | prod | tdef | edef) + ';' + Optional(cmnt)
    grammar = OneOrMore(rule | cmnt)

    nsym.setParseAction(lambda r: r[0])
    tsym.setParseAction(lambda r: ''.join(r))
    type.setParseAction(lambda r: r[0])
    ltag.setParseAction(lambda r: r[1])

    uops.setParseAction(_uops_action)
    elem.setParseAction(lambda r: ' '.join(r).strip('()'))
    fact.setParseAction(_fact_action)
    term.setParseAction(lambda r: sum(([e, '&'] for e in r[1:]), r[0:1]))
    term.addParseAction(lambda r: ' '.join(r))
    expr.setParseAction(lambda r: sum(([e, '|'] for e in r[2::2]), r[0:1]))
    expr.addParseAction(lambda r: ' '.join(r))

    sdef.setParseAction(lambda r: (r[0], r[2], r[1]))
    prod.setParseAction(lambda r: tuple(r[0:1] + r[2].split() + r[1:2]))
    tdef.setParseAction(lambda r: (tuple(r[:-2]), r[-1], r[-2]))
    edef.setParseAction(lambda r: (tuple(r[:-2]), r[-1], r[-2]))
    rule.setParseAction(lambda r: r[:-1])
    grammar.setParseAction(lambda r: r[:])

    sdefs, prods, tdefs, edefs = set(), {}, {}, set()
    for r in grammar.parseString(text, parseAll=True):
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

    if len(sdefs) == 0:
        raise NoStartSymbol()
    if 1 < len(sdefs):
        raise MultipleStartSymbol()

    if 1 < len(edefs):
        raise MultipleEvalCode()

    for lhs, rhs in tdefs.items():
        if 1 < len(rhs):
            raise MultipleTypeDefinition(lhs)

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

    g = Grammar(start, prods, tdefs, eval)
    g.validate()
    return g


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
