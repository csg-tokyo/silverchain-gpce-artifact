# -*- coding: utf-8 -*-
from collections import deque
from itertools import combinations
from networkx import DiGraph, descendants
from .data import Table, Cell, State


def to_dfa(table):
    for c in table.cells:
        if len(c.dst) != 1:
            raise Exception()

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

    def _sorted_edge_iter(g, src):
        edges = g.edges(src, data=True)
        edges = ((attrs['label'], dsts) for _, dsts, attrs in edges)
        for e in sorted(edges):
            yield e[1]

    nums, states = {}, {}
    visited, deq = set(), deque()
    graph = DiGraph((srcs, dsts, {'label': sym}) for srcs, sym, dsts in trs)
    for srcs, _, _ in trs:
        if any(s.is_ini for s in srcs):
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


def _create_eps_closure_func(table):
    edges = {(c.src, c.sym.text, c.dst[0]) for c in table.cells}
    graph = DiGraph((src, dst) for src, sym, dst in edges if sym == '')
    states = set(sum(((src, dst) for src, _, dst in edges), ()))

    cs = {s: descendants(graph, s) if s in graph else set() for s in states}
    return lambda ss: frozenset(set(ss).union(*(cs[s] for s in ss)))
