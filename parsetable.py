#!/usr/bin/env python

class ParseTable:
    """ Represents a parse table. """

    def __init__(self, grammar):
        self.table = dict()
        self.ll1 = True

        for nonTerminal in grammar.nonTerminals:
            self.table[nonTerminal] = dict()
            for terminal in grammar.terminals:

                productions = grammar.productions[nonTerminal]
                productions = [x for x in productions if terminal in x]
                if len(productions) > 1: self.ll1 = False
                self.table[nonTerminal][terminal] = productions
