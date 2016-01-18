#!/usr/bin/env python
#CS480
#HW1

__author__ = "Benjamin Narin"

'''translate the AST parsed by compiler.parse() and generate C code.
   based on Siek's code, but added assignments and for statement.'''

import sys
import random
import string
logs = sys.stderr
import compiler
from compiler.ast import *

def temp_var_gen(array_var, size=5, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    temp = "TEMP_"+"".join(random.choice(chars) for _ in range(size))
    if temp in array_var:
        temp_var_gen([array_var])
    else:
         return temp

def generate_c(array_var, n):
    if isinstance(n, Module):
        code = generate_c(array_var, n.node)
        var_def = ""
        for i in array_var:
            var_def += "int " + i + ";\n"
        return "\n".join(["#include <stdio.h>",
                          "int main()",
                          "{",
                          var_def,
                          code,
                          "return 0;",
                          "}"])
    elif isinstance(n, Stmt):
        code = ""
        for i in n.nodes:
            code += generate_c(array_var, i)
            code += '\n'
        return code
    elif isinstance(n, Printnl):
        code = ""
        print_num = len(n.nodes)
        code += ("printf(\"" + print_num * "%d ")[:-1] + "\\n\""
        code += ","
        for i in n.nodes:
            code += (generate_c(array_var, i) + ",")
        code = code[:-1]
        code += ");"
        return code
        # return 'printf(\"%%d\\n\", %s);' % generate_c(n.nodes[0])
    elif isinstance(n, Const):
        return '%d' % n.value
    elif isinstance(n, UnarySub):
        return '(-%s)' % generate_c(array_var, n.expr)
    elif isinstance(n, Add):
        return '(%s + %s)' % (generate_c(array_var, n.left), generate_c(array_var, n.right))
        # return '(+%s)' % generate_c(n.expr)
    elif isinstance(n, Assign):
        if not n.nodes[0].name in array_var:
            array_var.append(n.nodes[0].name)
        return '%s = %s;' % (n.nodes[0].name, generate_c(array_var, n.expr))
    elif isinstance(n, Name):
        return '%s' % (n.name)
    elif isinstance(n, For):
        code = ""
        if not n.assign.name in array_var:
            array_var.append(n.assign.name)
        temp_var = temp_var_gen(array_var)
        code += ("for(int {name} = 0, end = {val}; {name} < end; {name}++){{\n") .format(name = temp_var, val = generate_c(array_var, n.list.args[0]))
        code += '%s = %s;\n' % (n.assign.name, temp_var)
        code += '%s' % generate_c(array_var, n.body)
        code += "}"
        return code
    else:
        raise sys.exit('Error in generate_c: unrecognized AST node: %s' % n)

if __name__ == "__main__":
    # try:
    #     ast = compiler.parse("\n".join(sys.stdin.readlines()))
    #     print >> logs, ast # debug
    #     print generate_c(ast)
    # except Exception, e:
    #     print >> logs, e.args[0]
    #     exit(-1)
    array_var = []
    ast = compiler.parse("\n".join(sys.stdin.readlines()))
    print >> logs, ast # debug
    print generate_c(array_var, ast)
