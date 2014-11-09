#!/usr/bin/env python
from ll1_tools import *
from cfg import EOF

class ParseTable:
    """ Represents a parse table. """

    def __init__(self, grammar):
        self.table = dict()
        self.isLl1 = True

        first_dict = first(grammar)
        follows_dict = follows(grammar)
        nullables_set = nullable(grammar)

        # initialize table to include empty cells
        for nonTerminal in grammar.nonTerminals:
            self.table[nonTerminal] = dict()
            for terminal in grammar.terminals:
                self.table[nonTerminal][terminal] = []


        for lhs in grammar.productions:
            alphas = grammar.productions[lhs]
            for alpha in alphas:
                first_of_alpha = create_first_from_list(first_dict, nullables_set, alpha)
                for t in first_of_alpha:
                    self.table[lhs][t].append(alpha)
                    if len(self.table[lhs][t]) > 1:
                        self.isLl1 = False

                if [] in first_of_alpha:
                    for t in follows_dict[lhs]:
                        self.table[lhs][t].append(alpha)
                        if len(self.table[lhs][t]) > 1:
                            self.isLl1 = False

                    if EOF in follows_dict[lhs]:
                        self.table[lhs][EOF].append(alpha)
                        if len(self.table[lhs][EOF]) > 1:
                            self.isLl1 = False

