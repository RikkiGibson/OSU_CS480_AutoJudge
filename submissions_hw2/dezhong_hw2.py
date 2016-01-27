import sys
import ast
from ast import *
from collections import defaultdict
logs = sys.stderr

c_keywords = [
    "auto",
    "break",
    "case",
    "char",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "extern",
    "float",
    "for",
    "goto",
    "if",
    "int",
    "long",
    "register",
    "return",
    "short",
    "signed",
    "sizeof",
    "static",
    "struct",
    "switch",
    "typedef",
    "union",
    "unsigned",
    "void",
    "volatile",
    "while"
    ]

other_keywords = [
    "bool"
    ]

mykeywords = set(c_keywords + other_keywords)

class MyInt():
    def __init__(self):
        pass
    def __str__(self):
        return "MyInt"
    def __eq__(self, other):
        return self.__str__() == other

class MyBool():
    def __init__(self):
        pass
    def __str__(self):
        return "MyBool"
    def __eq__(self, other):
        return self.__str__() == other

class MyFunc():
    def __init__(self, *arg):
        self.lst = arg
    def __str__(self):
        return "("+(" -> ".join([str(x) for x in self.lst]))+")"
    def __eq__(self, other):
        return self.__str__() == other
    def gettype(self):
        return self.lst
        
