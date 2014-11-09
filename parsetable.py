#!/usr/bin/env python
from ll1_tools import *
from cfg import EOF, EPSILON


class ParseTable:
    """ Represents a parse table. """

    def __init__(self, grammar):
        self.table = dict()
        self.isLl1 = True
        self.grammar = grammar

        first_dict = first(grammar)
        follows_dict = follows(grammar)
        nullables_set = nullable(grammar)

        # Initialize all table cells to the empty list.
        for nonTerminal in grammar.nonTerminals:
            self.table[nonTerminal] = dict()
            self.table[nonTerminal][EPSILON] = []
            self.table[nonTerminal][EOF] = []
            for terminal in grammar.terminals:
                self.table[nonTerminal][terminal] = []

        # Build the table.
        for lhs in grammar.productions:
            alphas = grammar.productions[lhs]

            for alpha in alphas:

                first_of_alpha = create_first_from_list(first_dict, nullables_set, alpha)

                for t in first_of_alpha:
                    self.table[lhs][t].append(alpha)

                    # Check for multiple entries in cell - LL1 check.
                    if len(self.table[lhs][t]) > 1:
                        self.isLl1 = False

                if EPSILON in first_of_alpha:
                    print first_of_alpha
                    print alpha
                    for t in follows_dict[lhs]:
                        self.table[lhs][t].append(alpha)

                        # Check for multiple entries in cell - LL1 check.
                        if len(self.table[lhs][t]) > 1:
                            self.isLl1 = False

                    if EOF in follows_dict[lhs]:
                        print 'eof found'
                        self.table[lhs][EOF].append(alpha)
                        # Check for multiple entries in cell - LL1 check.
                        if len(self.table[lhs][EOF]) > 1:
                            self.isLl1 = False

    def __str__(self):
        """ Output to CSV format for viewing with a spreadsheet program. """
        ret = ""

        # Print row headers
        for header in self.grammar.terminals:
            ret += ',' + header
        ret += '\n'

        # Print rows
        for row in self.table:
            ret += row
            for col in self.table[row]:
                ret += ',' + str(self.table[row][col]).replace(',', ' ')
            ret += "\n"

        return ret

if __name__ == "__main__":
    g = Grammar("testdata/ll1.txt")
    fs = first(g)
    fl = follows(g)
    pt = ParseTable(g)
    print fs, '\n'
    print fl, '\n'
    print pt
