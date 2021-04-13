import copy
import networkx as netx
from ..processes import factory_leaf
from ..find_process_path import datastate_from_graph
from ..find_process_path import datastate
from .. import find_process_path
from .. import linear_factorybranch
from ..linear_factorybranch import create_linear_function
import math
import itertools
from ..find_process_path import datastate_not_connected_error
from ..linear_factorybranch import FailstateReached, NoPathToOutput, \
                                DataRescueException

from ..constants import DATAGRAPH_CONTAINED_DATA as CONTAINED_DATA


def complete_datagraph( myflowgraph, wholegraph ):
    asd = myflowgraph.find_possible_compatible_maximal_partgraph( wholegraph )
    generatable_nodes_with = dict()
    for max_datastate, datastate_to_graphnodes in asd:
        minimal_states = myflowgraph.find_minimal_datastates_to( \
                                                            max_datastate )
        for minstate in minimal_states:
            try:
                minigraph = wholegraph.subgraph( [ \
                                        datastate_to_graphnodes[n] \
                                        for n in minstate.nodes ] )
                generatable_dsnodes = max_datastate.nodes.difference( \
                                        minstate.nodes )
                targetgraph = wholegraph.subgraph( \
                                        datastate_to_graphnodes.values() )
                minigraph_nodes = frozenset( [ \
                                        datastate_to_graphnodes[n] \
                                        for n in minstate.nodes ] )
                targetgraph_nodes = frozenset( \
                                        datastate_to_graphnodes.values() )
                for dsnode in generatable_dsnodes:
                    try:
                        graphnode = datastate_to_graphnodes[ dsnode ]
                        tmpset = generatable_nodes_with.setdefault( \
                                        graphnode, set() )
                        #tmplist.append( (minigraph, targetgraph) )
                        tmpset.add((minigraph_nodes, targetgraph_nodes))
                    except KeyError:
                        pass
            except KeyError: #catch if minigraph cant be created from 
                            #given nodes of wholegraph
                pass
    while not wholegraph.completed:
        borderlist = wholegraph.get_completed_datanode_border( \
                                                not_completed_nodes=True )
        completed_nodes = set( wholegraph.get_completed_datanodes() )
        lever = False
        for node in borderlist:
            for in_nodes, out_nodes in generatable_nodes_with[ node ]:
                if set( in_nodes ).difference(completed_nodes) == set():
                    try:
                        in_graph = wholegraph.subgraph( in_nodes )
                        out_graph = wholegraph.subgraph( out_nodes )
                        myfoo = create_linear_function( \
                                        myflowgraph, in_graph, out_graph )
                        mydata = wholegraph.get_data_as_dictionary()
                        mydata = { key:value \
                                        for key, value in mydata.items() \
                                        if key in in_nodes }
                        asd = myfoo( **mydata )
                        for key, value in asd.items():
                            wholegraph[ key ] = value
                        lever = True
                        break
                    except (find_process_path.datastate_not_connected_error,
                            linear_factorybranch.NoPathToOutput ):
                        pass
            if lever:
                break
    return wholegraph


