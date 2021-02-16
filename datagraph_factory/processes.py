from collections import Counter
import itertools
import networkx as netx
from .datagraph import datagraph
from .constants import DATAGRAPH_DATATYPE as DATATYPE
from .constants import DATAGRAPH_EDGETYPE as EDGETYPE
import inspect
#import networkx as netx


myregister = []
datanode_input_to_process = {}
datanode_output_to_process = {}
possible_edges_between_types = {}

class conclusion_leaf():
    prestatus = None
    poststatus = None


def pass_function():
    pass

class factory_leaf():
    #prestatus = None # type == datagraph
    #poststatus = None # type == datagraph
    #cost = None
    def __init__( self, prestatus, poststatus, \
                                call_function=pass_function, extra_docs="" ):
        #if call_function != pass_function:
        #    call_args = inspect.signature(call_function).parameters.keys()
        #    if set( prestatus.nodes() ) != call_args:
        #        raise Exception( "prestatus has not the same nodes as the"
        #                        +"call_function has as arguments",\
        #                        f"prestatus: {prestatus.nodes()}; " \
        #                        +f"call: {call_args}" )
        self.prestatus = prestatus
        self.poststatus = poststatus
        self.call_function = call_function
        self.cost = 1

        idtotype = netx.get_node_attributes( prestatus, DATATYPE )
        inputdoc = "input:\n"\
                + "".join([ f"{nodename}: {nodetype}\n" \
                                for nodename, nodetype in idtotype.items() ])
        self.__doc__ = inputdoc + extra_docs + str( call_function.__doc__ )
    def __call__( self, **args ):
        return self.call_function( **args )




    #def __call__( self ):
    #    raise Exception(f"call not implemented of class{type( self )}")



def register_process( asd ):
    myregister.append( asd )

    for datanode in asd.input_datagraph.nodes():
        proc_list = datanode_input_to_process.setdefault( datanode, list() )
        proc_list.append( self )
    for datanode in asd.output_datagraph.nodes():
        proc_list = datanode_output_to_process.setdefault( datanode, list() )
        proc_list.append( self )

    nodetype = netx.get_node_attributes( asd.input_datagraph, DATATYPE )
    for node1, node2, k, data in asd.input_datagraph.edges(data=True,keys=True):
        nodetype1 = nodetype[ node1 ]
        nodetype2 = nodetype[ node2 ]
        to_dict = possible_edges_between_types.setdefault( nodetype1, dict() )
        edgeset = to_dict.setdefault( nodetype2, set() )
        edgeset.d( data[ EDGETYPE ] )
    del( nodetype )
    nodetype = netx.get_node_attributes( asd.output_datagraph, DATATYPE )
    for node1, node2, k,data in asd.output_datagraph.edges(data=True,keys=True):
        nodetype1 = nodetype[ node1 ]
        nodetype2 = nodetype[ node2 ]
        to_dict = possible_edges_between_types.setdefault( nodetype1, dict() )
        edgeset = to_dict.setdefault( nodetype2, set() )
        edgeset.add( data[ EDGETYPE ] )
    del( nodetype )


def get_all_processes():
    return myregister

def get_processes_with_datanode( datanode ):
    return datanode_output_to_process.get( datanode, list() )


def get_datanode_types():
    # this creates a set of all available keys
    return set( ( *datanode_output_to_process, *datanode_input_to_process ) )

def get_possible_edges( nodetype1, nodetype2 ):
    return possible_edges_between_types[ nodetype1 ][ nodetype2 ]


def _dictionaries_have_contradiction( dict1, dict2 ):
    mykeys = set( dict1.keys() ).intersection( dict2.keys() )
    return not all( [ dict1[ key ] == dict2[ key ] for key in mykeys ] )

def get_datanode_maximal_occurence( processlist ):
    maxoccur = Counter()
    for process in processlist:
        inputdict = netx.get_node_attributes( process.prestatus, DATATYPE )
        outputdict = netx.get_node_attributes( process.poststatus, DATATYPE )
        if _dictionaries_have_contradiction( inputdict, outputdict ):
            raise Exception( "prestatus and poststatus of "\
                    +f"{process.__qualname__} contradict oneanother")

        input_type_list, output_type_list = None, None
        occur_in, occur_out = None, None
        inputgraph = process.prestatus
        try:
            input_type_list = [ inputdict[ node ] \
                            for node in inputgraph.nodes() ]
        except KeyError as err:
            err.args = (*err.args, f"process {process.__qualname__} wasnt "\
                        + f"properly declared. Inputnodes lacked property"\
                        +f" 'datagraph_factory.constants.DATAGRAPH_DATATYPE'.",\
                        f"found nodes: {inputgraph.nodes()}" )
            raise err
        occur_in = Counter( input_type_list )
        del( input_type_list, inputgraph )
        outputgraph = process.poststatus
        try:
            output_type_list = [ outputdict[ node ] \
                            for node in outputgraph.nodes() ]
        except KeyError as err:
            err.args = (*err.args, f"process {process.__qualname__} wasnt "\
                        + f"properly declared. Outputnodes lacked property"\
                        +f" 'datagraph_factory.constants.DATAGRAPH_DATATYPE'.",\
                        f"found nodes: {outputgraph.nodes()}" )
            raise err
        occur_out = Counter( output_type_list )
        del( output_type_list, outputgraph )

        for datatype, occ in occur_in.items():
            dt = datatype
            maxoccur[ dt ] = max( occ, maxoccur.get( dt, 0 ) )
            del( dt )
        for datatype, occ in occur_out.items():
            dt = datatype
            maxoccur[ dt ] = max( occ, maxoccur.get( dt, 0 ) )
            del( dt )

    return maxoccur
