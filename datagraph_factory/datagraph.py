import networkx as netx
weisfeiler_lehmann_graph_hash = netx.graph_hashing.weisfeiler_lehman_graph_hash
from .constants import \
        DATAGRAPH_DATATYPE as DATATYPE,\
        DATAGRAPH_EDGETYPE as EDGETYPE, \
        DATAGRAPH_CONTAINED_DATA as CONTAINED_DATA

class datagraph( netx.MultiDiGraph ):
    """
    This is a datagraph
    """
    def __init__( self, *args, **argv ):
        super().__init__( *args, **argv )
        self._equivalent_list = set( self )

    def __setitem__( self, key, item ):
        try:
            self.nodes[key][ CONTAINED_DATA ] = item
        except KeyError as err:
            raise KeyError( "Item assignment only valid "
                        "for existing nodes" ) from err

    def __getitem__( self, key ):
        try:
            return self.nodes[key][ CONTAINED_DATA ]
        except KeyError as err:
            if key in self.nodes():
                raise KeyError( f"no data found for node {key}" ) from err
            else:
                raise KeyError( "Item fetching only valid for " \
                                "existing nodes" ) from err

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

            source_target_pairs = edgetype.get_source_target_pair_function()
            given_type_pair = tuple((self.nodes[firstnode][DATATYPE], \
                                    self.nodes[secondnode][DATATYPE]))
            if given_type_pair not in source_target_pairs:
                raise Exception(("datatypes of source (%s) and target (%s) "\
                                +"isnt compatible to typepairlist (%s) as "\
                                +"described by edgetype") \
                                %(self.nodes[firstnode][DATATYPE], \
                                self.nodes[secondnode][DATATYPE], \
                                source_target_pairs))
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
        raise Exception()
        return other in self._equivalent_list

    def same_structure_as( self, otherdatagraph ):
        """
        controls if this datagraph and another datagraph share the same
        graph in regard of datatypes and edgetypes
        """
        return self.weisfeil_hash() == otherdatagraph.weisfeil_hash()

    def nodelist_of_datatype( self, datatype ):
        return [ n for n in self.nodes() if self.nodes[n][DATATYPE] == datatype]
    
    def _check_if_all_nodes_completed( self ):
        for n in self.nodes:
            if CONTAINED_DATA not in self.nodes[ n ]:
                return False
        return True
    completed = property( fget=_check_if_all_nodes_completed )

    def get_completed_datanodes( self ):
        for n in self.nodes:
            data = self.nodes[ n ]
            if CONTAINED_DATA in data.keys():
                yield n

    def get_completed_datanode_border( self, not_completed_nodes=False ):
        """
        return completed datanodes which have a not-completed datanode as 
        neighbour, or vice-versa if not_completed_nodes
        """
        completed_list, not_completed_list = list(), list()
        for n in self.nodes:
            data = self.nodes[ n ]
            if CONTAINED_DATA in data.keys():
                completed_list.append( n )
            else:
                not_completed_list.append( n )
        neighbours = list()
        if not_completed_nodes:
            for n in completed_list:
                neighbours.extend( self.predecessors( n ) )
                neighbours.extend( self.successors( n ) )
            neighbours = set( neighbours ).difference( completed_list )
        else:
            for n in not_completed_list:
                neighbours.extend( self.predecessors( n ) )
                neighbours.extend( self.successors( n ) )
            neighbours = set( neighbours ).difference( not_completed_list )
        return neighbours


    def get_data_as_dictionary( self ):
        return netx.get_node_attributes( self, CONTAINED_DATA )

    def weisfeil_hash( self ):
        replicate_graph = netx.MultiDiGraph()
        replicate_graph.add_nodes_from( self.nodes() )
        replicate_graph.add_edges_from( self.edges() )
        tmp = netx.get_node_attributes( self, NODETYPE )
        tmp = { node: repr(value) for node, value in tmp.items() }
        netx.set_node_attributes( replicate_graph, tmp )
        netx.get_edge_attributes( self, EDGETYPE )
        tmp = { edge: repr(value) for edge, value in tmp.items() }
        netx.set_edge_attributes( replicate_graph, tmp )
        return int( weisfeiler_lehmann_graph_hash( replicate_graph, \
                                                    EDGETYPE, NODETYPE ), 16 )


edgetype_name = {}
edgetype_vec = {}
datatype_name = {}

edgetype = list()

class datatype():
    """
    This class is for saving data of the datagraph. Every data in datagraph
    is contained in node of childrenclasses of datatype:
    eg:
    class text( datatype ):
        def __init__( self, mytext ):
            self.text = mytext
    You can access via mydatagraph.nodes["nodename"].text
    Within a proccess an attribute will be given containing you object:
    def myprocess( nodename ):
        print( nodename.text )

    When you wan code to be save- and loadable create the functions 
    save_as( self, pathtotargetfile ) and load_from( self, pathtofile )
    """
    def _check_saveability( self ):
        try:
            self.save_as
            self.load_from
            return True
        except AttributeError:
            return False
    saveable = property( fget=_check_saveability )


class edgetype():
    def __init__( self, get_source_target_pair_function, name, doc ):
        self.__doc__ = doc
        self.__name__ = name
        self.get_source_target_pair_function = get_source_target_pair_function

    def get_source_target_pair_function( self ):
        return get_source_target_pair_function()

    def __repr__( self ):
        return self.__name__
        return object.__repr__( self )
    def __str__( self ):
        return self.__name__

