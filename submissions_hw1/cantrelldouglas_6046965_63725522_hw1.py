#!/usr/bin/env python

r"""
translate the AST parsed by compiler.parse() and generate C code.
based on Siek's code, but added assignments and for statement.

doctesting:
>>> from contextlib import closing
>>> import functools
>>> import subprocess
>>> import tempfile
>>> def test_output(src):
...     class Namespace(object):
...         def __init__(self, **kwargs):
...             for key in kwargs:
...                 setattr(self, key, kwargs[key])
...     expected_output = actual_output = None
...     f = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
...     with closing(Namespace(close=lambda: os.unlink(f.name))):
...         f.close()
...         with open(f.name, "w") as out:
...             out.write(src)
...         expected_output = subprocess.check_output(["python", f.name])
...     f = tempfile.NamedTemporaryFile(suffix=".c", delete=False)
...     with closing(Namespace(close=lambda: os.unlink(f.name))):
...         with open(f.name, "w") as out:
...             out.write(generate_c(compiler.parse(src)))
...         app = tempfile.NamedTemporaryFile(suffix=".exe", delete=False)
...         with closing(Namespace(close=lambda: os.unlink(app.name))):
...             app.close()
...             subprocess.check_call(["clang", "-o", app.name, f.name])
...             subprocess.call(["chmod", "0777", app.name])
...             app_path = os.path.abspath(app.name)
...             actual_output = subprocess.check_output([app_path])
...     return (actual_output == expected_output) and actual_output is not None
>>> print test_output("a = 3\nprint a\n")
True
>>> print test_output("a = ---3\nprint a, 7\n")
True
>>> print test_output("a = 1 + 1\nprint a + 1")
True
>>> print test_output("a = b = 2\nfor i in range(4): print a, (b + i)")
True
>>> print test_output("i = 2\nj = i\nfor i in range(j): print -i\nprint i")
True
>>> print test_output("i = 4\nfor i in range(0): print 1\nprint i")
True
>>> print test_output("i = 4\nfor i in range(1): print 1\nprint i")
True
>>> print test_output("i = 8\nfor i in range(2): a = i = i + 1\nprint i, a")
True
>>> print test_output("i = 8\nfor i in range(2): i = 0\nprint i")
True
>>> print test_output("i0 = 8\nfor i1 in range(2): i2 = i1\nprint i0, i1, i2")
True
>>> print test_output("limit = 9\nfor i in range(limit): limit = 100\nprint i")
True
"""

__author__ = "Liang Huang (modified by Douglas Cantrell)"

import os
import sys
logs = sys.stderr
import compiler
from compiler.ast import *
import itertools
import re

ivars = []
irefs = []

def generate_c(n):
    if isinstance(n, Module):
        del ivars[:] # Clear the global int var list. TODO: Don't use globals.
        headers = '\n'.join('#include <%s>' % h for h in ['stdio.h'])
        logic = '\n'.join((generate_c(n.node), 'return 0;'))
        decls = 'int %s;' % ', '.join(var for var in ivars)
        code = '%s\nint main()\n{\n%s\n%s\n}' % (headers, decls, logic)
        brackets = (ln.count('{') - ln.count('}') for ln in code.splitlines())
        levels = reduce(lambda a, b: a + [a[-1] + b if a else b], brackets, [])
        tabs = itertools.imap(lambda x: x * '\t', levels)
        code = '\n'.join(tab + ln for tab, ln in zip(tabs, code.splitlines()))
        pattern = re.compile('^\t(\t*{)$', flags=re.MULTILINE)
        return pattern.sub('\\1', code)
    elif isinstance(n, Stmt):
        return '\n'.join((generate_c(node) for node in n.nodes))
    elif isinstance(n, Printnl):
        format_string = ' '.join(['%d'] * len(n.nodes))
        format_values = ', '.join(map(generate_c, n.nodes))
        return 'printf("%s\\n", %s);' % (format_string, format_values)
    elif isinstance(n, Const):
        return '%d' % n.value
    elif isinstance(n, UnarySub):
        return '(-%s)' % generate_c(n.expr)
    elif isinstance(n, Assign):
        # assuming n.flags == OP_ASSIGN
        rhs = generate_c(n.expr)
        lhs = generate_c
        return '\n'.join('%s = %s;' % (lhs(node), rhs) for node in n.nodes)
    elif isinstance(n, AssName):
        if n.name not in ivars:
            ivars.append(n.name)
        return n.name
    elif isinstance(n, Name):
        if n.name not in irefs:
            irefs.append(n.name)
        return n.name
    elif isinstance(n, Add):
        return '%s + %s' % (generate_c(n.left), generate_c(n.right))
    elif isinstance(n, For):
        loop_var = generate_c(n.assign)
        range_arg = generate_c(n.list.args[0])
        code = generate_c(n.body)
        names = set(ivars + irefs)
        _itr = ('i%d' % n for n in range(len(names)) if 'i%d' % n not in names)
        _var = next(_itr, 'i%d' % len(names))
        init = '%s[2] = {0, %s}' % (_var, range_arg)
        test = '%s[0] < %s[1]' % (_var, _var)
        step = '%s[0]++' % _var
        loop = 'for (int %s; %s; %s)' % (init, test, step)
        body = '\n'.join(('%s = %s[0];' % (loop_var, _var), code))
        return '\n'.join((loop, '{', body, '}'))
    else:
        raise sys.exit('Error in generate_c: unrecognized AST node: %s' % n)

if __name__ == "__main__":
    try:
        ast = compiler.parse('\n'.join(sys.stdin.readlines()))
        print >> logs, ast # debug
        print generate_c(ast)
    except Exception, e:
        print >> logs, e.args[0]
        exit(-1)
