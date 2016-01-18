#!/usr/bin/env python

__author__ = "Max Eliaser"

import sys
logs = sys.stderr
import compiler
import copy
from compiler.ast import *

# before we output any of the code for the child scope, we output any
# declarations used by the child scope but not by the parent
def get_declarations_for_scope (parent_scope, child_scope):
    
    diff = child_scope.difference (parent_scope)
    if len (diff):
        return "int %s;" % (', '.join (list (diff)))
    return ""

# All variables accessible to Python code have a prefix added to their names.
# That way, variables created by the translator for use only by the C code
# can omit the prefix and thus will never be accessible to Python code.
user_pfx = "py_var_"

# For creating unique internal (non-Python-accessible) variables
internal_var_num = 0

def get_internal_var ():
    
    global internal_var_num
    
    internal_var_num += 1
    return "internal_var_%d" % (internal_var_num - 1)

def generate_c (n, indent, scope):
    def recurse (n, indent = indent, scope = scope):
        return generate_c (n, indent, scope)
    if isinstance (n, Module):
        new_scope = copy.copy (scope)
        main_contents = generate_c (n.node, indent + "    ", new_scope)
        return "\n".join ([indent + "#include <stdio.h>",
                            indent + "int main ()",
                            indent + "{",
                            indent + "    " + get_declarations_for_scope (scope, new_scope),
                            main_contents,
                            indent + "    return 0;",
                            indent + "}"])
    elif isinstance (n, Stmt):
        return indent + ('\n' + indent).join (map (recurse, n.nodes))
    elif isinstance (n, Printnl):
        return 'printf (\"%s\\n\", %s);' % (' '.join (["%d"] * len (n.nodes)), ', '.join (map (recurse, n.nodes)))
    elif isinstance (n, Const):
        return '%d' % n.value
    elif isinstance (n, UnarySub):
        return '(-%s)' % recurse (n.expr)
    elif isinstance (n, Assign):
        return ' = '.join (map (recurse, n.nodes + [n.expr])) + ";"
    elif isinstance (n, AssName):
        scope.add (user_pfx + n.name)
        return user_pfx + n.name
    elif isinstance (n, Name):
        return user_pfx + n.name
    elif isinstance (n, Add):
        return '%s + %s' % (recurse (n.left), recurse (n.right))
    elif isinstance (n, For):
        assert isinstance (n.list, CallFunc)
        assert isinstance (n.list.node, Name)
        assert n.list.node.name in ("range", "xrange")
        assert len (n.list.args) == 1
        py_limit_val = recurse (n.list.args[0])
        assert isinstance (n.assign, AssName)
        py_idx = recurse (n.assign)
        backup_limit = get_internal_var ()
        scope.add (backup_limit)
        hidden_idx = get_internal_var ()
        loop_body = recurse (n.body, indent + "    ")
        return "{1} = {2};\n{0}for (int {3} = 0; {3} < {1}; {3}++) {{\n{0}    {4} = {3};\n{5}\n{0}}}".format (
            indent, backup_limit, py_limit_val, hidden_idx, py_idx, loop_body
        )
    else:
        raise sys.exit ('Error in generate_c: unrecognized AST node: %s' % n)

if __name__ == "__main__":        
    ast = compiler.parse ("\n".join (sys.stdin.readlines ()))
    #print >> logs, ast # debug
    print generate_c (ast, "", set ())
