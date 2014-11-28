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
            # also initialize the epsilon and eof characters
            # to have empty cells as well
            self.table[nonTerminal][EPSILON] = []
            self.table[nonTerminal][EOF] = []
            for terminal in grammar.terminals:
                self.table[nonTerminal][terminal] = []

        # Build the table.
        for lhs in grammar.productions:
            # All right hand sides of a production in the
            # form: A -> alpha1 | alpha2 | alpha3 as a list
            alphas = grammar.productions[lhs]

            # For every right hand side above
            for alpha in alphas:

                #calculate First(alpha) using first dictionary and nullables
                #this is First(alpha[0]) U First(alpha[i]) where i = 1 : len(alpha)
                #and stop i when alpha[i] is not in nullables
                first_of_alpha = create_first_from_list(first_dict, nullables_set, alpha)

                # for all 't' that exist in First(alpha), where 't' is always
                # a terminal
                for t in first_of_alpha:
                    if not t == EPSILON:
                        #add this to the table for 't', don't add it twice
                        if alpha not in self.table[lhs][t]:
                            self.table[lhs][t].append(alpha)

                        # Check for multiple entries in cell - LL1 check.
                        if len(self.table[lhs][t]) > 1:
                            self.isLl1 = False

                # Now, if EPSILON exists in First(alpha), then we have a couple
                # other additions to make
                if EPSILON in first_of_alpha:
                    # For every terminal, t, in Follows(A), add an entry from [A][t] = alpha
                    for t in follows_dict[lhs]:
                        if alpha not in self.table[lhs][t]:
                            self.table[lhs][t].append(alpha)

                        # Check for multiple entries in cell - LL1 check.
                        if len(self.table[lhs][t]) > 1:
                            self.isLl1 = False

                    #Also, if EOF exists in Follows(A), then add entry: [A][EOF] = alpha
                    if EOF in follows_dict[lhs]:
                        if alpha not in self.table[lhs][EOF]:
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