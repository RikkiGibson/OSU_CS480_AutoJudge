#!/usr/bin/env python

__author__ = "Liang Huang, Evan Schallerer"

'''translate the AST parsed by compiler.parse() and generate C code.
   based on Siek's code, but added assignments and for statement.'''

import sys
logs = sys.stderr
import compiler
from compiler.ast import *

#Definition for size of a tab
TAB = '    '

# replaces the last n of 'old' in string s with 'new'
# Source: http://stackoverflow.com/questions/2556108/how-to-replace-the-last-occurence-of-an-expression-in-a-string
# Accessed: 1/13/2015
def rreplace(s, old, new, n):
    return new.join(s.rsplit(old, n))

# returns a string consisting of numTabs tabs
def addTabs(numTabs):
    tabs = ''
    for i in range(numTabs):
        tabs += TAB
    return tabs

# Takes in the parsed code and a set of variables declared
# Returns a declaration for each of the variables declared
def initAllVariables(n, vars, scope):
    vars = findAllVariables(n, vars)
    return addTabs(scope) + 'int ' + ', '.join(list(vars)) + ';'
    
# Takes in the parsed code and a set of variables
# Returns a set of all of the variables declared
def findAllVariables(n, vars):
    if isinstance(n, Module):
        return findAllVariables(n.node, vars)
    
    elif isinstance(n, Stmt):
        for node in n.nodes: 
            findAllVariables(node, vars)
        return vars 
        
    elif isinstance(n, For):
        return findAllVariables(n.body, vars).add(findAllVariables(n.assign, vars))
    
    elif isinstance(n, Assign):
        for node in n.nodes:
           vars.add(node.name)
        return vars
    
    elif isinstance(n, AssName):
        return '%s' % n.name

# Returns a 'var' with '_' appended to it until
# it is no longer contained in vars
def getUniqueName(vars, var):
    newVar = var + '_' 
    while newVar in vars:
        newVar += '_'
    return newVar        

   
# Params: 'For' node, set of variables declared, current scope 
# Returns the string that makes up a for loop
def generateForLoop(n, vars, scope):
    i = getUniqueName(vars, n.assign.name) #loop variable
    vars.add(i)
    loopInit = addTabs(scope) + 'int ' + i + ';\n'
    newVar = generate_c(n.list, vars, scope)
    
    for arg in n.list.args: #arguments of range function
        if isinstance(arg, Name): #if it is a variable (not a constant)
            newVar = getUniqueName(vars, arg.name)
            vars.add(newVar)
            loopInit += addTabs(scope) + 'int %s = %s;\n' % (newVar, arg.name)
    #NOTE: Can only handle one argument to range!
    return addTabs(scope).join([loopInit,
            'for(%s = 0; %s < %s; %s++){\n' % (i, i, newVar, i),
            addTabs(scope) + '%s = %s;\n' % (n.assign.name, i) + generate_c(n.body, vars, scope+1),
            '\n}'])

    #return value


#generates C code recursively
def generate_c(n, vars, scope):
    if isinstance(n, Module):
        scope += 1
        vars = findAllVariables(n.node, set())
        return "\n".join(["#include <stdio.h>",
                          "int main()",
                          "{",
                          addTabs(scope) +"int %s;" % (", ".join(list(vars))),
                          generate_c(n.node, vars, scope), 
                          addTabs(scope) + "return 0;",
                          '//Variables: ' + ', '.join(list(vars)),
                          "}"])
    
    elif isinstance(n, Stmt):  
        statements = []
        for node in n.nodes:
            statements.append(generate_c(node, vars, scope))
        return '\n'.join(statements) 
    
    elif isinstance(n, Printnl):
        value = ''
        for node in n.nodes:
            value += addTabs(scope) + 'printf(\"%%d \", %s);\n' % generate_c(node, vars, scope)
        # add newline in printf, remove trailing \n 
        return rreplace(value, '\"%d \"', '\"%d\\n\"', 1)[:-1]
    
    elif isinstance(n, Const):
        return '%s' % n.value
    
    elif isinstance(n, UnarySub):
        return '(-%s)' % generate_c(n.expr, vars, scope)
    
    elif isinstance(n, Add): 
		return '%s + %s' % (generate_c(n.left, vars, scope), 
                            generate_c(n.right, vars, scope))
                            
    elif isinstance(n, Assign):
        assName = generate_c(n.nodes[0], vars, scope)
        value = '%s = %s;' % (assName, generate_c(n.expr, vars, scope))
        return addTabs(scope) + value
        
    elif isinstance(n, AssName):  
        return '%s' % n.name
    
    elif isinstance(n, Name):
        return '%s' % n.name
        
    elif isinstance(n, For):
        return generateForLoop(n, vars, scope)

    elif isinstance(n, CallFunc):  
        if n.node.name == 'range':
			return generate_c(n.args[0], vars, scope)
        else :
            raise sys.exit('Error in generate_c: unknown function: %s' % n.node.name)
    else:
        raise sys.exit('Error in generate_c: unrecognized AST node: %s' % n)


if __name__ == "__main__":        
    try:
        ast = compiler.parse("\n".join(sys.stdin.readlines()))
        print >> logs, ast # debug
        print generate_c(ast, [], 0)
    except Exception, e:
        print e.args[0]
        exit(-1)