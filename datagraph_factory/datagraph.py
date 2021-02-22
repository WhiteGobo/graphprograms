import networkx as netx
from .constants import DATAGRAPH_DATATYPE as DATATYPE
from .constants import DATAGRAPH_EDGETYPE as EDGETYPE

class datagraph( netx.MultiDiGraph ):
    """
    This is a datagraph
    """
    def __init__( self, *args, **argv ):
        super().__init__( *args, **argv )
        self._equivalent_list = set( self )

    def add_node( self, node_id, datatype=None ):
        if datatype:
            super().add_node( node_id, **{DATATYPE: datatype} )
        else:
            super().add_node( node_id )

    def add_edge( self, firstnode, secondnode, edgetype = None ):
        if edgetype:
            errargs = []
            if firstnode not in self.nodes:
                errargs.append( f"node '{firstnode}' must be added before edge")
            if secondnode not in self.nodes:
                errargs.append( f"node'{secondnode}' must be added before edge")
            if errargs:
                raise Exception( *errargs )
            if self.nodes[firstnode][DATATYPE] != edgetype.source:
                errargs.append( f"datatype {self.nodes[firstnode][DATATYPE]} "\
                                +f"of source isnt {edgetype.source}"\
                                +"as described by edgetype" )
            if self.nodes[secondnode][DATATYPE] != edgetype.target:
                errargs.append( f"datatype {self.nodes[secondnode][DATATYPE]} "\
                                +f"of target isnt {edgetype.target}"\
                                +"as described by edgetype" )
            if errargs:
                raise Exception( *errargs )
            super().add_edge( firstnode, secondnode, **{EDGETYPE: edgetype})
        else:
            super().add_edge( firstnode, secondnode )



    def copy( self ):
        if not self.test_valid():
            raise Exception( "cant copy not valid datagraphs. check if "\
                            +"every node and edge has a corresponding "\
                            +"nodetype and edgetype", self.nodes( data=True) )
        newgraph = datagraph()
        for node, data in self.nodes( data=True ):
            newgraph.add_node( node, data[ DATATYPE ] )
        for node1, node2, key, data in self.edges( data=True, keys=True ):
            newgraph.add_edge( node1, node2, data[ EDGETYPE ] )
        return newgraph

    def add_edges_from( self, args ):
        for m in args:
            source, target = m[0], m[1]
            myedgetype = m[-1][EDGETYPE]
            self.add_edge( source, target, myedgetype )

    def test_valid( self ):
        chk1 = set(self.nodes()) \
                == netx.get_node_attributes( self, DATATYPE ).keys()
        chk2 = set(self.edges(keys=True)) \
                == netx.get_edge_attributes( self, EDGETYPE ).keys()
        return chk1 and chk2

    def raise_exception_if_not_valid( self ):
        chk1 = set(self.nodes()) \
                == netx.get_node_attributes( self, DATATYPE ).keys()
        if not chk1:
            raise Exception( "This datagraph is not valid. its nodes are "\
                            f"{self.nodes( data=True ) }. Every node must"\
                            f" contain data to {DATATYPE}" )
        chk2 = set(self.edges( keys=True )) \
                == netx.get_edge_attributes( self, EDGETYPE ).keys()
        if not chk2:
            raise Exception( "This datagraph is not valid. its edges are "\
                            f"{self.edges( data=True ) }. Every edge must"\
                            f" contain data to {EDGETYPE}")

    def set_equivalent_to( self, datagraph_list ):
        self._equivalent_list = set( datagraph_list ).union( set(self) )

    def __eq__( self, other ):
        return other in self._equivalent_list


edgetype_name = {}
edgetype_vec = {}
datatype_name = {}

edgetype = list()

class datatype():
    """ This is the base class """
    pass


class edgetype():
    def __init__( self, source, target, name, doc ):
        self.source = source
        self.target = target
        self.__doc__ = doc
        self.__name__ = name

    def __repr__( self ):
        return self.__name__
