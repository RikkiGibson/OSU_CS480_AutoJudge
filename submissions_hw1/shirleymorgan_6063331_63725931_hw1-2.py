#!/usr/bin/env pygthon

__author__ = "Liang Huang"

'''translate the AST parsed by compiler.parse() and generate C code.
   based on Siek's code, but added assignments and for statement.'''

import sys
logs = sys.stderr
import compiler
from compiler.ast import *


def next_string(n):
    '''http://stackoverflow.com/a/932536/1572816'''
    strip_zs = n.rstrip('z')
    if strip_zs:
        return strip_zs[:-1] + chr(ord(strip_zs[-1]) + 1) + 'a' * (len(n) - len(strip_zs))
    else:
        return 'a' * (len(n) + 1)

def find_names(n):
    assignedlist = []
    if isinstance(n, Module):
        for node in n.node.nodes:
            assignedlist += find_names(node)
    elif isinstance(n, Stmt):
        assignedlist += find_names(n.nodes[0])
    elif isinstance(n, Assign):
        if generate_c(n.nodes[0]) not in assignedlist:
            assignedlist.append(generate_c(n.nodes[0]))
    elif isinstance(n, For):
        if generate_c(n.assign) not in assignedlist:
            assignedlist.append(generate_c(n.assign))
        assignedlist += find_names(n.body)
    # no other situations require further recursion
    assignedlist = list(set(assignedlist))
    return assignedlist

safe_loop_var = "i"
safe_limit_var = "j"

def generate_c(n):
    global safe_loop_var
    global safe_limit_var
    assignedlist = []
    if isinstance(n, Module):
        assignedlist = find_names(n)
        while assignedlist.count(safe_loop_var) == 1:
            safe_loop_var = next_string(safe_loop_var)
        assignedlist.append(safe_loop_var)
        while assignedlist.count(safe_limit_var) == 1:
            safe_limit_var = next_string(safe_limit_var)
        assignedlist.append(safe_limit_var)
        initstring = "int "
        for variable in assignedlist:
            initstring += "%s, " % variable
        initstring = initstring[:-2]
        initstring += ";"
        prog = ["#include <stdio.h>",
                "int main()",
                "{",
                initstring]
        for node in n.node.nodes:
            prog.append(generate_c(node))
        prog.append("return 0;")
        prog.append("}")
        return "\n".join(prog)
    elif isinstance(n, Stmt):
        return generate_c(n.nodes[0])
    elif isinstance(n, Printnl): 
        percent_ds = ""
        values_to_print = ""
        for i in range(len(n.nodes) - 1):
            percent_ds += '%d '
            values_to_print += "%s, " % generate_c(n.nodes[i])
        percent_ds += '%d'
        values_to_print += "%s" % generate_c(n.nodes[-1])
        return 'printf(\"%s\\n\", %s);' % (percent_ds, values_to_print)
    elif isinstance(n, Const):
        return '%d' % n.value
    elif isinstance(n, UnarySub):
        return '(-%s)' % generate_c(n.expr)
    elif isinstance(n, Assign):
        if generate_c(n.nodes[0]) not in assignedlist:
            assignedlist.append(generate_c(n.nodes[0]))
        return '%s = %s;' % (generate_c(n.nodes[0]), generate_c(n.expr))
    elif isinstance(n, AssName) or isinstance(n, Name):
        return '%s' % n.name
    elif isinstance(n, Add):
        return '%s + %s' % (generate_c(n.left), generate_c(n.right))
    elif isinstance(n, For):
        if generate_c(n.assign) not in assignedlist:
            assignedlist.append(generate_c(n.assign))
        return "%s = %s;\nfor(%s = 0; %s < %s; %s++) {\n  %s = %s;\n  %s\n}" % ( 
                safe_limit_var, generate_c(n.list.args[0]),
                safe_loop_var, safe_loop_var, 
                safe_limit_var, safe_loop_var,
                generate_c(n.assign), safe_loop_var,
                generate_c(n.body))
    else:
        print " "
        print n.__dict__
        print " "
        raise sys.exit('Error in generate_c: unrecognized AST node: %s' % n)

if __name__ == "__main__":        
    try:
        ast = compiler.parse("\n".join(sys.stdin.readlines()))
        print >> logs, ast # debug
        print generate_c(ast)
    except Exception, e:
        print >> logs, e.args[0]
        exit(-1)
