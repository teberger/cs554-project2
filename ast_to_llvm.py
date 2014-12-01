
from cfg import Grammar
from ast_parser import Parser
import pydot
import ast_reductions
import subprocess
import re

#bad practice, but oh well. 
from llvm import *
from llvm.core import *

tp_int = Type.int()
tp_bool = Type.int(1)
tp_main = Type.function(tp_int, [])
gv_results = {}

def reduce_cst_to_llvm(cst):
    llvm_module = Module.new('Arithmetic Code')
    gv_results = {}
    
    f_main = llvm_module.add_function(tp_main, 'main')
    bb = f_main.append_basic_block('entry')
    builder = Builder.new(bb)

    _, post_builder = cst.to_llvm(builder, f_main)

    exit_bb = build_exit(llvm_module, f_main)
    post_builder.branch(exit_bb)

    return llvm_module

def build_exit(llvm_module, f_main):
    exit_bb = f_main.append_basic_block('exit')
    exit_builder = Builder.new(exit_bb)

    #copied from the example code...
    printstring = Constant.stringz('Global variable %s = %d\n')
    gv_printstring = llvm_module.add_global_variable(printstring.type, 'print_fmt')
    gv_printstring.initializer = printstring
    pt_printstring = exit_builder.gep(gv_printstring,
                                      [Constant.int(tp_int, 0),
                                       Constant.int(tp_int, 0)],
                                      inbounds=True)
    
    #creating a prototype for printf
    tp_string = Type.pointer(Type.int(8))
    tp_print = Type.function(Type.void(), [tp_string], var_arg=True)
    f_printf = llvm_module.add_function(tp_print, 'printf')
    
    sorted_keys = gv_results.keys()[0:]
    sorted_keys.sort()
    for gv in sorted_keys:
        value = exit_builder.load(gv_results[gv])
        string_val = Constant.stringz(gv)
        string_val_global = llvm_module.add_global_variable(string_val.type, gv+'_var')
        string_val_global.initializer = string_val
        pt_string = exit_builder.gep(string_val_global,
                                     [Constant.int(tp_int, 0),
                                      Constant.int(tp_int, 0)],
                                     inbounds=True)
                                                            
        exit_builder.call(f_printf, [pt_printstring, pt_string, value])
    exit_builder.ret(Constant.int(tp_int, 0))
    return exit_bb

def ast_to_cst(ast):
    if ast.symbol == 'if':
        boolean_expression = ast_to_cst(ast.children[0])
        then_statement = ast_to_cst(ast.children[1])
        else_statement = ast_to_cst(ast.children[2])

        node = StatementIf(boolean_expression,
                           then_statement, 
                           else_statement)
        
        boolean_expression.parent = node
        then_statement.parent = node
        else_statement.parent = node
        return node
    elif ast.symbol == 'while':
        boolean_expression = ast_to_cst(ast.children[0])
        do_statement = ast_to_cst(ast.children[1])
        node = StatementWhile(boolean_expression, do_statement)
        
        boolean_expression.parent = node
        do_statement.parent = node
        return node

    elif ast.symbol == 'skip':
        return StatementSkip()
    #we have sequential statements and will need to parse them
    #separeately
    elif ';' in [c.symbol for c in ast.children]:
        idx = [c.symbol for c in ast.children].index(';')
        c1 = ast.children[0:idx]
        c2 = ast.children[idx+1:]
        
        ast.children = c1
        s1 = ast_to_cst(ast)
        ast.children = c2
        s2 = ast_to_cst(ast)

        node = StatementSequential(s1, s2)
        s1.parent = node
        s2.parent = node

        return node
    elif ast.symbol == 'S':
        symbols = [c.symbol for c in ast.children]

        if ':=' in symbols:
            var = ast.children[0].value
            rhs = ast_to_cst(ast.children[2])
            node = StatementAssignment(var, rhs)
            rhs.parent = node
            return node
        if 'S' in symbols:
            #skip this node,
            return ast_to_cst(ast.children[symbols.index('S')])
        elif len(symbols) == 1:
            return ast_to_cst(ast.children[0])
        else:
            raise ValueError('should never get here... Symbol:' + str(ast.symbol))
    elif ast.symbol in ['A', 'num', 'var']:
        if ast.symbol == 'A':
            symbols = [c.symbol for c in ast.children]

            if '(' in symbols:
                expr = ast_to_cst(ast.children[1])
                return ArithmeticParenthesized(expr)
            elif 'aop' in symbols:
                lhs = ast_to_cst(ast.children[0])
                op = ast.children[1].value
                rhs = ast_to_cst(ast.children[2])
                
                node = ArithmeticOperation(lhs, op, rhs)
                lhs.parent = node
                rhs.parent = node
                return node

        elif ast.symbol == 'num':
            return ArithmeticNumber(ast.value)
        else:
            return ArithmeticVariable(ast.value)
    elif ast.symbol in ['B', 'true', 'false']:
        if ast.symbol == 'B':
            symbols = [c.symbol for c in ast.children]
            if 'bop' in symbols:
                idx = symbols.index('bop')
                op = ast.children[idx].value

                c1 = ast.children[0:idx]
                c2 = ast.children[idx+1:]
                
                ast.children = c1
                b1 = ast_to_cst(ast)

                ast.children = c2
                b2 = ast_to_cst(ast)

                node = BooleanBinary(b1, op, b2)
                b1.parent = node
                b2.parent = node
                return node
            elif 'not' in symbols:
                b = ast_to_cst(ast.children[1])
                node = BooleanNot(b)
                b.parent = node
                return node
            elif 'relop' in symbols:
                lhs = ast_to_cst(ast.children[0])
                op  = ast.children[1].value
                rhs = ast_to_cst(ast.children[2])
                node = BooleanRelation(lhs, op, rhs)
                lhs.parent = node
                rhs.parent = node
                return node
            else: #true or false value here...
                return BooleanValue(ast.children[0].value)
                
        else:
            return BooleanValue(ast.value)


