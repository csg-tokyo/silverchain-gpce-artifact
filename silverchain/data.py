# -*- coding: utf-8 -*-
from collections.abc import MutableSequence
from .errors import InvalidExpression
from .errors import InvalidStartSymbol, RuleConflict, UndefinedSymbol


class Table(object):
    def __init__(self, start, cells, eval):
        self._start = start
        self._cells = cells
        self._eval = eval

    @property
    def start(self):
        return self._start

    @property
    def cells(self):
        return self._cells

    @property
    def groups(self):
        grps = {}
        for c in self._cells:
            grps.setdefault(c.src.sym, set()).add(c)
        return grps

    @property
    def states(self):
        sts = set()
        for c in self._cells:
            sts.add(c.src)
            sts.update(c.dst)
        return sts

    @property
    def eval(self):
        return self._eval

    def __str__(self):
        lines = []
        lines.append('START = {}'.format(self._start))
        lines.append('EVAL = "{}"'.format(self._eval.replace('"', '\\"')))
        lines.extend(str(c) for c in sorted(self._cells))
        return '\n'.join(lines)


class Cell(object):
    def __init__(self, src, sym, dst):
        self._src = src
        self._sym = sym
        self._dst = dst

    @property
    def src(self):
        return self._src

    @property
    def sym(self):
        return self._sym

    @property
    def dst(self):
        return self._dst

    def __str__(self):
        return '{}  -{}->  {}'.format(
            self._src,
            self._sym,
            ', '.join(str(d) for d in self._dst)
        )

    def __hash__(self):
        return hash(self._src) + hash(self._sym) + hash(self._dst)

    def __eq__(self, other):
        return (self._src == other._src and
                self._sym == other._sym and
                self._dst == other.dst)

    def __lt__(self, other):
        seq1 = self._src, self._dst, self._sym
        seq2 = other._src, other._dst, other._sym
        return seq1 < seq2


class State(object):
    def __init__(self, sym, idx, is_ini=False, is_fin=False):
        self._sym = sym
        self._idx = idx
        self._is_ini = is_ini
        self._is_fin = is_fin

    @property
    def sym(self):
        return self._sym

    @property
    def idx(self):
        return self._idx

    @property
    def is_ini(self):
        return self._is_ini

    @property
    def is_fin(self):
        return self._is_fin

    def __str__(self):
        return '{}[{}]{}'.format(
            self._sym,
            self._idx,
            '*' if self._is_fin else ''
        )

    def __hash__(self):
        return hash(self._sym) + hash(self._idx) + self._is_ini + self._is_fin

    def __eq__(self, other):
        return (self._sym == other._sym and
                self._idx == other._idx and
                self._is_ini == other._is_ini and
                self._is_fin == other._is_fin)

    def __lt__(self, other):
        seq1 = self._sym, self._idx, not self._is_ini, self._is_fin
        seq2 = other._sym, other._idx, not other._is_ini, other._is_fin
        return seq1 < seq2


class Symbol(object):
    _TERM, _NONTERM = range(2)

    def __init__(self, text, category, type):
        self._text = text
        self._category = category
        self._type = type

    @classmethod
    def term(cls, text):
        return Symbol(text, cls._TERM, None)

    @classmethod
    def nonterm(cls, text, type=None):
        return Symbol(text, cls._NONTERM, type)

    @property
    def text(self):
        return self._text

    @property
    def is_term(self):
        return self._category == self._TERM

    @property
    def is_nonterm(self):
        return self._category == self._NONTERM

    @property
    def type(self):
        return self._type

    @property
    def is_typed(self):
        return self._type is not None

    def __str__(self):
        if self.is_term:
            return '"{}"'.format(self._text)
        if self.is_nonterm:
            if self.is_typed:
                return '{}({})'.format(
                    self._text,
                    str(self._type).strip('"')
                )
            else:
                return self._text

    def __hash__(self):
        return hash(self._text) + hash(self._category) + hash(self._type)

    def __eq__(self, other):
        return (self._text == other._text and
                self._category == other._category and
                self._type == other._type)

    def __lt__(self, other):
        seq1 = self._category, self._text, self._type
        seq2 = other._category, other._text, other._type
        return seq1 < seq2


