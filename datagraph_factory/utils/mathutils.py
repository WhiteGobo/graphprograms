import numpy as np

class id_to_graph_translator():
    """
    translates between id (int) to a graph
    The graph should consist of n possible nodes and m possible edges 
    between every node. Edges will be directed.
    """
    def __init__( self, number_nodes, number_different_edges ):
        self.size = np.math.comb( number_nodes ) \
                    * number_of_edges_in_complete_graph( number_nodes )
        

def number_of_edges_in_complete_graph( number_vertices ):
    return (number_vertices*(number_vertices-1))/2
