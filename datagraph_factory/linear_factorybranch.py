import copy
import networkx as netx
from .processes import factory_leaf
from .find_process_path import datastate_from_graph
from .find_process_path import datastate
from .constants import DATAGRAPH_EDGETYPE as EDGETYPE
import math

def create_linear_function( flowgraph, inputgraph, outputgraph, verbosity=0 ):
    """
    :type flowgraph: .find_process_path.flowgraph
    """
    node_to_datatype = flowgraph.node_to_datatype

    try:
        translator = flowgraph.translator( inputgraph, outputgraph )
    except KeyError as err:
        err.args = (*err.args, "cant create function for the purpose of "\
                        "creating the outputgraph from the inputgraph."\
                        " Please adjust those graphs or given flowgraph" )
        if verbosity > 0:
            err.args = (*err.args, f"input: {inputgraph.nodes(data=True)};;;; "\
                        +f";;;;{inputgraph.edges(data=True)}, output: "\
                        +f"{outputgraph.nodes(data=True)};;;; "\
                        +f"{outputgraph.edges(data=True)}",\
                        "for supported graphs by flowgraph, please use "\
                        +"flowgraph.nodes()" )
        else:
            err.args = (*err.args, "for more information "\
                        +"create_linear_function( ..., verbosity = 1 )")
        raise err
    
    current_datastate = datastate_from_graph( flowgraph, \
                                    netx.relabel_nodes(inputgraph, translator))
    target_datastate = datastate_from_graph( flowgraph, \
                                    netx.relabel_nodes(outputgraph, translator))

    flowcontroller = linearflowcontroller( flowgraph, target_datastate )

    def call_function( **args ):
        if set( inputgraph.nodes() ) != args.keys():
            raise KeyError( f"wrong input needed: {inputgraph.nodes()} "\
                            f"and got {args.keys()}" )
        mydatacontainer = { translator[ key ]:value \
                            for key, value in args.items() }
        flowcontroller.myflowgraph.datastate = current_datastate

        flowcontroller.data = mydatacontainer
        
        while flowcontroller.next_step():
            pass

        mydatacontainer = flowcontroller.data

        return_translator = \
                { \
                translator[ value ] : value \
                for value in outputgraph.nodes()
                if translator[ value ] in mydatacontainer \
                }
        return { value: mydatacontainer[ key ] \
                for key, value in return_translator.items() }
    call_function.__doc__ = "\n\tinputvariables are %s\n" \
                                %( inputgraph.nodes(data=True) )

    my_linear_function = factory_leaf( inputgraph, outputgraph, call_function )

    return my_linear_function


class linearflowcontroller():
    def __init__( self, myflowgraph, outputgraph, ):
        self.node_to_datatype = myflowgraph.node_to_datatype
        nextnode_from_state, possible_datastate_at_output \
                    = self.find_nextnode_from_state( myflowgraph, outputgraph )
        process_lib = self.create_process_lib( nextnode_from_state, myflowgraph)

        self.process_lib = process_lib
        self.nextnode_from_state = nextnode_from_state
        self.possible_datastate_at_output = possible_datastate_at_output
        self.myflowgraph = myflowgraph

    def create_process_lib( self, nextnode_from_state, myflowgraph ):
        processlib = dict()
        edgefunction = netx.get_edge_attributes( myflowgraph, "edgefunction" )
        weightfunction = netx.get_edge_attributes( myflowgraph, "weight" )
        for source, target in nextnode_from_state.items():
            tmpedges = [(source, target, i) \
                        for i in range( \
                        myflowgraph.number_of_edges( source, target )) ]
            get_min = lambda x: weightfunction[ x ]
            usededge = min( tmpedges, key=get_min )
            processlib[ source ] = edgefunction[ usededge ]
        return processlib


    def _get_data( self ):
        return self.myflowgraph.data
    def _set_data( self, data ):
        self.myflowgraph.data = dict( data )
    data = property( fget = _get_data, fset = _set_data )

    def next_step( self ):
        if self.myflowgraph.datastate in self.process_lib:
            self.process_lib[ self.myflowgraph.datastate ]()
            return True
        else:
            return False


    def find_nextnode_from_state( self, flowgraph, outputstate ):
        """
        :return mypaths:
        :rtype mypaths:
        :return possible_datastate_at_output:
        :rtype possible_datastate_at_output:
        """
        possible_datastate_at_output = flowgraph.get_superstates_to(outputstate)

        filter_path_possoutput = lambda tmpdict: { key:value \
                                    for key, value in tmpdict.items() \
                                    if key in possible_datastate_at_output }

        distances = netx.all_pairs_dijkstra_path_length( flowgraph )
        distances = { node1: filter_path_possoutput( target_dict) \
                    for node1, target_dict in distances }
        failstates = [ state for state, distdict in distances.items() \
                        if not distdict ]
        nearest_set = lambda distdict: min( distdict, key = distdict.get )
        mindist = { key: nearest_set( distdict ) \
                        for key, distdict in distances.items() \
                        if key not in failstates }

        all_paths = netx.all_pairs_dijkstra_path( flowgraph )
        mypaths = { source: target_dict[ mindist[ source ]][ 1 ] \
                    for source, target_dict in all_paths \
                    if source not in possible_datastate_at_output \
                    and source not in failstates }
        return mypaths, possible_datastate_at_output
