#!/usr/bin/env python

import sys
import compiler
from compiler.ast import *
logs = sys.stderr

__author__ = "Rikki Gibson"

'''translate the AST parsed by compiler.parse() and generate C code.
   based on Siek's code, but added assignments and for statement.'''


def generate_c(n):
    """
    :type n: Node
    :rtype: str
    """

    if isinstance(n, Module):
        return "\n".join(["#include <stdio.h>",
                          "int main()",
                          "{",
                          generate_c_names(n.node),
                          generate_c(n.node),
                          "return 0;",
                          "}"])
    elif isinstance(n, Stmt):
        return "\n".join([generate_c(stmt) for stmt in n.nodes])
    elif isinstance(n, Printnl):
        format_specifiers = " ".join(["%d" for _ in n.nodes])
        expressions = ", ".join([generate_c(expr) for expr in n.nodes])
        return "printf(\"" + format_specifiers + "\\n\", " + expressions + ");"
    elif isinstance(n, Const):
        return '%d' % n.value
    elif isinstance(n, UnarySub):
        return '(-%s)' % generate_c(n.expr)
    elif isinstance(n, Add):
        return '(%s + %s)' % (generate_c(n.left), generate_c(n.right))
    elif isinstance(n, Assign):
        ass_name = n.nodes[0]
        assert isinstance(ass_name, AssName)
        return '%s = %s;' % (ass_name.name, generate_c(n.expr))
    elif isinstance(n, Name):
        return n.name
    elif isinstance(n, For):
        return generate_for(n)
    else:
        raise sys.exit('Error in generate_c: unrecognized AST node: %s' % n)


# TODO: write a real solution for loop limit variable
def generate_names(node):
    """
    :type node: Node
    :return: set(str)
    """

    if isinstance(node, Module):
        return generate_names(node.node)

    if isinstance(node, Assign):
        return generate_names(node.nodes[0])

    if isinstance(node, AssName):
        return set([node.name])

    if isinstance(node, For):
        return generate_names(node.assign).union(generate_names(node.body))

    if hasattr(node, 'nodes'):
        names = set()
        for n in node.nodes:
            names = names.union(generate_names(n))
        return names

    return set()


def generate_c_names(root):
    """
    :type root: Node
    :return:
    """

    names = generate_names(root).union(["raise"])
    if len(names) != 0:
        return "int " + ", ".join(names) + ";"
    return ""


def generate_for(n):
    """
    :type n: For
    :rtype: str
    """
    # Declare variable if not exists
    assert isinstance(n.assign, AssName)
    result = ""
    var_name = n.assign.name

    assign_expr = generate_c(n.list.args[0])  # range(expr)

    # I'm using pass so that no Python script can use this variable.
    # TODO: need to save assign_expr to a variable so it can't change during loop
    assign_stmt = "int pass = 0;"  # i = 0
    cond_stmt = "pass < raise;"
    modify_stmt = "pass++"

    result += "raise = %s;\n" % assign_expr
    result += "for (%s %s %s) {\n" % (assign_stmt, cond_stmt, modify_stmt)
    result += "%s = pass;\n" % var_name
    result += generate_c(n.body.nodes[0])
    result += "\n}\n"

    return result


if __name__ == "__main__":        
    try:
        ast = compiler.parse("\n".join(sys.stdin.readlines()))
        print >> logs, ast  # debug
        print generate_c(ast)
    except Exception, e:
        print >> logs, e.args[0]
        exit(-1)
