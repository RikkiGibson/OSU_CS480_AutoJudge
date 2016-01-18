#!/usr/bin/env python

__author__ = "Liang Huang"

'''translate the AST parsed by compiler.parse() and generate C code.
   based on Siek's code, but added assignments and for statement.'''

import sys
logs = sys.stderr
import compiler
from compiler.ast import *

def init_vars(var_list):
    init_str = ''
    for idx, var in enumerate(var_list):
        init_str += 'int %s_%d;\n' % (var, idx)
    return init_str

def get_name(name, var_list):
    if name not in var_list:
        var_list.append(name)
    return name + '_' + str(var_list.index(name))
    
def generate_c(n, var_list):
    if isinstance(n, Module):
        code_string = generate_c(n.node, var_list)
        initialization_string = init_vars(var_list)
        return "\n".join(["#include <stdio.h>",
                          "int main()",
                          "{", 
                          initialization_string,
                          code_string,
                          "return 0;",
                          "}"])
    
    elif isinstance(n, Stmt):
        stmts = []
        for node in n.nodes:
            stmts.append(generate_c(node, var_list))
        return "\n".join(stmts)
    
    elif isinstance(n, Printnl):
        l1 = len(n.nodes) - 1
        formatString = 'printf(\"' + '%%d' + ' %%d' * l1\
            + '\\n\", ' + '%s' + ', %s' * l1 + ');'
        return formatString % tuple([generate_c(node, var_list) for node in n.nodes])
        #Old
        # return 'printf(\"%%d\\n\", %s);' % generate_c(n.nodes[0])
    
    elif isinstance(n, Const):
        return '%d' % n.value
    
    elif isinstance(n, UnarySub):
        return '(-%s)' % generate_c(n.expr, var_list)
    elif isinstance(n, Add):
        return '(%s)+(%s)' % (generate_c(n.left, var_list), generate_c(n.right, var_list))
    
    elif isinstance(n, Name):
        #idx = var_list.index(n.name)
        #return n.name + '__' + var_list[idx][1] + '_' + idx
        return get_name(n.name, var_list)
    elif isinstance(n, AssName):
        if n.name not in var_list:
            var_list.append(n.name)
        return get_name(n.name, var_list)
    elif isinstance(n, Assign):
        return '%s = %s;' % (generate_c(n.nodes[0], var_list), generate_c(n.expr, var_list))
    
    elif isinstance(n, For):
        #Assume simple for loop: for i in range(expr): simple_statment
        lim = generate_c(n.list.args[0], var_list)
        i = get_name(n.assign.name, var_list)
        return '\nfor(int %s_=0, %s__ = %s; %s_ < %s__; %s_++){{\n%s=%s_;\n%s\n}}\n'\
              % (i, i, lim, i, i, i, i, i, generate_c(n.body, var_list))
    else:
        raise sys.exit('Error in generate_c: unrecognized AST node: %s' % n)

if __name__ == "__main__":        
    try:
        ast = compiler.parse("\n".join(sys.stdin.readlines()))
        print >> logs, ast # debug
        print generate_c(ast, [])
    except Exception, e:
        print >> logs, e.args[0]
        exit(-1)


#Return type, string for type checking
