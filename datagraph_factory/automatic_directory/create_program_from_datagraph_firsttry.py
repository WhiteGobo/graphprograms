import copy
import networkx as netx
from ..processes import factory_leaf
from ..find_process_path import datastate_from_graph
from ..find_process_path import datastate
import math
import itertools
from ..find_process_path import datastate_not_connected_error
from ..linear_factorybranch import FailstateReached, NoPathToOutput, \
                                DataRescueException

from ..constants import DATAGRAPH_CONTAINED_DATA as CONTAINED_DATA


def complete_datagraph( flowgraph, wholegraph ):
    nodes_with_data = set( find_filled_datanodes( wholegraph ) )
    nodes_to_produce = set( wholegraph.nodes() ).difference( nodes_with_data )
    inputoutputgraph_helper = wholegraph_flowgraph_splitter()
    while nodes_to_produce != set():
        nextnode = find_neighbournode( nodes_to_produce, wholegraph )
        poss_graphs = inputoutputgraph_helper \
                            .get_possible_partgraphs_for_datanode( nextnode )
        for outputgraph in poss_graphs:
            try:
                inputgraph = filter_outputgraph( outputgraph, nodes_with_data )
                myfoo = create_linear_function( flowgraph, inputgraph, \
                                                                outputgraph )
                inputdata = wholegraph.data_of_subgraph( inputgraph )
                outputdata = myfoo( **{inputdata} )
                wholegraph.update( outputdata )
                break
            except datastate_not_connected_error:
                pass
        nodes_to_produce = nodes_to_produce.difference( outputdata.keys() )
        nodes_with_data = nodes_with_data.union( outputdata.keys() )
    return wholegraph



class wholegraph_flowgraph_splitter():
    __slots__= [ "flowgraph", "wholegraph", "targets_via_partgraphs" ]
    def __init__( self, flowgraph, wholegraph ):
        self.flowgraph = flowgraph
        self.wholegraph = wholegraph
        mingraph_with_partgraph = self.create_minimalgraphs_to_wholegraphparts(\
                                                    flowgraph, wholegraph )
        targets_via_partgraphs = self.create_targetnode_via_minpartgraphpair( \
                                                    mingraph_with_partgraph )
        self.targets_via_partgraphs = targets_via_partgraphs


    def get_possible_partgraphs_for_datanode( self, key ):
        return self.targets_via_partgraphs[ key ]


    def create_minimalgraphs_to_wholegraphparts( self, flowgraph, wholegraph ):
        #targetnode_to_datastate = self.find_maximal_outputstates_with_target( \
        #                        flowgraph, wholegraph )
        #parts_of_wholegraph \
        #                = self.find_possible_translations_of_targetgraphs_from(
        #                        targetgraph_targetnode_translation_tuplelist )
        parts_of_wholegraph \
                    = flowgraph.find_possible_compatible_maximal_partgraphs( \
                                                                    wholegraph)
        mingraph_to_partgraph = list()
        for partgraph in parts_of_wholegraph:
            minimalgraphs_to_partgraph = find_minimal_sourcegraph(
                                                    partgraph, flowgraph )
            for mingraph in minimalgraphs_to_wholegraph:
                mingraph_with_partgraph.append( ( mingraph, partgraph ) )
        return mingraph_with_partgraph


    def find_maximal_outputstates_with_target( self, flowgraph, wholegraph ):
        targetnode_to_datastate = dict()
        for node, data in wholegraph.nodes( data=True ):
            tmpdatatype = data[ DATATYPE ]
            datastatelist = flowgraph.get_maximal_states_with_datatype( \
                                                                tmpdatatype )
            targetnode_to_datatate[ node ] = datastatelist
        return datastatelist


    def find_possible_translations_of_targetgraphs_from( self, \
                                targetgraph_targetnode_translation_tuplelist ):
        pass

    def find_minimal_sourcegraph( self, partgraph, flowgraph ):
        pass

    def possible_targets_via_targetgraphs( self, partgraph, mingraph ):
        pass

            
    def create_targetnode_via_minpartgraphpair( self, mingraph_with_partgraph):
        targets_via_partgraphs = dict()
        for mingraph, partgraph in mingraph_with_partgraph:
            targets = self.possible_targets_via_targetgraphs( partgraph, \
                                                                mingraph )
            for t in targets:
                graph_for_target = targets_via_partgraphs.setdefault( t, list())
                graph_for_target.append( partgraph )
        return targets_via_partgraphs



def find_filled_datanodes( wholegraph ):
    nodes_with_data = set( node for node, data in wholegraph.nodes(data=True) \
                    if CONTAINED_DATA in data.keys() )
    return nodes_with_data
