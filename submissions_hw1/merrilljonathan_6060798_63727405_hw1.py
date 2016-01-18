#!/usr/bin/env python

__author__ = "Jonathan Merrill"

'''translate the AST parsed by compiler.parse() and generate C code.
   based on Siek's code, but added assignments and for statement.'''

import sys
logs = sys.stderr
import compiler
from compiler.ast import *
import re

def generate_c(n, assignments={}):
    if isinstance(n, Module):
        assignments = {
                        'list': [], # list of variables assigned
                        'last': '', # last variable assigned
                        'iterator': 0, # have we assigned an iterator variable?
                        'endloop': 0 # have we assigned a loop ending variable?
                      }
        return "\n".join(["#include <stdio.h>",
                          "int main()",
                          "{",
                          generate_c(n.node, assignments),
                          "return 0;",
                          "}"])

    elif isinstance(n, Stmt):
        string = ''
        for i in range(len(n.nodes)):
            string += generate_c(n.nodes[i], assignments) + ';\n'
        return string[:-1]

    elif isinstance(n, Printnl):
        string = 'printf(\"'
        for i in range(len(n.nodes)):
            string += '%d '

        string = string[:-1] + '\\n\", '
        for i in range(len(n.nodes)):
            string += '%s, ' % generate_c(n.nodes[i], assignments)

        string = string[:-2] + ')'
        return string

    elif isinstance(n, Const):
        return '%d' % n.value

    elif isinstance(n, UnarySub):
        return '(-%s)' % generate_c(n.expr, assignments)

    elif isinstance(n, Assign):
        return '%s = %s' % (generate_c(n.nodes[0], assignments),
                            generate_c(n.expr, assignments))

    elif isinstance(n, AssName):
        assignments['last'] = n.name
        if n.name not in assignments['list']:
            assignments['list'].append(n.name)
            return 'int %s' % n.name

        return '%s' % n.name

    elif isinstance(n, Name):
        return '%s' % n.name

    elif isinstance(n, Add):
        return '(%s + %s)' % (generate_c(n.left, assignments),
                              generate_c(n.right, assignments))

    elif isinstance(n, For):
        string = ''
        # declare translator loop variables
        if not assignments['iterator']:
            string += 'int '
            assignments['iterator'] = 1
        string += '__MERRIJON_ITER__ = 0;\n'
        if not assignments['endloop']:
            string += 'int '
            assignments['endloop'] = 1
        string += '__MERRIJON_ENDLOOP__ = 0;\n'

        # declare user loop variables
        declaration = '%s;\n' % generate_c(n.assign, assignments)
        if declaration[:3] == 'int':
            string += declaration

        # keep track of variables that have been declared before loop
        assignlist = []
        for var in assignments['list']:
            assignlist.append(var)
        iterator = assignments['last']

        # initialize 'for' header
        string += 'for(%s;' % generate_c(n.list, assignments)
        string += ' __MERRIJON_ITER__++)\n{\n'
        string += '%s = __MERRIJON_ITER__;\n' % iterator

        # translate body of for loop
        string += '%s\n}\n' % generate_c(n.body, assignments)

        # declare all new variables outside of for loop
        for var in assignments['list']:
            if var not in assignlist:
                pattern = 'int %s' % var
                string = re.sub(pattern, var, string)
                string = 'int %s;\n%s' % (var, string)

        return string

    elif isinstance(n, CallFunc):
        string = ''
        # will need to be fixed. This only works for simple range use in loops
        if 'range' == generate_c(n.node, assignments):
            string += '__MERRIJON_ENDLOOP__ = '
            string += '%s; ' % generate_c(n.args[0], assignments)
            string += '__MERRIJON_ITER__ < __MERRIJON_ENDLOOP__'
            return string

        return 'UNEXPECTED'

    else:
        raise sys.exit('Error in generate_c: unrecognized AST node: %s' % n)

if __name__ == "__main__":
    try:
        ast = compiler.parse("\n".join(sys.stdin.readlines()))
        print >> logs, ast # debug
        print generate_c(ast)
    except Exception, e:
        print >> logs, e.args[0]
        exit(-1)
