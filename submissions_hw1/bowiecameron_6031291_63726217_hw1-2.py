#!/usr/bin/env python

__author__ = "Liang Huang"

'''translate the AST parsed by compiler.parse() and generate C code.
   based on Siek's code, but added assignments and for statement.'''

import sys
logs = sys.stderr
import compiler
from compiler.ast import *

def get_id(ids, pyid=None, cid=None, internal=False):
	if pyid == cid == None:
		return None

	for i in ids:
		if (pyid == i["pyid"] or pyid == None) and \
		   (cid == i["cid"] or cid == None) and \
		   i["internal"] == internal:
				return i

def is_defined(ids, pyid=None, cid=None, internal=False):
	return get_id(ids, pyid, cid, internal) != None

def generate_decl(ids, d=0):
	decl = ""
	for i in ids:
		if not i["internal"]:
			decl += d * "\t" + "%s %s;\n" % (i["type"], i["cid"])

	return decl

def add_id(ids, name, idType, internal=False):
	new_id = {}
	new_id["pyid"] = name
	new_id["cid"] = "%s_%d" % (name, len(ids))
	new_id["type"] = idType
	new_id["internal"] = internal

	ids.append(new_id)

def generate_c(n, d=0, ids=[]):
	indent = d * "\t"

	if isinstance(n, Module):
		body = generate_c(n.node, d, ids);
		decl = generate_decl(ids, d + 1)

		return "\n".join([indent + "#include <stdio.h>",
		                  indent + "int main()",
		                  indent + "{",
		                  decl,
		                  body, 
		                  indent + "\treturn 0;",
		                  indent + "}"])
	elif isinstance(n, Stmt):
		return "\n".join([generate_c(node, d + 1, ids) for node in n.nodes])
	elif isinstance(n, Printnl):
		code = indent + 'printf(\"'
		code += '%d ' * len(n.nodes)
		code = code[:-1] + '\\n\"'
		code += "".join([', %s' % generate_c(node, d + 1, ids) for node in n.nodes])

		return code + ');'
	elif isinstance(n, Const):
		return '%d' % n.value
	elif isinstance(n, UnarySub):
		return '(-%s)' % generate_c(n.expr, d, ids)
	elif isinstance(n, Add):
		return '%s + %s' % (generate_c(n.left, d, ids), generate_c(n.right, d, ids))
	elif isinstance(n, Name):
		return '%s' % get_id(ids, n.name)["cid"]
	elif isinstance(n, Assign):
		if not is_defined(ids, n.nodes[0].name):
			add_id(ids, n.nodes[0].name, "int")

		return indent + '%s = %s;' % (get_id(ids, n.nodes[0].name)["cid"], generate_c(n.expr, d, ids))
	elif isinstance(n, For):
		if not is_defined(ids, n.assign.name):
			add_id(ids, n.assign.name, "int")

		iterNum = len(ids)
		iterType = "int"
		
		add_id(ids, "FOR_ITER%d" % iterNum, iterType, internal=True)
		add_id(ids, "FOR_END%d" % iterNum, iterType, internal=True)

		iterId = get_id(ids, n.assign.name)
		intIterId = get_id(ids, "FOR_ITER%d" % iterNum, internal=True)
		intEndId = get_id(ids, "FOR_END%d" % iterNum, internal=True)

		return '{indent}for({intType} {intId} = 0, {intEndId} = {end}; {intId} < {intEndId}; {intId}++){{\n{indent}\t{iterId} = {intId};\n{body}\n{indent}}}'.format(iterId=iterId["cid"],
		                                            intId=intIterId["cid"],
		                                            intType=intIterId["type"],
		                                            body=generate_c(n.body, d, ids),
		                                            end=generate_c(n.list.args[0], d + 1, ids),
		                                            intEndId=intEndId["cid"],
		                                            indent=indent)

	else:
		raise sys.exit('Error in generate_c: unrecognized AST node: %s' % n)

if __name__ == "__main__":        
	try:
		ast = compiler.parse("\n".join(sys.stdin.readlines()))
		print >> logs, ast # debug
		print generate_c(ast)
	except Exception, e:
		print e.args[0]
		exit(-1)
