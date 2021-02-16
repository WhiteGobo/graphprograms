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
        #edge[i] is: i=  0:sourcenode; 1:targetnode; -1:data
        edgecontainer = list([(edge[0], edge[1], edge[-1][ EDGETYPE ]) \
                            for edge \
                            in inputgraph.edges( data=True ) ])
                            #in inputgraph.edges( data=True, key=True ) ])
        
        while flowcontroller.next_step( mydatacontainer, edgecontainer ):
            pass

        return_translator = \
                { \
                translator[ value ] : value \
                for value in outputgraph
                if translator[ value ] in mydatacontainer \
                }
        return { value: mydatacontainer[ key ] \
                for key, value in return_translator.items() }
    call_function.__doc__ = "\n\tinputvariables are %s\n" \
                                %( inputgraph.nodes(data=True) )

    my_linear_function = factory_leaf( inputgraph, outputgraph, call_function )

    return my_linear_function


class linearflowcontroller():
    def __init__( self, flowgraph, outputgraph, ):
        self.node_to_datatype = flowgraph.node_to_datatype
        nextnode_from_state, possible_datastate_at_output \
                    = self.find_nextnode_from_state( flowgraph, outputgraph )
        process_lib = self.create_process_lib( nextnode_from_state, flowgraph )

        self.process_lib = process_lib
        self.nextnode_from_state = nextnode_from_state
        self.possible_datastate_at_output = possible_datastate_at_output

    def create_process_lib( self, nextnode_from_state, flowgraph ):
        #nextnode_from_state
        process_dict = {}
        process_weight = {}
        alledges = flowgraph.edges( data=True )
        notfromfailstates_edges = [ edge for edge in alledges \
                                    if edge[0] in nextnode_from_state ]
        for edge in notfromfailstates_edges:
            if nextnode_from_state[ edge[0] ] == edge[1]:
                if process_weight.get( edge[0], math.inf ) > edge[-1]["weight"]:
                    process_weight[ edge[0] ] = edge[-1][ "weight" ]
                    process_dict[ edge[0] ] = edge[-1][ EDGETYPE ]
        return process_dict


    def next_step( self, datacontainer, edgecontainer ):
        current_state = datastate( self.node_to_datatype, \
                                    datacontainer.keys(), edgecontainer )
        if current_state in self.possible_datastate_at_output:
            return False
        #raise Exception( current_state.nodes, current_state.edges )
        try:
            nextprocess = self.process_lib[ current_state ]
        except KeyError as err:
            asd = [ st.__hash__() for st in self.process_lib.keys() ]
            err.args = ( *err.args, "The function has most likely run "\
                        +"into a deadend. Please configure your factoryleafs",\
                        asd )
            raise err
        newdata_dict = nextprocess( **datacontainer )
        delete_nodes = nextprocess.delete_nodes
        add_edges = nextprocess.add_edges
        if newdata_dict:
            for rm_node in delete_nodes:
                current_state.pop( rm_node )
            for edge in edgecontainer:
                if edge[0] in delete_nodes or edge[1] in delete_nodes:
                    edgecontainer.remove( edge )
            datacontainer.update( newdata_dict )
            for edge in add_edges:
                if edge[0] in datacontainer and edge[1] in datacontainer:
                    edgecontainer.append( edge )
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
