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
    def __init__( self, generate_datagraphs ):
        self._generate_datagraphs = generate_datagraphs
        #prestatus, poststatus = generate_datagraphs()
        #self.prestatus = prestatus
        #self.poststatus = poststatus
    def _generate_pre_and_poststatus( self ):
        pre, post = self._generate_datagraphs()
        self._prestatus = pre
        self._poststatus = post
        if set( pre.nodes() ) != set( post.nodes() ):
            raise KeyError( "conclusions only works to add single edges",
                            "prestatus.nodes: {set(pre.nodes())}", \
                            "poststatus.nodes: {set(post.nodes())}")
    def _generate_prestatus( self ):
        try:
            return self._prestatus
        except AttributeError:
            pass
        self._generate_pre_and_poststatus()
        return self._prestatus
    prestatus = property( fget=_generate_prestatus )

    def _generate_poststatus( self ):
        try:
            return self._poststatus
        except AttributeError:
            pass
        self._generate_pre_and_poststatus()
        return self._poststatus
    poststatus = property( fget=_generate_poststatus )




def pass_function():
    pass

class factory_leaf():
    #prestatus = None # type == datagraph
    #poststatus = None # type == datagraph
    #cost = None
    def __init__( self, generate_datagraphs, \
                                                call_function=pass_function, \
                                                extra_docs="", cost=1, name=""):
        #prestatus, poststatus = generate_datagraphs()
        self._generate_datagraphs = generate_datagraphs
        #if call_function != pass_function:
        #    call_args = inspect.signature(call_function).parameters.keys()
        #    if set( prestatus.nodes() ) != call_args:
        #        raise Exception( "prestatus has not the same nodes as the"
        #                        +"call_function has as arguments",\
        #                        f"prestatus: {prestatus.nodes()}; " \
        #                        +f"call: {call_args}" )
        #if not (prestatus.test_valid() and poststatus.test_valid() ):
        #    raise Exception( prestatus.test_valid(), poststatus.test_valid() )
        if name:
            self.name = "{%s}" %(name)
        else:
            self.name = object.__repr__( self )
        #self.prestatus = prestatus
        #self.poststatus = poststatus
        self.call_function = call_function
        self.cost = cost

        #idtotype = netx.get_node_attributes( prestatus, DATATYPE )
        #inputdoc = "input:\n"\
        #        + "".join([ f"{nodename}: {nodetype}\n" \
        #                        for nodename, nodetype in idtotype.items() ])
        #self.__doc__ = inputdoc + extra_docs + str( call_function.__doc__ )

    def _generate_pre_and_poststatus( self ):
        pre, post = self._generate_datagraphs()
        self._prestatus = pre
        self._poststatus = post
    def _generate_prestatus( self ):
        try:
            return self._prestatus
        except AttributeError:
            pass
        self._generate_pre_and_poststatus()
        return self._prestatus
    prestatus = property( fget=_generate_prestatus )

    def _generate_poststatus( self ):
        try:
            return self._poststatus
        except AttributeError:
            pass
        self._generate_pre_and_poststatus()
        return self._poststatus
    poststatus = property( fget=_generate_poststatus )

    def __repr__( self ):
        return self.name

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
        try:
            process.prestatus, process.poststatus
        except AttributeError as err:
            raise TypeError( process, "given processlist didnt contain "\
                                "factory_leaf-like elements" ) from err
        inputdict = netx.get_node_attributes( process.prestatus, DATATYPE )
        outputdict = netx.get_node_attributes( process.poststatus, DATATYPE)
        if _dictionaries_have_contradiction( inputdict, outputdict ):
            raise Exception( "prestatus and poststatus of "\
                    +f"{process.__qualname__} contradict oneanother")
        if inputdict.keys() != set( process.prestatus.nodes() ):
            raise Exception(f"process {process.__qualname__} wasnt "\
                        + f"properly declared. Inputnodes lacked property"\
                        +f" 'datagraph_factory.constants.DATAGRAPH_DATATYPE'.",\
                        f"found nodes: {inputgraph.nodes()}" )
        if outputdict.keys() != set( process.poststatus.nodes() ):
            raise Exception( f"process {process.__qualname__} wasnt "\
                        + f"properly declared. Outputnodes lacked property"\
                        +f" 'datagraph_factory.constants.DATAGRAPH_DATATYPE'.",\
                        f"found nodes: {outputgraph.nodes()}" )
        inputdict = netx.get_node_attributes( process.prestatus, DATATYPE )
        outputdict = netx.get_node_attributes( process.poststatus, DATATYPE)
        wholedict = inputdict
        wholedict.update( outputdict )
        occur = Counter( wholedict.values() )

        for datatype, occ in occur.items():
            dt = datatype
            maxoccur[ dt ] = max( occ, maxoccur.get( dt, 0 ) )
            del( dt )

    return maxoccur

