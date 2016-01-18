#!/usr/bin/env python

__author__ = "Liang Huang"

'''translate the AST parsed by compiler.parse() and generate C code.
   based on Siek's code, but added assignments and for statement.'''

import sys
logs = sys.stderr
import compiler
from compiler.ast import *

seen = {}
def generate_c(n):
    if isinstance(n, Module):
        return "\n".join(["#include <stdio.h>",
                          "int main()",
                          "{ int temp = 0; int temp1 = 0; int temp2 = 0; int temp3=0; int temp4=0; int temp5=0;", 
                          generate_c(n.node), 
                          "return 0;",
                          "}"])
    elif isinstance(n, Stmt):  # only one statement; TODO: handle multiple statements
        s0=""
        for s1 in n.nodes:
            s0+=generate_c(s1) + "\n"
        return s0
    #    return generate_c(n.nodes[0])
    elif isinstance(n, Printnl): # only support single item; TODO: handle multiple items
        s0= 'printf(\"'
        count = 0
        space = ' '
        for s1 in n.nodes:
            if count > 0:
                s0+=space
            count+=1
            gen = generate_c(s1)
            #if gen is not None:
            s0+='%d'
        s0+='\\n\"'
        for s2 in n.nodes:
            gen = generate_c(s2)
            #if gen is not None:
            s0+=', %s' % gen
        s0+=');'
        return s0
       # return 'printf(\"%%d\\n\", %s);' % generate_c(n.nodes[0])
    elif isinstance(n, Const):
        return '%d' % n.value
    elif isinstance(n, UnarySub):
        return '(-%s)' % generate_c(n.expr)
    elif isinstance(n, Name):
        return n.name
    elif isinstance(n, AssName):
        if seen.get(n.name):
            return n.name
        else:
            seen[n.name]=1
            return 'int %s' % n.name     
    elif isinstance(n, Assign):
        return '%s = %s;' %(generate_c(n.nodes[0]), generate_c(n.expr))
    elif isinstance(n, Add):
        return '%s + %s' % (generate_c(n.left), generate_c(n.right))
    elif isinstance(n, CallFunc):
        s = ''
        if n.node.name == "range":
            for a in n.args:
                s += generate_c(a)
            return s
    elif isinstance(n, For):
        s = ''
        tempSet = ''
        temp1Set = ''
        varSet = ''
        varSet1 = ''
        tempSetR= ''
        tempSetR1 = ''
        rSet = ''
        rSet1 = ''
        #tempSetA = ''
        tempSetRV = ''
        #varSetA = ''
        #varSetRV = ''
        rangeValue = generate_c(n.list)
        #if not seen.get(n.assign.name):
        initialVar = "%s;" % generate_c(n.assign)    
        tempSetRV = 'temp4 = %s;' % n.assign.name
        tempSetA = 'temp5 = %s;' % n.assign.name
        varSetRV = '%s = temp4;' % n.assign.name
        varSetA = '%s = temp5;' % n.assign.name

        if (isinstance(n.body.nodes[0], Assign)):
            if n.list.node.name == "range":
                for a in n.list.args:
                    if (isinstance(a, Name)):
                       # if a.name == n.assign.name:
                           # tempSetA = 'temp4 = %s;' % a.name
                        #    tempSetRV = 'temp4 = %s;' % a.name
                        #    rangeValue = 'temp4'
                            # varSetA = '%s = temp4;' % a.name
                            # varSetRV = '%s = temp5;' % a.name
                        if a.name == n.body.nodes[0].nodes[0].name:
                            tempSetR = 'temp3 = %s;' % a.name
                            tempSetR1 = 'temp2 = %s;' % a.name
                            rSet1 = '%s = temp2;' % a.name
                            rSet = '%s = temp3;' % a.name
            if n.assign.name == n.body.nodes[0].nodes[0].name:
                tempSet = 'temp = %s;' % n.assign.name
                temp1Set = 'temp1 = %s;' % n.assign.name
                varSet = '%s = temp;' % n.assign.name
                varSet1 = '%s = temp1;' % n.assign.name
            if not seen.get(n.body.nodes[0].nodes[0].name):
                seen[n.body.nodes[0].nodes[0].name] = 1
                s = 'int %s = 0;' % n.body.nodes[0].nodes[0].name
        return '%s temp = 0; temp1 = 0; %s %s %s=0; %s for (%s temp5 < %s; temp5++){%s %s %s %s %s %s %s %s %s %s} temp5--; %s %s %s' % (s, initialVar, tempSetRV, generate_c(n.assign), tempSetA, varSetRV, rangeValue, varSetA, tempSetR, tempSet, generate_c(n.body), tempSetR1, temp1Set, varSet, rSet, tempSetA, varSetRV, varSetA, varSet1, rSet1)
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