class Grammar(object):
    def __init__(self, start, prods, tdefs, eval):
        self.start = start
        self._prods = prods
        self._tdefs = tdefs
        self.eval = eval

    @property
    def prods(self):
        return self._prods

    @property
    def tdefs(self):
        return self._tdefs

    def validate(self):
        if self.start not in self._prods:
            raise InvalidStartSymbol()

        for lhs in (set(self._prods) & set(self._tdefs)):
            raise RuleConflict(lhs)

        for expr in self._prods.values():
            expr.validate()
            for tok in expr:
                if not tok.is_nonterm:
                    continue
                if tok in self._prods:
                    continue
                if tok in self._tdefs:
                    continue
                raise UndefinedSymbol(tok)

    def __str__(self):
        lines = []
        lines.append('START = {} ;'.format(self.start))
        for lhs, rhs in sorted(self._prods.items()):
            lines.append('{} -> {} ;'.format(lhs, rhs))
        for lhs, rhs in sorted(self._tdefs.items()):
            lines.append('{} : {}'.format(lhs, rhs))
        lines.append('EVAL = {} ;'.format(self.eval))
        return '\n'.join(lines)


class Expr(MutableSequence):
    def __init__(self, tokens):
        self._tokens = [t for t in tokens]

    def __delitem__(self, i):
        return self._tokens.__delitem__(i)

    def __getitem__(self, i):
        return self._tokens.__getitem__(i)

    def __len__(self):
        return self._tokens.__len__()

    def __setitem__(self, i, v):
        return self._tokens.__setitem__(i, v)

    def insert(self, i, v):
        return self._tokens.insert(i, v)

    def validate(self):
        n_stack = 0
        for tok in self._tokens:
            if tok.is_term or tok.is_nonterm:
                n_stack += 1
            elif tok.is_concat or tok.is_alter:
                n_stack -= 1
        if n_stack != 1:
            raise InvalidExpression(self)

    def __str__(self):
        return ' '.join(str(t) for t in self)


class Token(object):
    _TERM, _NONTERM, _CONCAT, _ALTER, _STAR, _TYPE, _CODE = range(7)

    def __init__(self, text, category):
        self._text = text
        self._category = category

    @classmethod
    def term(cls, text):
        return Token(text, cls._TERM)

    @classmethod
    def nonterm(cls, text):
        return Token(text, cls._NONTERM)

    @classmethod
    def concat(cls):
        return Token('&', cls._CONCAT)

    @classmethod
    def alter(cls):
        return Token('|', cls._ALTER)

    @classmethod
    def star(cls):
        return Token('*', cls._STAR)

    @classmethod
    def type(cls, text):
        return Token(text, cls._TYPE)

    @classmethod
    def code(cls, text):
        return Token(text, cls._CODE)

    @property
    def text(self):
        return self._text

    @property
    def is_term(self):
        return self._category == self._TERM

    @property
    def is_nonterm(self):
        return self._category == self._NONTERM

    @property
    def is_concat(self):
        return self._category == self._CONCAT

    @property
    def is_alter(self):
        return self._category == self._ALTER

    @property
    def is_star(self):
        return self._category == self._STAR

    @property
    def is_type(self):
        return self._category == self._TYPE

    @property
    def is_code(self):
        return self._category == self._CODE

    def __str__(self):
        if self.is_term:
            return '"{}"'.format(self._text)
        if self.is_nonterm:
            return self._text
        if self.is_concat or self.is_alter or self.is_star:
            return self._text
        if self.is_type or self.is_code:
            return '"{}"'.format(self._text.replace('"', '\\"'))

    def __hash__(self):
        return hash(self._text) + hash(self._category)

    def __eq__(self, other):
        return (self._text == other._text and
                self._category == other._category)

    def __lt__(self, other):
        seq1 = self._category, self._text
        seq2 = other._category, other._text
        return seq1 < seq2
