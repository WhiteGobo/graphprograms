import copy
import networkx as netx
import inspect
"""
:todo: rename NODEFUNCTIONCONTAINER to NODEOBJECT
    document structure of the graphs
"""

NODECLASS = "nodeclass"
NODEFUNCTIONCONTAINER = "mycontainer"
MOTHERNODE = "mothernode"
TIMINGSUBLABEL = "sublabel"
NODEFUNCTION = "nodefunction"
EDGETYPE = "edgetype"

PROGRAMKEYS = [ NODECLASS, NODEFUNCTIONCONTAINER, MOTHERNODE, TIMINGSUBLABEL, \
                NODEFUNCTION, EDGETYPE ]
class DoubledNameError( Exception ):
    pass

class cyprogra(): #cycle program from graph
    def __init__( self, graph ):
        """
        generates from a graph a program.
        The idea is to create a layered functionlist. The functions will be 
        readily decorated so that no arguments must be given.
        Every node in the graph must have the

        """
        graph = copy.deepcopy( graph )
        self.graph = graph
        self.return_graph = copy.deepcopy( graph )
        if set( graph.nodes() ) \
                    != set( netx.get_node_attributes( graph, NODECLASS).keys()):
            raise Exception( "All nodes must have a corresponding class", \
                            ("nodeattribute to be set is '%s'; see also "\
                            +"%s.NODECLASS") %(NODECLASS, __name__ ) )

        timing_graph = netx.MultiDiGraph()
        generate_all_nodefunctioncontainers_from_graph( graph )
        timing_graph = add_code_of_functioncontainers_to_timing_graph( \
                                                        graph, timing_graph )
        timing_graph = add_code_of_edges_to_timing_graph( graph, timing_graph )

        self.cycle_function = compile_code( timing_graph )


    def cycle( self ):
        self.cycle_function()


    def return_to_graph( self ):
        return_graph = copy.deepcopy( self.return_graph )
        #calcgraph_attr = netx.get_node_attributes( self.graph )
        for node, data in self.graph.nodes( data=True ):
            nodeobject = data[ NODEFUNCTIONCONTAINER ]
            for key, nodedata in nodeobject.get_properties().items():
                netx.set_node_attributes( return_graph, {node:nodedata},key)
        return return_graph



def add_code_of_edges_to_timing_graph( graph, timing_graph ):
    data_of_mothernodes = graph.nodes( data=True )
    for edge in graph.edges( data=True ):
        node1, node2, data = edge[0], edge[1], edge[-1]

        node1_object = data_of_mothernodes[ node1 ][ NODEFUNCTIONCONTAINER ]
        node2_object = data_of_mothernodes[ node2 ][ NODEFUNCTIONCONTAINER ]
        node2_type = data_of_mothernodes[ node2 ][ NODECLASS ]

        try:
            function_identifier = ( node2_type, data[ EDGETYPE ] )
        except KeyError as err:
            err.args = (*err.args, f"for edge {repr(edge[:-1])} information "\
                    + f"how node {node1} and node {node2} are interacting "\
                    + f"with one another. please add the edgeattribute "\
                    + f"'{EDGETYPE}' to the graph. see also "\
                    + f"{__name__}.EDGETYPE", "edgeattr must align the "\
                    + f"edgedictionary of nodefunctioncontainer {node1}" )
            raise err

        tmpfunction, after_self, before_self, after_other, before_other \
                    = node1_object.edge_to_dictionary[ function_identifier ]

        nodeid = repr( edge ) #This should be a unique name
        nodedata = { NODEFUNCTION: tmpfunction, "other": node2_object }
        nodedata.update( data )
        insert_edgefunction_in_timing_graph( nodeid, timing_graph, nodedata, \
                                            data_of_mothernodes, node1, node2,
                                            after_self, before_self,\
                                            after_other, before_other )

        
    return timing_graph

def insert_edgefunction_in_timing_graph( nodeid, timing_graph, nodedata,\
                                        data_of_mothernodes, node1, node2,\
                                        after_self, before_self, \
                                        after_other, before_other ):
    timing_graph.add_node( nodeid, **nodedata )
    for functionlabel in after_self:
        tmp_after_node = data_of_mothernodes[ node1 ][ functionlabel ]
        timing_graph.add_edge( tmp_after_node, nodeid )
    for functionlabel in after_other:
        tmp_after_node = data_of_mothernodes[ node2 ][ functionlabel ]
        timing_graph.add_edge( tmp_after_node, nodeid )
    for functionlabel in before_self:
        tmp_after_node = data_of_mothernodes[ node1 ][ functionlabel ]
        timing_graph.add_edge( nodeid, tmp_after_node )
    for functionlabel in before_other:
        tmp_after_node = data_of_mothernodes[ node2 ][ functionlabel ]
        timing_graph.add_edge( nodeid, tmp_after_node )

def compile_code( timing_graph ):
    nodelayers = DiGraph_to_layers( timing_graph )
    functionlayer = nodelayers_to_functionlayers( timing_graph, nodelayers )
    def cycle_function():
        for i in functionlayer:
            for j in i:
                j()
    return cycle_function