class Generator():

    def __init__(self):
        self.memo_int = set()
        self.memo_bool = set()
        self.vd = defaultdict(str) #variable dict
        # self.temp = set()

    def scan_variables(self, myast):
        self._scan_variables(myast)
        while True:
            flag = True
            cleanset = set()
            for var in self.vd:
                nvar = self.vd[var]
                if nvar in cleanset or nvar in mykeywords:
                    self.vd[var] = nvar+"_"
                    flag = False
                    break
                else:
                    cleanset.add(nvar)
            if flag == True:
                break
        self.varset = cleanset
        return
        
    def _scan_variables(self, myast):
        print >> logs, "_scan_variables: %s" % ast.dump(myast)
        if isinstance(myast, Module):
            for item in myast.body:
                self._scan_variables(item)
            return
        elif isinstance(myast, Name):
            ## only consider True, False, and variables
            var = myast.id
            if var == "True" or var == "False":
                return
            else:
                self.vd[var] = var
                return
        elif isinstance(myast, BinOp):
            self._scan_variables(myast.left)
            self._scan_variables(myast.right)
            return
        elif isinstance(myast, UnaryOp):
            self._scan_variables(myast.operand)
            return
        elif isinstance(myast, BoolOp):
            for item in myast.values:
                self._scan_variables(item)
            return
        elif isinstance(myast, Compare):
            self._scan_variables(myast.left)
            for item in myast.comparators:
                self._scan_variables(item)
            return
        elif isinstance(myast, IfExp):
            self._scan_variables(myast.test)
            self._scan_variables(myast.body)
            self._scan_variables(myast.orelse)
            return
        elif isinstance(myast, Assign):
            ## only support single target assignment
            self._scan_variables(myast.targets[0])
            self._scan_variables(myast.value)
            return
        elif isinstance(myast, If):
            self._scan_variables(myast.test)
            for item in myast.body:
                self._scan_variables(item)
            return
        elif isinstance(myast, For):
            self._scan_variables(myast.target)
            ## only consider the iter is range(expr)
            self._scan_variables(myast.iter.args[0])
            for item in myast.body:
                self._scan_variables(item)
            return
        elif isinstance(myast, Print):
            for item in myast.values:
                self._scan_variables(item)
            return
        else:
            return

    def generate_c(self, myast, mytype = None):
        print >> logs, "generate_c:"+ast.dump(myast), mytype

        ## Module
        if isinstance(myast, Module):
            requiretype = None
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            main = "\n".join([self.generate_c(item, None)[0] for item in myast.body])
            assign_int = "int "+", ".join(list(self.memo_int))+";" if len(self.memo_int) != 0 else ""
            assign_bool = "mybool "+", ".join(list(self.memo_bool))+";" if len(self.memo_bool) != 0 else ""
            return "\n".join([
                "#include <stdio.h>",
                "typedef enum {false, true} mybool; //define type bool",
                "",
                "int main()",
                "{",
                assign_int+" //declare all global variables: int",
                assign_bool+" //declare all global variables: bool",
                "",
                main,
                "",
                "return 0;",
                "}"
            ]), None

        ## Num, Name
        ## Name only supports True, False, and variables
        ## Should be changed if other stuff allowed.
        elif isinstance(myast, Num):
            requiretype = MyInt()
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            return str(myast.n), MyInt()

        elif isinstance(myast, Name):
            var = myast.id
            if var == "True" or var == "False":
                requiretype = MyBool()
                assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
                return var.lower(), MyBool()
            else:
                if isinstance(mytype, MyInt):
                    ## This does not support dynamic typing
                    if var in self.memo_bool:
                        raise "VariableTypeError:%s should be %s, used as %s" % (var, mytype, MyBool())
                    var = self.vd[var]
                    self.memo_int.add(var)
                    return var, mytype
                elif isinstance(mytype, MyBool):
                    ## This does not support dynamic typing
                    if var in self.memo_int:
                        raise "VariableTypeError:%s should be %s, used as %s" % (var, mytype, MyInt())
                    var = self.vd[var]
                    self.memo_bool.add(var)
                    return var, mytype
                else:
                    raise "TypeError: unknown type %s; in %s" % (mytype, ast.dump(myast))

        ## BinOp, Add, Sub, UnaryOp, USub
        ## Assume binary operator can only be Add and Sub, unary operator can only be USub and Not.
        ## Should add code below if other operators allowed.
        elif isinstance(myast, BinOp):
            requiretype = MyInt()
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            op, _ = self.generate_c(myast.op, MyFunc(mytype, mytype, mytype))
            left, _ = self.generate_c(myast.left, mytype)
            right, _ = self.generate_c(myast.right, mytype)
            return "("+left+" "+op+" "+right+")", mytype
        elif isinstance(myast, Add):
            requiretype = MyFunc(MyInt(), MyInt(), MyInt())
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            return "+", mytype
        elif isinstance(myast, Sub):
            requiretype = MyFunc(MyInt(), MyInt(), MyInt())
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            return "-", mytype
        elif isinstance(myast, UnaryOp):
            requiretypelist = [MyInt(), MyBool()]
            assert mytype in requiretypelist, "TypeError: require %s, get %s; in %s" % (" or ".join(requiretypelist), mytype, ast.dump(myast))
            op, _ = self.generate_c(myast.op, MyFunc(mytype, mytype))
            oprand, _ = self.generate_c(myast.operand, mytype)
            return op+"("+oprand+")", mytype
        elif isinstance(myast, USub):
            requiretype = MyFunc(MyInt(), MyInt())
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            return "-", mytype
        elif isinstance(myast, Not):
            requiretype = MyFunc(MyBool(), MyBool())
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            return "!", mytype

        ## BoolOp, And, Or
        elif isinstance(myast, BoolOp):
            requiretype = MyBool()
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            op, _ = self.generate_c(myast.op, MyFunc(mytype, mytype, mytype))
            values = map(lambda x:self.generate_c(x, mytype)[0], myast.values)
            return "("+values[0]+" "+op+" "+values[1]+")", mytype
        elif isinstance(myast, Or):
            requiretype = MyFunc(MyBool(), MyBool(), MyBool())
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            return "||", mytype
        elif isinstance(myast, And):
            requiretype = MyFunc(MyBool(), MyBool(), MyBool())
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            return "&&", mytype

        ## Compare, Eq, NotEq, Lt, LtE, Gt, GtE
        elif isinstance(myast, Compare):
            requiretype = MyBool()
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            try:
                left, lefttype = self.generate_c(myast.left, MyInt())
            except:
                left, lefttype = self.generate_c(myast.left, MyBool())
            
            for i in range(len(myast.ops)):
                right, _ = self.generate_c(myast.comparators[i], lefttype)
                op, _ = self.generate_c(myast.ops[i], MyFunc(lefttype, lefttype, mytype))
                if i == 0:
                    result = left+" "+op+" "+right
                else:
                    result += " && "+left+" "+op+" "+right
                left = right
            return "("+result+")", mytype
        elif isinstance(myast, Eq):
            requiretypelist = [MyFunc(MyInt(), MyInt(), MyBool()), MyFunc(MyBool(), MyBool(), MyBool())]
            assert mytype in requiretypelist, "TypeError: require %s, get %s; in %s" % (" or ".join(requiretypelist), mytype, ast.dump(myast))
            return "==", mytype
        elif isinstance(myast, NotEq):
            requiretypelist = [MyFunc(MyInt(), MyInt(), MyBool()), MyFunc(MyBool(), MyBool(), MyBool())]
            assert mytype in requiretypelist, "TypeError: require %s, get %s; in %s" % (" or ".join(requiretypelist), mytype, ast.dump(myast))
            return "!=", mytype
        elif isinstance(myast, Lt):
            requiretype = MyFunc(MyInt(), MyInt(), MyBool())
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            return "<", mytype
        elif isinstance(myast, LtE):
            requiretype = MyFunc(MyInt(), MyInt(), MyBool())
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            return "<=", mytype
        elif isinstance(myast, Gt):
            requiretype = MyFunc(MyInt(), MyInt(), MyBool())
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            return ">", mytype
        elif isinstance(myast, GtE):
            requiretype = MyFunc(MyInt(), MyInt(), MyBool())
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            return ">=", mytype

        ## IfExp
        elif isinstance(myast, IfExp):
            requiretypelist = [MyInt(), MyBool()]
            assert mytype in requiretypelist, "TypeError: require %s, get %s; in %s" % (" or ".join(requiretypelist), mytype, ast.dump(myast))
            test, _ = self.generate_c(myast.test, MyBool())
            body, _ = self.generate_c(myast.body, mytype)
            orelse, _ = self.generate_c(myast.orelse, mytype)
            return "("+test+"?"+body+":"+orelse+")", mytype
        
        ## Assign
        ## Assume only one target be assigned.
        ## Should be changed if multiple targets assigned. 
        elif isinstance(myast, Assign):
            requiretype = None
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            try:
                right, righttype = self.generate_c(myast.value, MyInt())
            except:
                right, righttype = self.generate_c(myast.value, MyBool())
            left, _ = self.generate_c(myast.targets[0], righttype)
            return left+" = "+right+";", mytype

        
        ## If
        ## Does not support else statement currently
        ## Should be extended if else needed
        elif isinstance(myast, If):
            requiretype = None
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            test, _ = self.generate_c(myast.test, MyBool())
            body = "\n".join(map(lambda x:self.generate_c(x, None)[0], myast.body))
            # orelse = None
            return "\n".join([
                "if (%s)" % test,
                "{",
                body,
                "}"
            ]), None
        
        ## For
        ## Support "for 'onevar'[1] in range('expr')[2]: body" only.
        ## Should be extended if
        ##   [1] could be not only one variable, or
        ##   [2] could be not only range()
        elif isinstance(myast, For):
            requiretype = None
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            loopvar, _ = self.generate_c(myast.target, MyInt())
            looprange, _ = self.generate_c(myast.iter.args[0], MyInt())
            newvar = "i"
            while (newvar in self.varset or
                   # newvar in self.temp or
                   newvar in mykeywords):
                newvar += "_"
            newrange = "rng"
            while (newrange in self.varset or
                   # newrange in self.temp or
                   newrange in mykeywords):
                newrange += "_"
            # self.temp.add(newvar)
            # self.temp.add(newrange)
            body = "\n".join(map(lambda x:self.generate_c(x, None)[0], myast.body))
            # self.temp.remove(newvar)
            # self.temp.remove(newrange)
            return "\n".join([
                "for (int "+newvar+" = 0, "+newrange+" = "+looprange+"; "+newvar+" < "+newrange+"; "+newvar+" ++)",
                "{",
                loopvar+" = "+newvar+";",
                body,
                "}",
            ]), None

        ## Print
        elif isinstance(myast, Print):
            requiretype = None
            assert mytype == requiretype, "TypeError: require %s, get %s; in %s" % (requiretype, mytype, ast.dump(myast))
            lefts = []
            rights = []
            for i in range(len(myast.values)):
                try:
                    right, righttype = self.generate_c(myast.values[i], MyInt())
                except:
                    right, righttype = self.generate_c(myast.values[i], MyBool())
                    right = right+"?\"True\":\"False\""
                rights.append(right)
                if righttype == MyInt():
                    lefts.append("%d")
                else:
                    lefts.append("%s")
            left = " ".join(lefts)
            right = ", ".join(rights)
            return "printf(\""+left+"\\n\", "+right+");", None

        else:
            raise sys.exit("Error in generate_c: unrecognized AST node: "+ast.dump(myast))        

def c_indent(icode):
    icodelist = icode.split("\n")
    indent = "    "
    ocodelist = []
    indentcnt = 0
    for i in range(len(icodelist)):
        line = icodelist[i]
        if not (line == "{" or line == "}"):
            ocodelist.append(indent*indentcnt+line)
        elif line == "{":
            ocodelist.append(indent*indentcnt+line)
            indentcnt += 1
        elif line == "}":
            indentcnt -= 1
            ocodelist.append(indent*indentcnt+line)
    return "\n".join(ocodelist)
        
if __name__ == "__main__":
    try:
        inputcode = "".join(sys.stdin.readlines())
        myast = ast.parse(inputcode)
        generator = Generator()
        generator.scan_variables(myast)
        outputcode_woindent, _ = generator.generate_c(myast, None)
        outputcode = c_indent(outputcode_woindent)
        print outputcode
    except Exception, e:
        print >> logs, e.args[0]
        exit(-1)
