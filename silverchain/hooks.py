# -*- coding: utf-8 -*-
import sys
from networkx import DiGraph
from networkx import bfs_edges, strongly_connected_components as sccs
from .data import Expr, Token
from .data import Cell, State, Symbol


def post_parse(grammar):
    graph = DiGraph()
    graph.add_nodes_from(grammar.prods)
    for lhs, rhs in grammar.prods.items():
        for tok in rhs:
            if tok in grammar.prods:
                graph.add_edge(lhs, tok)

    while True:
        for ns, nd in bfs_edges(graph, grammar.start):
            if graph.has_edge(nd, nd):
                continue

            g = graph.subgraph(n for n in graph.nodes_iter() if n != ns)
            if len(next((c for c in sccs(g) if nd in c))) != 1:
                continue

            expr = []
            alter = Token.alter()
            for tok in grammar.prods[ns]:
                expr.append(tok)
                if tok == nd:
                    expr.extend(list(grammar.prods[nd]) + [alter])
            grammar.prods[ns] = Expr(expr)

            graph.remove_edge(ns, nd)
            for _, dst in graph.edges_iter(nd):
                graph.add_edge(ns, dst)

            break

        else:
            break


def post_tabulate(table):
    groups = {}
    for c in table.cells:
        groups.setdefault(c.src.sym, set()).add(c)

    for sym, cells in groups.items():
        rrec = any(c.dst[0].is_fin for c in cells if c.sym == sym)
        lrec = any(c.src.idx == 0 for c in cells if c.sym == sym)
        if rrec:
            msg = 'WARNING: Right recursion in the rule for {}'.format(sym)
            print(msg, file=sys.stderr)
        if lrec:
            msg = 'WARNING: Left recurstion in the rule for {}'.format(sym)
            print(msg, file=sys.stderr)

    copies = {}
    for sym, cells in groups.items():
        if any(c.src.is_fin for c in cells):
            continue

        copies[sym] = set()
        for c in cells:
            s = Symbol.nonterm('_' + c.src.sym.text)
            src = State(s, c.src.idx)
            dst = () if c.dst[0].is_fin else (State(s, c.dst[0].idx),)
            copies[sym].add(Cell(src, c.sym, dst))

    for cells in copies.values():
        table.cells.update(cells)

    adds = set()
    for cell in table.cells:
        if cell.sym not in copies:
            continue

        fsts = set(c for c in copies[cell.sym] if c.src.idx == 0)
        for f in fsts:
            if len(f.dst) == 0:
                for c in table.cells:
                    if c.src == cell.src and c.sym == f.sym:
                        break
                else:
                    c = Cell(cell.src, f.sym, cell.dst)
                    adds.add(c)
            else:
                for c in table.cells:
                    if c.src == cell.src and c.sym == f.sym:
                        break
                else:
                    c = Cell(cell.src, f.sym, f.dst + cell.dst)
                    adds.add(c)

    table.cells.update(adds)
