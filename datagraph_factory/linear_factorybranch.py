import copy
import networkx as netx
from .processes import factory_leaf
from .find_process_path import datastate_from_graph
from .find_process_path import datastate
from .constants import DATAGRAPH_EDGETYPE as EDGETYPE
import math
import itertools
from .find_process_path import datastate_not_connected_error

class FailstateReached( Exception ):
    pass
class NoPathToOutput( Exception ):
    pass
class DataRescueException( Exception ):
    def __init__( self, mydatagraph ):
        super().__init__()
        self.datagraph = mydatagraph

def create_linear_function( flowgraph, inputgraph, outputgraph, verbosity=0 ):
    """
    :type flowgraph: .find_process_path.flowgraph
    """
    node_to_datatype = flowgraph.node_to_datatype
    try:
        translators = flowgraph.translator( inputgraph, outputgraph )
    except KeyError as err:
        err.args = (*err.args, "cant create function for the purpose of "\
                        "creating the outputgraph from the inputgraph."\
                        " Please adjust those graphs or given flowgraph", \
                        f"input: {inputgraph.nodes(data=True)};;;; "\
                        +f";;;;{inputgraph.edges(data=True)}, output: "\
                        +f"{outputgraph.nodes(data=True)};;;; "\
                        +f"{outputgraph.edges(data=True)}",\
                        "for supported graphs by flowgraph, please use "\
                        +"flowgraph.nodes()" )
        raise err
    inputtranslator = translators[0]
    try:
        current_datastate = datastate_from_graph( flowgraph, \
                                netx.relabel_nodes(inputgraph, inputtranslator))
    except datastate_not_connected_error as err:
        err.args = ( *err.args, "ingraph must be connected" )
        raise err
    try:
        create_datastate = lambda trans: datastate_from_graph( flowgraph, \
                                netx.relabel_nodes(outputgraph, trans))
        target_datastates = { create_datastate( trans ): trans \
                                for trans in translators }
    except datastate_not_connected_error as err:
        err.args = ( *err.args, "outputgraph must be connected" )
        raise err

    flowcontroller = linearflowcontroller( flowgraph, target_datastates )
    call_function = _create_call_function( inputgraph, inputtranslator, \
                                            flowcontroller, current_datastate )
    _get_inputoutputgraph = lambda: (inputgraph, outputgraph)
    my_linear_function = factory_leaf( _get_inputoutputgraph, call_function )
    return my_linear_function


def _create_call_function( inputgraph, inputtranslator, \
                            flowcontroller, current_datastate ):
    def call_function( **args ):
        if set( inputgraph.nodes() ) != args.keys():
            raise KeyError( f"wrong input needed: {inputgraph.nodes()} "\
                            f"and got {args.keys()}" )
        mydatacontainer = { inputtranslator[ key ]:value \
                            for key, value in args.items() }
        flowcontroller.myflowgraph.datastate = current_datastate
        flowcontroller.data = mydatacontainer
        try:
            while flowcontroller.next_step():
                pass
        except Exception as err:
            mydata = flowcontroller.get_all_data()
            raise DataRescueException( mydata ) from err
        return flowcontroller.get_output_data()

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
    return call_function


class linearflowcontroller():
    def __init__( self, myflowgraph, outputstates_to_graph ):
        outputstates = list( outputstates_to_graph.keys() )
        self.node_to_datatype = myflowgraph.node_to_datatype
        nextnode_from_state, possible_datastate_at_output_with_trans,failstates\
                    = self.find_nextnode_from_state( myflowgraph, \
                                                    outputstates_to_graph )
        possible_datastate_at_output = possible_datastate_at_output_with_trans
        if len( possible_datastate_at_output) == 0:
            raise NoPathToOutput( "Cant find way to create given output "\
                                    "with this flowgraph", \
                                    "possible outputstates are: %s"\
                                    %(outputstates_to_graph) )
        process_lib = self.create_process_lib( nextnode_from_state, myflowgraph)
        process_lib = self.add_failstate_exception( failstates, process_lib )

        #self.outputstates_to_graph = outputstates_to_graph
        self.outputstates_to_graph = possible_datastate_at_output_with_trans

        self._failstates = failstates
        self.process_lib = process_lib
        self.nextnode_from_state = nextnode_from_state
        self.possible_datastate_at_output = possible_datastate_at_output
        self.myflowgraph = myflowgraph

    def get_output_data( self ):
        currentstate = self.myflowgraph.datastate
        mydatacontainer = self.data
        try:
            translator = self.outputstates_to_graph[ currentstate ]
        except Exception as err:
            print( self.outputstates_to_graph )
            raise
        raise Exception()

        return_translator = \
                { \
                newkey : value \
                for value, newkey in translator.items() \
                if newkey in mydatacontainer \
                }
        return { value: mydatacontainer[ key ] \
                for key, value in return_translator.items() }

    def get_all_data( self ):
        currentstate = self.myflowgraph.datastate
        mydatacontainer = self.data
        return mydatacontainer

    def add_failstate_exception( self, failstates, processlib ):
        def raiseFailstateError():
            raise FailstateReached( "reached failstate", \
                                    self.myflowgraph.datastate )
        for singlestate in failstates:
            processlib[ singlestate ] = raiseFailstateError
        return processlib
        

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


    def find_nextnode_from_state( self, flowgraph, \
                                    outputstates_with_translation ):
        """
        :return mypaths:
        :rtype mypaths:
        :return possible_datastate_at_output:
        :rtype possible_datastate_at_output:
        """
        foo_allsuperstate_with_trans = lambda state, translation: \
                    itertools.product( \
                    flowgraph.get_superstates_to(state ),\
                    [translation] )
        tmppairs = (foo_allsuperstate_with_trans( state, translation )\
                    for state, translation \
                    in outputstates_with_translation.items() )
        #raise Exception( list(list(x) for x in tmppairs) )
        possible_datastate_at_output_with_translation \
                    = { key:value \
                        for key, value in itertools.chain( *tmppairs ) }
        possible_datastate_at_output \
                = set( possible_datastate_at_output_with_translation.keys() )
        #possible_datastate_at_output = set( \
        #            itertools.chain(*[ flowgraph.get_superstates_to(state )\
        #            for state in outputstates ] ) )

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
        return mypaths, possible_datastate_at_output_with_translation,failstates
