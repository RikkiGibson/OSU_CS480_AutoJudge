#!/usr/bin/env python
__author__ = "Sean Hoyo"
__skeleauthor__ = "Liang Huang"

'''translate the AST parsed by compiler.parse() and generate C code.
   based on Siek's code, but added assignments and for statement.'''

import sys
logs = sys.stderr
import compiler
from compiler.ast import *
names = []
def generate_c(n):
    global names
    if isinstance(n, Module):
        return "\n".join(["#include <stdio.h>",
                          "int main()",
                          "{", 
                          generate_c(n.node), 
                          "return 0;",
                          "}"])
    elif isinstance(n, Stmt):  #Generate for any number of statements
        return "\n".join(map(generate_c, n.nodes))
    elif isinstance(n, Printnl): #Generate for printing any number of expressions
        return "printf(\"" + (len(n.nodes)*"%d ")[:-1] +"\\n\"" + len(n.nodes)*", %s" % tuple(map(generate_c, n.nodes)) + ");" 
    elif isinstance(n, Const):
        return '%d' % n.value
    elif isinstance(n, UnarySub):
        return '(-%s)' % generate_c(n.expr)
    elif isinstance(n, Add):
        return '%s + %s' % (generate_c(n.left), generate_c(n.right))
    elif isinstance(n, Assign):
        if n.nodes[0].name in names:
            return n.nodes[0].name + '=' + generate_c(n.expr) + ';'
        else:
            names.append(n.nodes[0].name)     
            return 'int ' + n.nodes[0].name + '=' + generate_c(n.expr) + ';'
    elif isinstance(n, Name):
        return n.name
    elif isinstance(n, For):
        blk = '';

        for o in n.body.nodes:#place variables declared in body outside
            if isinstance(o, Assign) and o.nodes[0].name not in names:
                names.append(o.nodes[0].name)
                blk += 'int ' + o.nodes[0].name + ';\n'

        if n.assign.name not in names: #Place given iterable outside loop
            names += n.assign.name
            blk += "int " + n.assign.name + ' = 0;\n'

        iterable = "_i"
        while iterable in names: iterable = '_' + iterable #Create a new iterable (search for valid name)
        names.append(iterable)
    
        condition = "_x"
        while condition in names: condition = '_' + condition
        names.append(condition)

        blk += "int " + condition + "=" + generate_c(n.list.args[0]) + ";\n"
    
        #Setup for loop
        blk += "for(int " + iterable + "=0;" + iterable + "<" + condition + ";++" + iterable + "){\n"
        blk += n.assign.name + " = " + iterable + ";\n" + generate_c(n.body) + "\n}"

        #New iterable is scoped so remove it
        names.remove(iterable)
        return blk      
    else:
        raise sys.exit('Error in generate_c: unrecognized AST node: %s' % n)

if __name__ == "__main__":
    try:
        ast = compiler.parse("\n".join(sys.stdin.readlines()))
        print >> logs, ast# debug
        print generate_c(ast)
    except Exception, e:
        print >> logs, e.args[0];
        exit(-1)
