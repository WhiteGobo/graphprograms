import networkx as netx

class behaviourtree():
    def __init__( self, tree ):
        if not netx.tree.is_tree( tree ):
            raise TypeError(f"given graph is no tree, see {netx.tree.__name__}")


class behaviourleaf():
    prestatus = None #type == datagraph
    poststatus = None #type == datagraph
    cost = None
    def __call__( self ):
        raise Exception(f"{self.__call__.__qualname__} wasnt correctly "\
                            + "implemented")

class inner

class innerknot_sequence( behaviourleaf ):
    branchdutylist = list()
    def __init__( self ):
        #doing something with the branchdutylist
        pass
