from ..find_process_path import datastate_from_graph, \
                            datastate, \
                            datastate_not_connected_error
from ..linear_factorybranch import create_linear_function, \
                            FailstateReached, NoPathToOutput, \
                            DataRescueException
import networkx as netx
import logging
logger = logging.getLogger( __name__ )
from ..constants import \
        DATAGRAPH_DATATYPE as DATATYPE


def complete_datagraph( myflowgraph, wholegraph ):
    logger.debug( "wholegraph, nodes to datatype: %s "\
                    %(netx.get_node_attributes( wholegraph, DATATYPE )))
    asd = myflowgraph.find_possible_compatible_maximal_partgraph( wholegraph )

    newasd = []
    for max_datastate, datastate_to_graphnodes in asd:
        minimal_states = myflowgraph.find_minimal_datastates_to( max_datastate )
        for minstate in minimal_states:
            newasd.append( (minstate, max_datastate, datastate_to_graphnodes) )
    if len(newasd) == 0:
        raise Exception( "couldnt find any creatablegraphs" )

    newnewasd = set()
    for min_datastate, max_datastate, datastate_to_graphnodes in newasd:
        tmp = reduce_generator_to_newsubgraph_weakly_connected( \
                                        min_datastate, max_datastate, \
                                        datastate_to_graphnodes, wholegraph )
        for i in tmp:
            newnewasd.add( i )
    if newnewasd == set():
        raise Exception( "couldnt separate creatablegraphs to graphs. This shouldnt happen if the algorithm is correct. Please contact the programmer" )

    generatable_nodes_with = create_generatordict_for_graphnodes( newnewasd, \
                                                    myflowgraph, wholegraph )

    notcompleted = set(wholegraph.nodes()).difference( wholegraph.get_completed_datanodes() )
    logger.debug( "startnodes are: %s" %( notcompleted ))
    if not set( generatable_nodes_with.keys() ).issuperset( notcompleted ):
        raise Exception( "cant generate following missing nodes "\
                            "from wholegraph: %s" %( 
                            notcompleted.difference(
                            generatable_nodes_with.keys()))
                            )
    wholegraph = _steploop_complete_graph( generatable_nodes_with, \
                                            myflowgraph, wholegraph )
    return wholegraph


def create_generatordict_for_graphnodes( inout_graphnodesets, \
                                        myflowgraph, wholegraph ):
    generatable_nodes_with = dict()
    for in_graphnodes, out_graphnodes in inout_graphnodesets:
        extra_graphnodes = set( out_graphnodes ).difference( in_graphnodes )
        for single in extra_graphnodes:
            tmplist = generatable_nodes_with.setdefault( \
                            single, list() )
            tmplist.append( (in_graphnodes, out_graphnodes) )
    #sort by first maximal number of innodes and second by maximal n of outnodes
    mysort = lambda x: ( -( len(x[1])-len(x[0]) ), -len(x[0]) )
    #mysort = lambda x: ( -len(x[1]), -len(x[0]) )
    for mylist in generatable_nodes_with.values():
        mylist.sort( key = mysort )
    return generatable_nodes_with


def reduce_generator_to_newsubgraph_weakly_connected( min_datastate, \
                                        max_datastate, datastate_to_graphnodes,\
                                        wholegraph ):
    extra_nodes = set( max_datastate.nodes ).difference( min_datastate.nodes )
    try:
        in_graphnodes = set( datastate_to_graphnodes[n] \
                                for n in min_datastate.nodes )
    except KeyError as err:
        # If minimal datastate cant be provided 
        # by datagraph no generator is possible. 
        return
    out_graphnodes = set( datastate_to_graphnodes[n] \
                                for n in max_datastate.nodes \
                                if n in datastate_to_graphnodes.keys() )
    extra_graphnodes = out_graphnodes.difference( in_graphnodes )
    newnodes_subgraph = wholegraph.subgraph( extra_graphnodes )
    weak_components = netx.weakly_connected_components( newnodes_subgraph )
    for single in weak_components:
        new_out_graphnodes_with_connected_newnodes \
                = in_graphnodes.union( single )
        yield ( frozenset( in_graphnodes ), \
                frozenset( new_out_graphnodes_with_connected_newnodes ) )
        #yield ( min_graphnodes, new_out_graphnodes_with_connected_newnodes, \
        #        datastate_to_graphnodes )


def _steploop_complete_graph( generatable_nodes_with, myflowgraph, wholegraph ):
    while not wholegraph.completed:
        completed_nodes = set( wholegraph.get_completed_datanodes() )
        asd = _complete_graph_step( generatable_nodes_with, myflowgraph, \
                                wholegraph, completed_nodes )

        for key, value in asd.items():
            if key in completed_nodes:
                raise Exception( "recreated node in graph autocomplete", key )
            wholegraph[ key ] = value
    return wholegraph


def _complete_graph_step(generatable_nodes_with, myflowgraph, \
                                wholegraph, completed_nodes ):

    borderlist = wholegraph.get_completed_datanode_border( \
                                                not_completed_nodes=True)
    borderlist = list( borderlist )
    completed_nodes = set( wholegraph.get_completed_datanodes() )
    for node in borderlist:
        for in_nodes, out_nodes in generatable_nodes_with[ node ]:
            real_innodes = set( out_nodes ).intersection( completed_nodes )
            if real_innodes.issuperset( in_nodes ):
                try:
                    in_graph = wholegraph.subgraph( real_innodes )
                    out_graph = wholegraph.subgraph( out_nodes )
                    myfoo = create_linear_function( \
                                    myflowgraph, in_graph, out_graph )
                    mydata = wholegraph.get_data_as_dictionary()
                    mydata = { key:value \
                                    for key, value in mydata.items() \
                                    if key in real_innodes }
                    logger.debug( f"Use nodes %s to create nodes: %s" \
                                    %(str(in_graph.nodes()), \
                                    set(out_graph.nodes())\
                                    .difference(in_graph.nodes())) )
                    asd = myfoo( **mydata )
                    return { key: value for key, value in asd.items() \
                            if key not in real_innodes }
                except ( datastate_not_connected_error, NoPathToOutput ) as er:
                    pass
    raise Exception( f"tried to generate following nodes {borderlist}", \
                        set( wholegraph.get_completed_datanodes() ))