class ProgramNode:
    def __init__(self):
        pass
    def to_llvm(self, incoming_builder, f_main):
        pass

class StatementWhile(ProgramNode):
    def __init__(self, boolean_expression, do_statement, parent=None):
        self.parent = parent
        self.bool_expr = boolean_expression
        self.do_statement = do_statement

    def to_llvm(self, incoming_builder, f_main):
        exit_block = f_main.append_basic_block('exit')
        exit_builder = Builder.new(exit_block)

        do_block = f_main.append_basic_block('do_block')
        do_builder = Builder.new(do_block)

        b, builder = self.bool_expr.to_llvm(incoming_builder,
                                            f_main)

        #true if b is true, false if b is false
        tmp = builder.icmp(ICMP_NE, b, Constant.int(tp_bool, 0))
        builder.cbranch(tmp, do_block, exit_block)

        self.do_statement.to_llvm(do_builder, f_main)

        do_builder.branch(exit_block)

        return None, exit_builder
        
class StatementIf(ProgramNode):
    def __init__(self, bool_expr, then_statement, else_statement, parent=None):
        self.parent = parent
        self.boolean_expression = bool_expr
        self.then_statement = then_statement
        self.else_statement = else_statement
        
    def to_llvm(self, incoming_builder, f_main):
        exit_block = f_main.append_basic_block('exit')
        exit_builder = Builder.new(exit_block)

        then_block = f_main.append_basic_block('then')
        then_builder = Builder.new(then_block)

        else_block = f_main.append_basic_block('else')
        else_builder = Builder.new(else_block)

        b, builder = self.boolean_expression.to_llvm(incoming_builder,
                                                     f_main)

        tmp = builder.icmp(ICMP_NE, b, Constant.int(tp_bool, 0))
        builder.cbranch(tmp, then_block, else_block)

        _, then_builder = self.then_statement.to_llvm(then_builder,
                                                      f_main)
        then_builder.branch(exit_block)

        _, else_builder = self.else_statement.to_llvm(else_builder,
                                                      f_main)
        else_builder.branch(exit_block)

        return None, exit_builder

class StatementSequential(ProgramNode):
    def __init__(self, s1, s2, parent=None):
        self.parent = parent
        self.s1 = s1
        self.s2 = s2

    def to_llvm(self, incoming_builder, f_main):
        _, builder = self.s1.to_llvm(incoming_builder, f_main)
        ret, builder = self.s2.to_llvm(builder, f_main)
        return ret, builder
        
class StatementAssignment(ProgramNode):
    def __init__(self, var, value, parent=None):
        self.parent = parent
        self.var = var
        self.value = value

    def to_llvm(self, incoming_builder, f_main):
        #calculate the rhs
        v, builder = self.value.to_llvm(incoming_builder, f_main)

        #Is this something we already have a variable for?
        if self.var in gv_results.keys():
            #yes, then just load the value into the ptr
            builder.store(v, gv_results[self.var])
        else:
            #allocate memory for that value
            value_pt = builder.malloc(tp_int, self.var)
            builder.store(v, value_pt)
            gv_results[self.var] = value_pt

        return v, incoming_builder

