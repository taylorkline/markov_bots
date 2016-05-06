from collections import Counter
import random
"""
A graph module for Markov chains.
"""


class Graph():
    def __init__(self, state=None):
        """
        Initialize a graph dict of key=state, val=neighbors and a current
        state.
        Any given state except None will be considered valid.
        """
        if state is None:
            self._state_key = None
        else:
            self._vertices = {state: Counter()}
            self._state_key = state

    def add_edge(self, next_state):
        """
        Constructs an edge between the most recently updated vertex and a
        vertex with state 'next_state'.
        """
        assert(hasattr(next_state, '__iter__'))
        if self._state_key is None:
            # First token added to the graph.
            self.__init__(next_state)
        else:
            # Add the new state as a vertex in the graph if it's not already.
            if next_state not in self._vertices:
                self._vertices[next_state] = Counter()

            # Construct the edge between the previous token's vertex and the
            # new.
            self._vertices[self._state_key][next_state] += 1

            # Update the new state
            self._state_key = next_state

    def get_random_token(self):
        """
        Returns the token from a yielded neighbor of the current state, if
        possible, or sets and returns a token from a new state at random.
        """
        if self._state_key is None:
            raise ValueError("You must add some data to the graph!")

        try:
            self._state_key = self.yield_neighbor()
        except ValueError:
            # The state had no neighbors, so choose a new state at random.
            self._state_key = random.choice(list(self._vertices))

        return self._state_key[-1]

    def yield_neighbor(self):
        """
        From the current state, yields a random neighbor.
        """
        neighbor_count = sum(self._vertices[self._state_key].values())
        if neighbor_count is 0:
            raise ValueError("The current state has no neighbors.")

        selection = random.randint(1, neighbor_count)

        for neighbor, weight in self._vertices[self._state_key].items():
            # yield a random selection
            selection -= weight
            if selection <= 0:
                return neighbor

        assert(False)   # never reach here

    def __str__(self):
        return str(["State: '{}', Neighbors: '{}'".format(k, v) for k, v
                   in self._vertices.items()])
