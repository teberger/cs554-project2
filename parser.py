__author__ = 'Taylor'

from parsetable import ParseTable
from cfg import Grammar
from ll1_tools import first, follows

class Parser:
    '''
    Data structure wrapping a grammar and parse table together
    '''

    def __init__(self, grammar=None):
        #storing this just in case
        self.grammar = grammar
        #start the stack with just the start node
        self.parse_stack = [grammar.start]
        #construct the parse table
        self.table = ParseTable(grammar).table

    def ll1_parse(self, rose_tree, token_list):
        '''
        :param rose_tree: a Rose_Tree of the current node we are parsing
        :param token_list: a list of terminal tokens to parse into a tree structure
        :return: RoseTree, [tokens]: the RoseTree is the AST of the parse and the
                                     list of tokens are the unconsumed tokens
        '''

        # if the stack is empty, return the current parse and leftover input
        if not self.parse_stack:
            return rose_tree, token_list

        # if there's no tokens left and we are here, parse error
        if not token_list:
            raise ValueError("Unexpected EOF, current parse stack is:" + str(self.parse_stack.reverse()))

        # Get the first symbol
        current_symbol = self.parse_stack.pop()
        # one token look-ahead
        token = token_list[0]

        #if we have a matching symbol and token, we can consume the input
        if current_symbol in self.grammar.terminals:
            leaf = Rose_Tree(current_symbol, token)
            return leaf, token_list[1:]

        #else we have a non-terminal, we must continue with the rewrite
        #returns a list of possible productions that should follow
        production_to_follow = self.table[current_symbol][token]

        # if empty production to follow, unexpected terminal found:
        if not production_to_follow:
            raise ValueError("Unexpected terminal, " + str(token) + ", found.")

        # we can't handle this in LL1 style parsing
        if len(production_to_follow) > 1:

            print production_to_follow
            raise ValueError("Too many possible parses for LL1, this is non-deterministic. "
                             "Please check your grammar. Current parse: " +
                             str(self.parse_stack[0:-1]) + " on terminal " + str(token))

        # push all symbols onto the stack
        for symbol in production_to_follow[0][::-1]:
            self.parse_stack.append(symbol)

        #construct a node in the tree and attach all children parsed
        current_rose_tree_node = Rose_Tree(current_symbol, "")

        leftover = token_list

        for symbol in production_to_follow[0]:
            print self.parse_stack[::-1]
            #this can never just return from an empty stack since we place
            #all symbols found on the stack before this. See lines 54 & 55
            parsed_tree_node, leftover = self.ll1_parse(current_rose_tree_node, leftover)

            # append as a child
            current_rose_tree_node.children.append(parsed_tree_node)

            # point back to parent
            parsed_tree_node.parent = current_rose_tree_node

        #finished parsing for this node completely, return the node and any leftover input
        return current_rose_tree_node, leftover

class Rose_Tree:
    def __init__(self, symbol, node_value):
        '''
        :param node_name:
        :param node_value:
        :param children:
        :return:
        '''
        self.symbol = symbol
        self.value = node_value
        self.children = []
        self.parent = None

    def __str__(self):
        ret = "Symbol: " + str(self.symbol) + ", val=" + str(self.value) + '\n'

        for child in self.children:
            ret += str(child)

        return ret