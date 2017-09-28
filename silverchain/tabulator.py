# -*- coding: utf-8 -*-
from collections import deque
from itertools import combinations
from networkx import DiGraph, descendants
from .data import Token
from .data import Table, Cell, State, Symbol


def tabulate(grammar):
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
    return _to_dfa(table)


def _to_dfa(table):
    eps_cls = _create_eps_closure_func(table)
    trs, queue, queued = set(), [], set()
    inis = {eps_cls((c.src,)) for c in table.cells if c.src.is_ini}

    queue.extend(inis)
    queued.update(inis)
    while queue:
        srcs, queue = queue[0], queue[1:]
        edges = {}
        for c in table.cells:
            if c.src in srcs:
                edges.setdefault(c.sym, set()).add(c.dst[0])
        for sym, dsts in edges.items():
            if sym.text != '':
                dsts = eps_cls(dsts)
                trs.add((srcs, sym, dsts))
                if dsts not in queued:
                    queue.append(dsts)
                    queued.add(dsts)

    while True:
        grps = {}
        for srcs, sym, dsts in trs:
            grps.setdefault(srcs, set()).add((sym, dsts))

        pair = None
        for (s1, g1), (s2, g2) in combinations(grps.items(), 2):
            if (g1 == g2):
                if any(s.is_fin for s in s1) is any(s.is_fin for s in s2):
                    if any(s.is_ini for s in s2):
                        pair = s2, s1
                    else:
                        pair = s1, s2
                    break
        else:
            break

        trs = {t for t in trs if t[0] != pair[1]}
        trs = {t[:2] + (pair[0] if t[2] == pair[1] else t[2],) for t in trs}

    nums, states = {}, {}
    visited, deq = set(), deque()
    graph = DiGraph((srcs, dsts, {'label': sym}) for srcs, sym, dsts in trs)
    for srcs, _, _ in trs:
        if srcs in inis:
            states[srcs] = 0
            deq.append((srcs, _sorted_edge_iter(graph, srcs)))
            visited.add(srcs)

    while deq:
        parent, children = deq[0]
        try:
            child = next(children)
            if child not in visited:
                if child not in states:
                    sym = next(iter(child)).sym
                    nums.setdefault(sym, 1)
                    states[child] = nums[sym]
                    nums[sym] += 1
                visited.add(child)
                deq.append((child, _sorted_edge_iter(graph, child)))
        except StopIteration:
            deq.popleft()

    cells = set()
    for t in trs:
        if t[0] not in states:
            continue

        sym = next(iter(t[0])).sym

        idx = states[t[0]]
        is_ini = any(s.is_ini for s in t[0])
        is_fin = any(s.is_fin for s in t[0])
        src = State(sym, idx, is_ini, is_fin)

        idx = states[t[2]]
        is_ini = any(s.is_ini for s in t[2])
        is_fin = any(s.is_fin for s in t[2])
        dst = State(sym, idx, is_ini, is_fin)

        c = Cell(src, t[1], (dst,))
        cells.add(c)

    table = Table(table.start, cells, table.eval)
    return table


def _sorted_edge_iter(g, src):
    edges = g.edges(src, data=True)
    edges = ((attrs['label'], dsts) for _, dsts, attrs in edges)
    for e in sorted(edges):
        yield e[1]


def _create_eps_closure_func(table):
    edges = {(c.src, c.sym.text, c.dst[0]) for c in table.cells}
    graph = DiGraph((src, dst) for src, sym, dst in edges if sym == '')
    states = set(sum(((src, dst) for src, _, dst in edges), ()))

    cs = {s: descendants(graph, s) if s in graph else set() for s in states}
    return lambda ss: frozenset(set(ss).union(*(cs[s] for s in ss)))
