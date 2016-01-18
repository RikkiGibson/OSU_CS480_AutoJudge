#!/usr/bin/env python

__author__ = "Liang Huang & David Winkler"
debug = False;

'''translate the AST parsed by compiler.parse() and generate C code.
   based on Siek's code, but added assignments and for statement.'''

import sys
logs = sys.stderr
import compiler
from compiler.ast import *

# List of variables that have already been declared in our C code
declared = []
c_text = ''

def generate_c(n):
    if isinstance(n, Module):
        if debug: print '\t module'
        c_text = "#include <stdio.h>\n"
        c_text += "int main()\n"
        c_text += "{\n"
        temp_text = '// MAIN FUNCTION BODY\n'
        temp_text += generate_c(n.node)
        
        # If anything is in our list of declarations
        declarations = '// VARIABLE DECLARATIONS\n'
        if declared:
            declarations += 'int ' + ', '.join(declared) + ';\n\n'
        
#        print "#### C TEXT:\n" + c_text + "####"
#        print "#### DECLARATIONS:\n" + declarations + '\n#####'
#        print "#### TEMP TEXT:\n" + temp_text + "\n####"

        c_text = c_text + declarations + temp_text
        c_text += '\nreturn 0;\n}\n'
        return c_text
        
    elif isinstance(n, Stmt):  # only one statement; TODO: handle multiple statements
        if debug: print '\t stmt'
        # Stmt contains an array of nodes. To handle multiple statements, we will
        # need to iterate through all of these nodes...
        # use a for loop to iterate through all the nodes, and append the string
        # returned by generate_c to the string.
        joined = ""
        for node in n.nodes:
            if debug: print node
            joined += (generate_c(node)) + "\n"
        return joined
        #return generate_c(n.nodes[0])
    elif isinstance(n, Printnl): # only support single item; TODO: handle multiple items
        if debug: print '\t printnl'
        # My change: iterate through all the nodes, instead of only node[0].
        # start the printf statement, and add as many %d's as there are arguments 
        # as there are commas (nodes).
        # At the same time, add all of the arguments to a seperate string.
        # Then, concatenate the two to produce a single print statment.
        #return 'printf(\"%%d\\n\", %s);' % generate_c(n.nodes[0])
        format = []
        arguments = []
        for node in n.nodes:
            format.append('%d')
            arguments.append(generate_c(node))
        return 'printf(\"' + ' '.join(format) + '\\n\", ' + ', '.join(arguments) + ');'
    elif isinstance(n, Const):
        if debug: print '\t const'
        return '%d' % n.value
    elif isinstance(n, UnarySub):
        if debug: print '\t unary sub'
        return '(-%s)' % generate_c(n.expr)

    # MY ADDITIONS BELOW #
    elif isinstance(n, Add):
        if debug: print '\t add'
        return '(%s) + (%s)' % (generate_c(n.left), generate_c(n.right))

    # Assignments have a a list of nodes containing the lvalue and an expr rvalue.
    elif isinstance(n, Assign):
        if debug: print '\t assign'
        
        # Assign contains a list of nodes, followed by an expression.
        # First parse the nodes, then apply the expression.
        assignments = ""
        for node in n.nodes:
            assignments += generate_c(node)
        return '%s %s;' % (assignments, generate_c(n.expr))

    # AssName has a name and flags. Flags for now are just OP_ASSIGN (=).
    elif isinstance(n, AssName):
        if debug: print '\t assname'
        # add this name to our list of declarations
        if n.name not in declared:
            declared.append(n.name)  
        # always return the name
        return '%s = ' % n.name

    # Name contains only the name of a thing
    elif isinstance(n, Name):
        return n.name
        
    # For loops contain an assignment, a list of values, a body, and an else
    # range(a) makes a CallFunc node, which has a 
    elif isinstance(n, For):
        # n.list should be a CallFunc node, which should have an args node.
        # Pull the iteration limits from the CallFunc args.
        # The iteration limit will be converted into a string, so no further
        # conversion is necessary.
        if not isinstance(n.list, CallFunc):
            print 'ERROR IN FOR LOOP BOUNDS'
        range = '(' + generate_c(n.list.args[0]) + ')'
        temp_range_var = '_temp_range_var'
        while temp_range_var in declared:
            temp_range_var += '_'
        declared.append(temp_range_var)
        
        # Check what the looping variable is
        loop_var = generate_c(n.assign)
        loop_var = n.assign.name
        
        # Now I have the end bound of the loop, and I have the iterator variable.
        # Now I have to convert the body
        body_text = generate_c(n.body)

        # Make a temp loop var so we can use the actual loop var in the loop without changing the loop range
        temp_loop_var = '_temp_loop_var'
        while temp_loop_var in declared:
            temp_loop_var += '_'
        declared.append(temp_loop_var)
        
        # Now construct the FOR loop.
        # temp_loop_var is what we use for iteration instead of the given loop var.
        # Begin by setting that to 0.
        result = temp_loop_var + ' = 0;\n'
        
        # temp_range_var is the end condition of our loop. 
        # set that equal to the argument given to range().
        result += temp_range_var + ' = ' + range + ';\n'
        
        # Now construct the actual for loop.
        result += "for(; %s < %s; %s++)\n{\n" % (temp_loop_var, temp_range_var, temp_loop_var)
        
        # Now we need to set the given loop var to our temp loop var
        result += "\t%s = %s;\n" % (loop_var, temp_loop_var)
        
        # Now insert the actual body of the FOR loop
        result += '\t' + body_text + '}'
        
#        result = loop_var + ';\n'
#        result += 'for( ; ' + name + '<' + range + '; ' + name + '++)\n'
#        result += '    ' + generate_c(n.body) + '\n'

        # Now adjust the loop variable to behave like python
        #result += name + '--;\n'
        return result
    else:
        if debug: print '\t ELSE'
        raise sys.exit('Error in generate_c: unrecognized AST node: %s' % n)

if __name__ == "__main__":
    try:
        c_text = ''
        ast = compiler.parse("\n".join(sys.stdin.readlines()))
        print >> logs, ast # debug
        print generate_c(ast)
    except Exception, e:
        print "Caught exception"
        print >> logs, e.args[0]
        exit(-1)
