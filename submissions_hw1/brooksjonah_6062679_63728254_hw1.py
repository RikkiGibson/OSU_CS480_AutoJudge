#!/usr/bin/env python

__author__ = "Jonah Brooks"

'''translate the AST parsed by compiler.parse() and generate C code.
   based on Siek's code, but added assignments and for statement.'''

'''Implements the P_1 cfg defined as follows:
   program : module
   module : stmt+
   stmt : (simple_stmt | for_stmt) NEWLINE
   simple_stmt : "print" expr ("," expr)*
               | name "=" expr

   for_stmt : "for" name "in" "range" "(" expr ")" ":" simple_stmt

   expr : name
        | decint
        | "-" expr
        | expr "+" expr
        | "(" expr ")"
'''

import sys
logs = sys.stderr
import compiler
from compiler.ast import *

prelude = set([])
first_pass = True

def generate_c(n):
    global prelude
    if isinstance(n, Module):
        out_prelude = ''
        if first_pass == False:
          for assignment in prelude:
            out_prelude = out_prelude + "int " + assignment + " = 0;\n"
          return "\n".join(["#include <stdio.h>",
                             "int main()",
                             "{", 
                             out_prelude,
                             generate_c(n.node), 
                             "return 0;",
                             "}"])
        else:
          prelude = set([])
          generate_c(n.node)
          return prelude
    elif isinstance(n, Stmt): 
        out = '' 
        for node in n.nodes:
            out = out + generate_c(node) + '\n'
        return out
    elif isinstance(n, Printnl): 
        out = 'printf(\"'
        for i in range(len(n.nodes)):
          out = out + '%d'
          if i < len(n.nodes)-1:
            out = out + ' '
        out = out + '\\n\"'
        for node in n.nodes:
          out = out + ', %s' % generate_c(node)
        out = out + ');'

        return out
    elif isinstance(n, Const):
        return '%d' % n.value
    elif isinstance(n, Name):
        return '%s' % n.name
    elif isinstance(n, UnarySub):
        return '(-%s)' % generate_c(n.expr)
    elif isinstance(n, Add):
        out = ''
        out = out + '%s + ' % generate_c(n.left)
        out = out + '%s' % generate_c(n.right)
        return out
    elif isinstance(n, Assign):
        name = generate_c(n.nodes[0])
        out = ''
        if name in prelude:
            out = '%s = ' % name
            out = out + generate_c(n.expr) + ';'
        else:
            prelude.add(name) # Just add this to prelude; nothing else matters since this is a first pass
        return out
    elif isinstance(n, AssName):
        return '%s' % n.name
    elif isinstance(n, For):
        # for_stmt : "for" name "in" "range" "(" expr ")" ":" simple_stmt
        out = ''
        index_var = generate_c(n.assign)
        orig_index_var = index_var
        if index_var in prelude:
            while index_var in prelude:
              index_var = index_var + '_' # Add underscores until this name is unique
            out = out + 'int %s = 0;\n' % index_var
            if first_pass == False:
              prelude.add(index_var) # Won't declare at top, will prevent duplicates later
        else:
            prelude.add(index_var) # Just add this to prelude; nothing else matters since this is a first pass
        reference_var = generate_c(n.list.args[0]) 
        orig_reference_var = reference_var
        reference_var = 'tmp'
        while reference_var in prelude:
          reference_var = reference_var + '_'
        if first_pass == False:
          prelude.add(reference_var) # Won't declare at top, will prevent duplicates later
        out = out + 'int ' + reference_var + ' = ' + orig_reference_var + ';\n'
        out = out + 'for(' + index_var + ' = 0; '
        out = out + index_var + ' < ' + reference_var + '; '
        out = out + index_var + '++' + ')\n'
        out = out + '{\n'
        out = out + '\t' + orig_index_var + ' = ' + index_var + ';\n'
        out = out + '\t' + generate_c(n.body)
        out = out + '}'
        return out
    else:
        raise sys.exit('Error in generate_c: unrecognized AST node: %s' % n)


if __name__ == "__main__":        
    try:
        ast = compiler.parse("\n".join(sys.stdin.readlines()))
        print >> logs, ast # debug
        generate_c(ast) # Fill prelude with variable assignments
        first_pass = False
        print generate_c(ast)
    except Exception, e:
        print >> logs, e.args[0]
        exit(-1)
