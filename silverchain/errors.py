# -*- coding: utf-8 -*-


# Raised in Parser ------------------------------------------------------------
class InvalidQuantifier(Exception):
    def __init__(self, n, m):
        msg = '{{{},{}}} is invalid.'.format(n, m)
        super(InvalidQuantifier, self).__init__(msg)


class MultipleEvalCode(Exception):
    def __init__(self):
        msg = 'Eval code is specified more than once.'
        super(MultipleEvalCode, self).__init__(msg)


class MultipleStartSymbol(Exception):
    def __init__(self):
        msg = 'Start symbol is specified more than once.'
        super(MultipleStartSymbol, self).__init__(msg)


class NoStartSymbol(Exception):
    def __init__(self):
        msg = 'Start symbol is not specified.'
        super(NoStartSymbol, self).__init__(msg)


class MultipleTypeDefinition(Exception):
    def __init__(self, sym):
        msg = 'The type of {} is specified more than once.'.format(sym)
        super(MultipleTypeDefinition, self).__init__(msg)


# Raised in Grammar.validate --------------------------------------------------
class InvalidStartSymbol(Exception):
    def __init__(self):
        msg = 'Start symbol must be a non-typed nonterminal'
        super(InvalidStartSymbol, self).__init__(msg)


class RuleConflict(Exception):
    def __init__(self, sym):
        msg = '{} has a type definition and a production rule'.format(sym)
        super(RuleConflict, self).__init__(msg)


class UndefinedSymbol(Exception):
    def __init__(self, sym):
        msg = '{} is undefined'.format(sym)
        super(UndefinedSymbol, self).__init__(msg)


# Raised in Expr.validate -----------------------------------------------------
class InvalidExpression(Exception):
    def __init__(self, expr):
        msg = '`{}` is invalid.'.format(expr)
        super(InvalidExpression, self).__init__(msg)
