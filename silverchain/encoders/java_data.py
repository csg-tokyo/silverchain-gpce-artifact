# -*- coding: utf-8 -*-
from textwrap import indent


class NontermClass(object):
    @staticmethod
    def to_class_name(text):
        if text.startswith('_'):
            return '_' + text[1].upper() + text[2:]
        else:
            return text[0].upper() + text[1:]

    def __init__(self, name, is_start, eval):
        self._name = self.to_class_name(name)
        self._is_start = is_start
        self._eval = eval
        self._stcs = set()
        self._starts = set()

    @property
    def stcs(self):
        return self._stcs

    @property
    def starts(self):
        return self._starts

    @property
    def fname(self):
        return self._name + '.java'

    def __str__(self):
        c = ''
        c += 'public class ' + self._name + ' {\n\n'
        if self._is_start:
            c += '    public void eval() {\n'
            c += indent(self._eval, '    '*2) + '\n'
            c += '    }\n\n'
        c += '    private ' + self._name + '() {}\n\n'
        c += '    Context$ context() {\n'
        c += '        return null;\n'
        c += '    }\n\n'

        if not self._name.startswith('_'):
            c += '    public static final class StartingMethods {\n\n'
            c += '        private StartingMethods() {}\n\n'
            for m in sorted(self._starts):
                c += indent(str(m), '    '*2) + '\n\n'
            c += '    }\n\n'

        for stc in sorted(self._stcs):
            c += indent(str(stc), '    ') + '\n\n'

        c += '}'
        return c


class StateClass(object):
    def __init__(self, name, idx, extends):
        self._name = NontermClass.to_class_name(name)
        self._idx = str(idx)
        self._extends = extends
        self._methods = set()

    @property
    def methods(self):
        return self._methods

    def __str__(self):
        c = ''
        c += 'public static final class State' + self._idx + '<T>'
        c += ' extends {}'.format(self._name) if self._extends else ''
        c += ' {\n\n'
        c += '    final Context$ context;\n\n'
        c += '    State' + self._idx + '(Context$ context) {\n'
        c += '        this.context = context;\n'
        c += '    }\n\n'

        if self._extends:
            c += '    Context$ context() {\n'
            c += '        return context;\n'
            c += '    }\n\n'

        for m in sorted(self._methods):
            c += indent(str(m), '    ') + '\n\n'

        c += '}'
        return c

    def __lt__(self, other):
        return int(self._idx) < int(other._idx)


class Method(object):
    @staticmethod
    def escape_reserved(name):
        reserved = [
            'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
            'char', 'class', 'const', 'continue', 'default', 'do', 'double',
            'else', 'enum', 'extends', 'false', 'final', 'finally', 'float',
            'for', 'goto', 'if', 'implements', 'import', 'instanceof', 'int',
            'interface', 'long', 'native', 'new', 'null', 'package', 'private',
            'protected', 'public', 'return', 'short', 'static', 'strictfp',
            'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
            'transient', 'true', 'try', 'void', 'volatile', 'while'
        ]
        return name + '_' if name in reserved else name

    def __init__(self, ret, name, arg=None, is_native_arg=False, repeat=False):
        self._ret = ''
        for sym, idx in ret:
            ntc = NontermClass.to_class_name(sym)
            self._ret += ntc + '.State' + str(idx) + '<'
        self._ret += 'T' + '>' * len(ret)

        name = self.escape_reserved(name[0].lower() + name[1:])
        self._name = name

        if arg is None:
            self._arg = ''
            self._madd = ''
        elif arg == '':
            self._arg = ''
            self._madd = 'context.methods.add(new Method$("' + name + '"));'
        elif is_native_arg:
            self._arg = arg + ' ' + name
            self._madd = 'context.methods.add('
            self._madd += 'new Method$("' + name + '", ' + name + '));'
            if repeat:
                self._arg += ', ' + self._arg.replace(' ', '... ') + 'Array'
                forstmt = '\nfor ({} $: {}Array) {{\n'.format(arg, name)
                forstmt += '    context.methods'
                forstmt += '.add(new Method$("{}", $));\n'.format(name)
                forstmt += '}'
                self._madd += forstmt
        else:
            ntc = NontermClass.to_class_name(arg)
            val = ntc[0].lower() + ntc[1:]
            self._arg = ntc + ' ' + val
            self._madd = 'context.methods.addAll('
            self._madd += val + '.context().methods);'
            if repeat:
                self._arg += ', ' + self._arg.replace(' ', '... ') + 'Array'
                forstmt = '\nfor ({} $: {}Array) {{\n'.format(ntc, val)
                forstmt += '    context.methods.addAll($.context().methods);\n'
                forstmt += '}'
                self._madd += forstmt

        if 1 < len(ret):
            c = self._ret.split('<', 2)[1]
            self._cpush = 'context.classes.push(' + c + '.class);'
        else:
            self._cpush = ''

        if len(ret):
            r = self._ret.split('<', 1)[0]
            self._new = 'return new ' + r + '<>(context);'
        else:
            n = ''
            n += 'try {\n'
            n += '    return (T) context.classes\n'
            n += '            .pop()\n'
            n += '            .getDeclaredConstructor(Context$.class)\n'
            n += '            .newInstance(context);\n'
            n += '} catch (Exception e) {\n'
            n += '    throw new RuntimeException(e);'
            n += '}\n'
            self._new = n

    def __lt__(self, other):
        return self._name < other._name

    def __str__(self):
        r = self._ret
        n = self._name
        a = self._arg
        c = ''
        c += 'public ' + r + ' ' + n + '(' + a + ') {\n'

        if self._madd:
            c += indent(self._madd, '    ') + '\n'

        if self._cpush:
            c += '    ' + self._cpush + '\n'

        c += indent(self._new, '    ') + '\n'
        c += '}'

        if r == 'T':
            c = '@SuppressWarnings("unchecked")\n' + c
        return c


class StartingMethod(Method):
    def __str__(self):
        lines = super(StartingMethod, self).__str__().splitlines()
        lines[0] = lines[0].replace('public ', 'public static ')
        lines[0] = lines[0].replace('<T>', '<Bottom$>')
        lines.insert(1, '    Context$ context = new Context$();')
        return '\n'.join(lines)


BOTTOM = 'Bottom$.java', """
final class Bottom$ {}
""".strip()


CONTEXT = 'Context$.java', """
import java.util.ArrayList;
import java.util.Stack;

final class Context$ {

    final Stack<Class<?>> classes = new Stack<>();

    final ArrayList<Method$> methods = new ArrayList<>();

}
""".strip()


METHOD = 'Method$.java', """
final class Method$ {

    final Object argument;

    final String name;

    Method$(Object argument, String name) {
        this.argument = argument;
        this.name = name;
    }

    Method$(String name) {
        this.argument = null;
        this.name = name;
    }

}
""".strip()
