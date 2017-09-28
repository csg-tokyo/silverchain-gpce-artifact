# -*- coding: utf-8 -*-
import sys
from networkx import DiGraph
from networkx import bfs_edges, strongly_connected_components as sccs
from .data import Expr, Token
from .data import Cell, State, Symbol


def post_parse(grammar):
    # Create `G`
    G = DiGraph()
    G.add_nodes_from(grammar.prods)
    for lhs, rhs in grammar.prods.items():
        for tok in rhs:
            if tok in grammar.prods:
                G.add_edge(lhs, tok)

    # DEBUG: from ._debug import Drawer # DEBUG
    # DEBUG: drawer = Drawer(G, grammar.start) # DEBUG

    # Inlining
    for root, _ in list(bfs_edges(G, grammar.start)):
        while True:
            nodes = [d for _, d in bfs_edges(G, root)]
            nodes = [root] + nodes
            edges = []
            for n in nodes:
                edges.extend(G.edges([n]))
            for ns, nd in reversed(edges):
                # DEBUG: drawer.draw(G, (ns, nd)) # DEBUG

                # Skip if `nd` has a self-loop
                if G.has_edge(nd, nd):
                    continue

                # Skip if `C` consists of multiple nodes
                g = G.subgraph(n for n in G.nodes_iter() if n != ns)
                if len(next((c for c in sccs(g) if nd in c))) != 1:
                    continue

                # Update grammar
                expr = []
                alter = Token.alter()
                for tok in grammar.prods[ns]:
                    expr.append(tok)
                    if tok == nd:
                        expr.extend(list(grammar.prods[nd]) + [alter])
                grammar.prods[ns] = Expr(expr)

                # Update G
                G.remove_edge(ns, nd)
                for _, dst in G.edges_iter(nd):
                    G.add_edge(ns, dst)

                # DEBUG: drawer.draw(G) # DEBUG
                break  # Back to `for ns, nd in ...`

            else:
                # DEBUG: drawer.draw(G) # DEBUG
                break  # Back to `for root, _ in ...`

    return {nd for _, nd in G.edges_iter()}  # Unexpanded nonterminals


def post_tabulate(table, unexpanded):
    # Group cells
    groups = {}
    for c in table.cells:
        groups.setdefault(c.src.sym, set()).add(c)

    # Copy cells for unexpanded nonterminals
    copies = {}
    for sym, cells in groups.items():
        if sym not in unexpanded:
            continue

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

    # Modify table
    adds = set()
    for cell in table.cells:
        # Skip if cell's symbol is not related to a copied symbol
        if cell.sym not in copies:
            continue

        # Add cells
        fsts = set(c for c in copies[cell.sym] if c.src.idx == 0)
        for f in fsts:
            for c in table.cells:
                if c.src == cell.src and c.sym == f.sym:
                    break
            else:
                if len(f.dst) == 0:
                    c = Cell(cell.src, f.sym, cell.dst)
                    adds.add(c)
                else:
                    c = Cell(cell.src, f.sym, f.dst + cell.dst)
                    adds.add(c)

    table.cells.update(adds)