def nodelayers_to_functionlayers( mygraph, nodelayers ):
    """
    returns a list of lists of function
    Each function must be callable without arguments. So everyfunction must be
    decorated with its arguments to be used further
    """
    functionlayers = []
    for layer in nodelayers:
        newlayer = []
        for node in layer:
            data = mygraph.nodes(data=True)[ node ]
            try:
                tmpfunction = data[ NODEFUNCTION ]
                function_variables = data #this holds more than only func_vars
            except KeyError as err:
                err.args = (*err.args, "Check if nodefunction key is set "\
                        + "correct inside the timing graph of "\
                        + "nodetype %s"%("(ahm oops)"), \
                        "timinggraphnode has following "\
                        + "attributes:%s"%(repr(data))
                        )
                raise err
            newlayer.append( static_variables( tmpfunction, \
                                            function_variables) )

        functionlayers.append( newlayer )
    return functionlayers

def DiGraph_to_layers( mydigraph ):
    restnodes = set( mydigraph.nodes() )
    layers = []
    while len( restnodes )>0:
        restgraph = mydigraph.subgraph( restnodes )
        nextlayer = [ n for n in restgraph.nodes() \
                        if len( set(restgraph.predecessors(n))) == 0 ]
        layers.append( nextlayer )
        restnodes = set(restgraph.nodes()).difference( nextlayer )
    return layers


def add_code_of_functioncontainers_to_timing_graph( graph, timing_graph ):
    for node, data in graph.nodes( data=True ):
        tiny_timing = data[ NODEFUNCTIONCONTAINER ].get_timing_graph()
        tiny_timing = netx.MultiDiGraph( tiny_timing )
        netx.set_node_attributes( tiny_timing, \
                                    { n:node for n in tiny_timing.nodes() }, \
                                    MOTHERNODE )
        netx.set_node_attributes( tiny_timing, \
                                    { n:n for n in tiny_timing.nodes() }, \
                                    TIMINGSUBLABEL )

        timing_graph = netx.disjoint_union( timing_graph, tiny_timing )

    #save the timing nodes in original graph for finding purposes, see edges
    for timingnode, data in timing_graph.nodes( data=True ):
        netx.set_node_attributes( graph, {data[MOTHERNODE]: timingnode}, \
                                    data[TIMINGSUBLABEL] )
    return timing_graph



def generate_all_nodefunctioncontainers_from_graph( graph ):
    nodeid_to_functioncontainer = {}
    for node, data in graph.nodes( data=True ):
        nodegenerator = data[ NODECLASS ]
        #init_varnames = inspect.getargspec( nodegenerator.__init__ )[0][1:]
        init_varnames = list( inspect.signature( nodegenerator.__init__ )\
                                                        .parameters)[1:]
        # throw away the object-reference('self') and default values

        init_variables = { varname: data[ varname ] \
                            for varname in data \
                            if varname in init_varnames }
        #init_variables = { varname: data[ varname ] \
        #                    for varname in init_varnames}
        try:
            functioncontainer = generate_nodefunctioncontainer( node, \
                                                nodegenerator, init_variables )
        except TypeError as err:
            err.args = (*err.args, "Node: %s, class: %s"%(node, \
                                    nodegenerator.__name__))
            raise err
        nodeid_to_functioncontainer.update( { node: functioncontainer } )

    netx.set_node_attributes( graph, nodeid_to_functioncontainer, \
                                NODEFUNCTIONCONTAINER)


def static_variables( function, functionvariables ):
    """
    makes a function callable with no arguments. makes all the given argument
    s frorm functionvariables static to the given function
    :todo: default values doesnt need to be set
    """
    # always use class methods. So the argument contains always 'self'
    # hence the argument count must be higher than 1 to need to insert extras
    if function.__code__.co_argcount > 1:
        # filter arguments for arguments for method
        #myvarnames = inspect.getargspec( function )[0][1:]
        myvarnames = list( inspect.signature( function ).parameters)[:]
        try:
            funcvars = { varname: functionvariables[ varname ] \
                            for varname in myvarnames }
        except KeyError as err:
            err.args = ( *err.args, "couldnt find all needed variables for"\
                                + " function %s"%( function.__code__.co_name ) )
            raise err
        def newfunction():
            function( **funcvars )

        return newfunction

    else:
        return function

def generate_nodefunctioncontainer( nodeid, nodegenerator, init_variables ):
    try:
        mycontainer = nodegenerator( **init_variables )
    except TypeError as err:
        err.args = ( *err.args, "all required arguments for class init must be"\
                + " as given as node attribute" )
        raise err
    return mycontainer

class nodefunctioncontainer():
    inputvariables = []
    def __init__( self ):
        self.timing_graph = netx.MultiDiGraph()
        self.edge_to_dictionary = {}

    propertyfilter = ["timing_graph", "edge_to_dictionary"]
    def get_properties( self ):
        filtered_properties = { key: prop for key,prop in self.__dict__.items()\
                                if key not in self.propertyfilter }
        return filtered_properties

    def add_possible_edge_to( self, other_type, edgetype, function, \
                                timing_after_self, timing_before_self,\
                                timing_after_other, timing_before_other ):
        """
        :param timing_after_self: array of node_id in timing_graph
                                the function will be called after every function
                                of those nodes
        """
        self.edge_to_dictionary.update( {(other_type, edgetype): (function,\
                                timing_after_self, timing_before_self,\
                                timing_after_other, timing_before_other )})

    def get_timing_graph( self ):
        return self.timing_graph

