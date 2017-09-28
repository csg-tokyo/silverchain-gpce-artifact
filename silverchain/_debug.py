# -*- coding: utf-8 -*-
import glob
import os
import subprocess
from networkx import bfs_edges


class Drawer(object):
    WSDIR = './workspace'

    def __init__(self, graph, start):
        for f in glob.glob(self.WSDIR + '/*.png'):
            os.remove(f)
        for f in glob.glob(self.WSDIR + '/*.dot'):
            os.remove(f)

        self._n = 0

        ranks = {start: 0}
        for s, d in bfs_edges(graph, start):
            ranks[d] = ranks[s] + 1
        _ranks = {}
        for n, r in ranks.items():
            _ranks.setdefault(r, set()).add(n)
        ranks = _ranks

        self._ranks = ''
        fmt = '  "{n}" [pos="{x},{y}!"] ;\n'
        for r, ns in sorted(ranks.items()):
            ns = sorted([str(n) for n in ns])
            for i, n in enumerate(ns):
                x = i * 2 + r % 2
                y = -r * 2
                self._ranks += fmt.format(n=n, x=x, y=y)

    def draw(self, graph, highlight=None):
        gv = ''
        gv += 'digraph G{} {{\n'.format(self._n)
        gv += '  layout=neato;\n'
        gv += self._ranks
        for s, d in graph.edges_iter():
            gv += '  "{}" -> "{}"'.format(s, d)
            if (s, d) == highlight:
                gv += '[color=red,penwidth=3]'
            gv += ';\n'
        gv += '}'

        fname = self.WSDIR + '/{0:04d}'.format(self._n)
        with open(fname + '.dot', 'w') as f:
            print(gv, file=f)

        cmd = ''
        cmd += '/usr/local/bin/neato'
        cmd += ' -Tpng {f}.dot -o{f}.png'.format(f=fname)
        subprocess.call(cmd, shell=True)

        self._n += 1
