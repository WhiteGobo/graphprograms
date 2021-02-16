import networkx as netx
from .constants import DATAGRAPH_DATATYPE as DATATYPE
from .constants import DATAGRAPH_EDGETYPE as EDGETYPE

class datagraph( netx.MultiDiGraph ):
    def __init__( self, *args, **argv ):
        super().__init__( *args, **argv )
        self._equivalent_list = set( self )

    def add_node( self, node_id, datatype=None ):
        if datatype:
            super().add_node( node_id, **{DATATYPE: datatype} )
        else:
            super().add_node( node_id )

    def add_edge( self, firstnode, secondnode=None, edgetype=None ):
        if secondnode:
            if edgetype:
                super().add_edge( firstnode, secondnode, **{EDGETYPE: edgetype})
            else:
                super().add_edge( firstnode, secondnode )
        else:
            super().add_edge( firstnode )

    def copy( self ):
        newgraph = datagraph()
        for node, data in self.nodes( data=True ):
            newgraph.add_node( node, data[ DATATYPE ] )
        for node1, node2, key, data in self.edges( data=True, keys=True ):
            newgraph.add_edge( node1, node2, data[ EDGETYPE ] )
        return newgraph

    def add_edges_from( self, *args ):
        if not args[0]:
            return super().add_edges_from( *args )
        else:
            return

    def test_valid( self ):
        chk1 = self.nodes() == netx.get_node_attributes( self, DATATYPE ).keys()
        chk2 = self.edges() == netx.get_edge_attributes( self, EDGETYPE ).keys()
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
    nodetype_source = None
    nodetype_target = None
    def __init__( self, name, doc=str()):
        #if not ( isinstance( nodetype_source, datatype ) \
        #        and isinstance( nodetype_target, datatype ) ):
        #    raise Exception()
        self.name = str( name )
        self.doc = str( doc )

        self._register()

    def _register( self ):
        global edgetype_name
        global edgetype_vec
        global edgetype
        q = edgetype_name.setdefault( self.name, list() )
        q.append( self )

        q = edgetype_vec.setdefault( self.name, list() )
        q.append( self )

        edgetype.append( self )