class StatementSkip(ProgramNode):
    def __init__(self, parent=None):
        self.parent = parent

    def to_llvm(self, incoming_builder, f_main):
        return None, incoming_builder

class ArithmeticParenthesized(ProgramNode):
    def __init__(self, a_statement, parent=None):
        self.parent = parent
        self.expr = a_statement

    def to_llvm(self, incoming_builder, f_main):
        return self.expr.to_llvm(incoming_builder, f_main)

class ArithmeticOperation(ProgramNode):
    def __init__(self, lhs, op, rhs, parent=None):
        self.parent = parent
        self.lhs = lhs
        self.op  = op
        self.rhs = rhs

    def to_llvm(self, incoming_builder, f_main):
        x, builder = self.lhs.to_llvm(incoming_builder, f_main)
        y, builder = self.rhs.to_llvm(builder, f_main)

        if self.op == '+':   ret = builder.add(x, y)
        elif self.op == '-': ret = builder.sub(x, y)
        elif self.op == '*': ret = builder.imul(x, y)
        else: raise ValueError("Error in Arithmetic Operation. Operator was found to be: " + self.op)

        return ret, builder

class ArithmeticNumber(ProgramNode):
    def __init__(self, num, parent=None):
        self.parent = parent
        self.num = num

    def to_llvm(self, incoming_builder, f_main):
        val = Constant.int(tp_int, self.num)
        return val, incoming_builder

class ArithmeticVariable(ProgramNode):
    def __init__(self, var, parent=None):
        self.parent = parent
        self.var = var

    def to_llvm(self, incoming_builder, f_main):
        if self.var in gv_results.keys():
            value = incoming_builder.load(gv_results[self.var])
            return value, incoming_builder
        else:
            print gv_results
            raise ValueError(self.var + " is not in memory yet!")

class BooleanValue(ProgramNode):
    def __init__(self, value, parent=None):
        self.parent = parent
        self.value = value

    def to_llvm(self, incoming_builder, f_main):
        if self.value == 'true':    ret = Constant.int(tp_bool, 1)
        elif self.value == 'false': ret = Constant.int(tp_bool, 0)
        else: raise ValueError("Boolean value is not true of false: " + self.value)

        return ret, incoming_builder
        
class BooleanNot(ProgramNode):
    def __init__(self, boolean_expression, parent=None):
        self.parent = parent
        self.expr = boolean_expression

    def to_llvm(self, incoming_builder, f_main):
        ret, builder = self.expr.to_llvm(incoming_builder, f_main)
        #one's compliment of the return value
        builder.not_(ret)
        return ret, builder

class BooleanBinary(ProgramNode):
    def __init__(self, lhs, boolean_op, rhs, parent=None):
        self.parent = parent
        self.lhs = lhs
        self.op  = boolean_op
        self.rhs = rhs

    def to_llvm(self, incoming_builder, f_main):
        lhs,builder = self.lhs.to_llvm(incoming_builder, f_main)
        rhs,builder = self.rhs.to_llvm(builder, f_main)

        if self.op == '&&':   ret = builder.and_(lhs, rhs)
        elif self.op == '||': ret = builder.or_(lhs, rhs)
        else:raise ValueError('Not a valid boolean self.operator:' + self.op)

        return ret, builder

class BooleanRelation(ProgramNode):
    def __init__(self, lhs, comparison_operator, rhs, parent=None):
        self.parent = parent
        self.lhs = lhs
        self.op  = comparison_operator
        self.rhs = rhs

    def to_llvm(self, incoming_builder, f_main):
        lhs,builder = self.lhs.to_llvm(incoming_builder, f_main)
        rhs,builder = self.rhs.to_llvm(builder, f_main)
        
        if self.op == '<':   ret = builder.icmp(ICMP_SLT, lhs, rhs)
        elif self.op == '<=':ret = builder.icmp(ICMP_SLE, lhs, rhs)
        elif self.op == '=': ret = builder.icmp(ICMP_EQ, lhs, rhs)
        elif self.op == '>=':ret = builder.icmp(ICMP_SGE, lhs, rhs)
        elif self.op == '>': ret = builder.icmp(ICMP_SGT, lhs, rhs)
        elif self.op == '!=':ret = builder.icmp(ICMP_NE, lhs, rhs)
        else: raise ValueError('Not a valid relational self.self.operator:' + self.op)

        return ret, builder

