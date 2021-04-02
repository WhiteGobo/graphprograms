import copy
import networkx as netx
from ..processes import factory_leaf
from ..find_process_path import datastate_from_graph
from ..find_process_path import datastate
from ..constants import DATAGRAPH_EDGETYPE as EDGETYPE
import math
import itertools
from ..find_process_path import datastate_not_connected_error
from ..linear_factorybranch import FailstateReached, NoPathToOutput, \
                                DataRescueException

from ..constants import DATAGRAPH_CONTAINED_DATA as CONTAINED_DATA

def complete_datagraph( flowgraph, wholegraph ):
    nodes_with_data = set( find_filled_datanodes( wholegraph ) )
    nodes_to_produce = set( wholegraph.nodes() ).difference( nodes_with_data )
    targetgraph_minimalgraph_distance_tripel \
                        = find_minimal_inputgraphs_for_creation( \
                                        flowgraph, wholegraph, \
                                        nodes_to_produce, nodes_with_data )
    while nodes_to_produce != set():
        use_graph, target_graph = pop_minimal_distance( nodes_with_data, \
                                    targetgraph_minimalgraph_distance_tripel)
        myfoo = create_linear_function( flowgraph, use_graph, target_graph  )
        inputdata = wholegraph.data_of_subgraph( use_graph )
        outputdata = myfoo( **{inputdata} )
        wholegraph.update( outputdata )
        nodes_to_produce = nodes_to_produce.difference( outputdata.keys() )
        targetgraph_minimalgraph_distance_tripel \
                = remove_target( targetgraph_minimalgraph_distance_tripel, \
                                                        outputdata.keys() )
        nodes_with_data = nodes_with_data.union( outputdata.keys() )
    return wholegraph



def pop_minimal_distance( nodes_with_data, \
                            targetgraph_minimalgraph_distance_tripel ):
    getdistance = lambda trip: trip[2]
    get_mingraph = lambda trip: trip[1]
    mysort = sorted( targetgraph_minimalgraph_distance_tripel, key=getdistance )
    mysort = iter( mysort )
    minimi = None
    while minimi == None:
        tmptriple = q.__next__()
        if nodes_with_data.issuperset( get_mingraph(tmptriple) ):
            minimi = tmptriple
    targetgraph_minimalgraph_distance_tripel.discard( minimi )
    return minimi

def find_minimal_inputgraphs_for_creation( flowgraph, wholegraph, \
                                        nodes_to_produce ):
    for target_node in nodes_to_produce:
        state_nodes = flowgraph.translator[ target_node ]
        for state_node in state_nodes:
            target_states  = [ node for node in flowgraph.nodes() \
                                if state_node in node ]
            for endstate in target_states:
                startstates = flowgraph.find_minimalestate( endstate )


def find_filled_datanodes( wholegraph ):
    nodes_with_data = set( node for node, data in wholegraph.nodes(data=True) \
                    if CONTAINED_DATA in data.keys() )
    return nodes_with_data

