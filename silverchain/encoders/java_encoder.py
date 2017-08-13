# -*- coding: utf-8 -*-
from .java_data import NontermClass, StateClass, Method, StartingMethod
from .java_data import BOTTOM, CONTEXT, METHOD


def encode(table):
    files = dict((BOTTOM, CONTEXT, METHOD))

    ntcs = {}
    for sym in table.groups:
        ntcs[sym] = NontermClass(sym.text, sym == table.start, table.eval)

    stcs = {}
    for st in table.states:
        stcs[st] = StateClass(st.sym.text, st.idx, st.is_fin)
        ntcs[st.sym].stcs.add(stcs[st])

    for c in table.cells:
        ret = [(d.sym.text, d.idx) for d in c.dst]
        name = c.sym.text

        arg = None
        is_native_arg = False
        if c.sym.is_term:
            arg = ''
            is_native_arg = False
        elif c.sym.is_typed:
            arg = c.sym.type
            is_native_arg = True
        else:
            arg = c.sym.text
            is_native_arg = False

        if c.src.idx == 0:
            method = StartingMethod(ret, name, arg, is_native_arg)
            ntcs[c.src.sym].starts.add(method)

        repeat = False
        if 0 < len(c.dst):
            for _c in table.cells:
                if c.dst[0] == _c.src:
                    if _c.sym == c.sym:
                        repeat = True
                        break
        method = Method(ret, name, arg, is_native_arg, repeat)
        stcs[c.src].methods.add(method)

    for sym, ntc in ntcs.items():
        ret = [(sym.text, 0)]
        name = sym.text
        method = StartingMethod(ret, name)
        for m in ntc.starts:
            if m._name == name:
                break
        else:
            ntc.starts.add(method)

    for c in ntcs.values():
        files[c.fname] = str(c)

    pkg = 'package {};\n\n'.format(table.start.text.lower())
    return {name: pkg + content for name, content in files.items()}
