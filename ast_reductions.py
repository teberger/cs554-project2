
from cfg import Grammar, EOF
from ast_parser import Parser, Rose_Tree
import pydot

def simplify_ast(ast):
    '''Reduces the AST to a concrete syntax tree (CST), which removes
    all the extraneous non-terminal symbols and creates a logical 
    program structure.

    For example a _while_ loop should be represented as it's own tree
    node, with a single node with 2 children: the boolean expression
    to test and the contents of the while loop.

    while loops and if statements are condensed, and sequential
    statements (S ; S) are put into one serial block of
    code. 

    :param ast: a RoseTree that represents the AST of the parse
                of the arithmetic language defined in the 
                homework specification.
    :return: a ProgramTree with the correct code flow and 
             precedence ordering.

    '''
    children_symbols = [c.symbol for c in ast.children if c.value != '']

    #while statements: S -> (while) (B) (do) (S) (od)
    if 'while' in children_symbols:
        return reduceWhile(ast)
    #if statements: S -> (if) (B) (then) (S) (else) (S) (fi)
    elif 'if' in children_symbols:
        return reduceIf(ast)
    #else, leave it as is, this contains valuable information
    #regarding precedence 
    else:
        node = Rose_Tree(ast.symbol, ast.value)
    
        for c in ast.children:
            child_node = reduce_ast(c)
            child_node.parent = node
            node.children.append(child_node)

        return node
        

def find_child_with_symbol(ast, symbol, num=1):
    count = 0
    for c in ast.children:
        if c.symbol == symbol:
            count += 1
            if count == num:
                return c
    return None;

#We know that at this level, the root of the AST is S, we can abstract
#away the S-> ...  and replace it with a simplified rose_tree node
#that represents the appropriate structure
def reduceWhile(ast):
    new_root = Rose_Tree(symbol = 'while', node_value='while')
    new_root.parent = ast.parent

    boolean_child = find_child_with_symbol(ast, 'B')
    while_block = find_child_with_symbol(ast, 'S')

    new_root.children = [reduce_ast(boolean_child), 
                         reduce_ast(while_block)]
    return new_root

#reduces an S -> if .... fi production into a single node with only
#the three children: boolean expression, then statement, and else
#statement
def reduceIf(ast):
    new_root = Rose_Tree(symbol='if', node_value='if')
    new_root.parent = ast.parent
    
    boolean_child = find_child_with_symbol(ast, 'B')
    then_statement = find_child_with_symbol(ast, 'S')
    else_statement = find_child_with_symbol(ast, 'S', 2)

    new_root.children = [reduce_ast(boolean_child),
                         reduce_ast(then_statement),
                         reduce_ast(else_statement)]
    return new_root

#removes all nodes that were created from using epsilon productions
def filter_epsilon(ast):
    if not ast.children and (ast.value == ''): 
        return None
    else:
        children = [filter_epsilon(c) for c in ast.children]
        tree = Rose_Tree(ast.symbol, ast.value)
        tree.children = filter(lambda x: x is not None, children)
        return tree

#compresses nodes with only one children since they do not contribute
#to the actual structure of the language
def reduce_singleton_children(ast):
    #leaf nodes always stay the same
    if len(ast.children) == 0:
        return ast
    
    #else, we only have one child, remove ourselves from the equation
    elif len(ast.children) == 1:
        new_child = reduce_singleton_children(ast.children[0])
        return new_child
    else:
        children = ast.children[0:len(ast.children)]
        ast.children = []
        
        for c in children:
            new_child = reduce_singleton_children(c)
            ast.children.append(new_child)

        return ast

#removes all A -> A' edges and condenses them into a the A node like
#we originally wanted in our grammar
def remove_ll1_requirement_syntax(ast):            
    symbol = ast.symbol
    
    children = ast.children[0:]
    
    reduce_node = None

    for c in children:
        if (symbol + "'") == c.symbol:
            reduce_node = c

    if reduce_node is not None:
        ast.children.remove(reduce_node)
        for c in reduce_node.children:
            ast.children.append(c)

    for c in ast.children:
        remove_ll1_requirement_syntax(c)


def reduce_ast(ast):
    '''The compilation of all reductions possible into the smallest AST
    that still maintains grammar structure. See filter_epsilon,
    simplify_ast, reduce_singleton_children, and
    remove_ll1_requirement_syntax.

    '''
    root = filter_epsilon(ast)
    root = simplify_ast(root)
    root = reduce_singleton_children(root)
    remove_ll1_requirement_syntax(root)
    return root

if __name__ == '__main__':
    g = Grammar('./testdata/homework1_grammar.txt')
    x = Parser(g)

    root, _ = x.ll1_parse([('if', 'if'),
                           ('(', '('),
                           ('num', '1'),
                           (')', ')'),
                           ('relop','<'), 
                           ('num', '1'),
                           ('then','then'), 
                           ('var', 'x'),
                           (':=', ':='),
                           ('num','123'),
                           ('aop', '+'),
                           ('num', '5'),
                           ('else', 'else'),
                           ('while', 'while'),
                           ('var', 'x'),
                           ('relop', '<'),
                           ('num', '10'),
                           ('do', 'do'),
                           ('var', 'x'),
                           (':=',':='),
                           ('var', 'x'),
                           ('aop', '+'),
                           ('num', '1'),
                           ('fi', 'fi'),
                           ('\0', '\0')
                       ])

    root = reduce_ast(root)
    graph = pydot.Dot('Parse Tree', graph_type='digraph')
    g, _ = root.pydot_append(graph, 0)
    g.write_png('./testdata/test.png')

