import sys
import ast
from ast import *
logs = sys.stderr

class Generator():

    def __init__(self):
        self.memo = set()

    def generate_c(self, myast):
        # print "generate_c:"+ast.dump(myast)

        ## Module
        if isinstance(myast, Module):
            main = "\n".join([self.generate_c(item) for item in myast.body])
            assign = "int "+", ".join(list(self.memo))+";"
            return "\n".join([
                "#include <stdio.h>",
                "",
                "int main()",
                "{",
                assign,
                main,
                "return 0;",
                "}"
            ])

        ## Num, Name
        elif isinstance(myast, Num):
            return str(myast.n)
        elif isinstance(myast, Name):
            var = myast.id
            self.memo.add(var)
            return var

        ## BinOp, Add, UnaryOp, USub
        ## Assume binary operator can only be Add, unary operator can only be USub.
        ## Should add code below if other operators allowed.
        elif isinstance(myast, BinOp):
            left = self.generate_c(myast.left)
            right = self.generate_c(myast.right)
            op = self.generate_c(myast.op)
            return left+" "+op+" "+right
        elif isinstance(myast, Add):
            return "+"
        elif isinstance(myast, UnaryOp):
            left = self.generate_c(myast.op)
            right = self.generate_c(myast.operand)
            return left+right
        elif isinstance(myast, USub):
            return "-"

        ## Assign
        ## Assume only one target be assigned.
        ## Should be changed if multiple targets assigned. 
        elif isinstance(myast, Assign):
            left = self.generate_c(myast.targets[0])
            right = self.generate_c(myast.value)
            return left+" = "+right+";"

        ## For
        ## Support "for 'onevar'[1] in range('expr')[2]: body" only.
        ## Should be extended if
        ##   [1] could be not only one variable, or
        ##   [2] could be not only range()
        elif isinstance(myast, For):
            loopvar = self.generate_c(myast.target)
            looprange = self.generate_c(myast.iter.args[0])
            body = "\n".join(map(self.generate_c, myast.body))
            newvar = loopvar+"_"
            while (newvar in body or
                   newvar in looprange or
                   newvar in self.memo):
                newvar += "_"
            newrange = "rng"
            while (newrange in body or
                   newrange in looprange or
                   newrange in self.memo):
                newrange += "_"
            self.memo.add(newrange)
            return "\n".join([
                newrange+" = "+looprange+";",
                "for ( int "+newvar+" = 0; "+newvar+" < "+newrange+"; "+newvar+" ++)",
                "{",
                loopvar+" = "+newvar+";",
                body,
                "}"
            ])

        ## Print
        elif isinstance(myast, Print):
            left = " ".join(["%d"] * len(myast.values))
            right = ", ".join(map(self.generate_c, myast.values))
            return "printf(\""+left+"\\n\", "+right+");"
        else:
            raise sys.exit("Error in generate_c: unrecognized AST node: "+str(myast))        

if __name__ == "__main__":
    try:
        inputcode = "".join(sys.stdin.readlines())
        myast = ast.parse(inputcode)
        generator = Generator()
        outputcode = generator.generate_c(myast)
        print outputcode
    except Exception, e:
        print >> logs, e.args[0]
        exit(-1)
