import networkx as netx
#weisfeiler_lehmann_graph_hash = netx.graph_hashing.weisfeiler_lehman_graph_hash
from extrasfornetworkx import weisfeiler_lehman_graph_hash_multidigraph \
                                as weisfeiler_lehman_graph_hash
from .processes import get_all_processes, get_datanode_maximal_occurence
import itertools
import math
from collections import Counter
from .constants import DATAGRAPH_DATATYPE as DATATYPE
from .constants import DATAGRAPH_EDGETYPE as EDGETYPE


class datastate_not_connected_error( Exception ):
    pass

def create_flowgraph_for_datanodes( factoryleaf_list, conclusionleaf_list=[]):
    """
    :rtype: flowgraph
    :type factoryleaf_list: iterable
    :type *factoryleaf_list: process.factoryleaf
    """
    factoryleaf_list = list( factoryleaf_list )
    node_to_datatype, datatype_to_node = get_my_nodelists( factoryleaf_list )

    visible_datagraphs = flowgraph( node_to_datatype )
    conclusionlist = translate_conclusion_leaf( visible_datagraphs, \
                                        datatype_to_node,\
                                        node_to_datatype, conclusionleaf_list )

    try:
        all_processes = list( translate_factoryleaf_to_datastateeffect( 
                                        visible_datagraphs, datatype_to_node,\
                                        factoryleaf_list, node_to_datatype, \
                                        conclusionlist ) )
    except datastate_not_connected_error as err:
        err.args = (*err.args, "couldnt create flowgraph, cause factoryleafs have broken datagraphs as input/output" )
        raise err
    startdatastates = [ proc.inputdatastate for proc in all_processes ]
    visible_datagraphs.set_startgraphs( startdatastates )
    visible_datagraphs.extend_visible_datagraphs_fully( all_processes )
    return visible_datagraphs

class conclusionleaf_effect():
    def __init__( self, mother_flowgraph, myconclusionleaf, \
                                        translation_of_nodes ):
        self.conclusionleaf = myconclusionleaf
        self.trans = translation_of_nodes
        self.mother_flowgraph = mother_flowgraph
        trans = translation_of_nodes
        inputgraph = myconclusionleaf.prestatus
        tmpnodes = [ trans[ node ] for node in inputgraph.nodes() ]
        tmpedges = [ ( trans[e[0]], trans[e[1]], e[-1][EDGETYPE] ) \
                        for e in inputgraph.edges( data=True ) ]
        self.inputdatastate = datastate( mother_flowgraph, tmpnodes, tmpedges )

        outputgraph = myconclusionleaf.poststatus
        tmpnodes = [ trans[ node ] for node in outputgraph.nodes() ]
        tmpedges = [ ( trans[e[0]], trans[e[1]], e[-1][EDGETYPE] ) \
                        for e in outputgraph.edges( data=True ) ]
        self.outputdatastate = datastate( mother_flowgraph, tmpnodes, tmpedges )

        self._created_edge_functions = dict()
        
        self.added_edges = self.outputdatastate.edges \
                            .difference( self.inputdatastate.edges )
    
    def operate_on( self, mydatastate ):
        if self.inputdatastate.issubset_to( mydatastate ):
            return datastate( mydatastate._flowgraph, \
                            mydatastate.nodes, \
                            mydatastate.edges.union( self.added_edges ) )
        else:
            return mydatastate

class factoryleaf_effect():
    def __init__( self, mother_flowgraph, factoryleaf, translation_of_nodes,\
                        extra_conclusions = [] ):
        self.factoryleaf = factoryleaf
        self.trans = translation_of_nodes
        self.mother_flowgraph = mother_flowgraph
        trans = translation_of_nodes

        inputgraph = factoryleaf.prestatus
        tmpnodes = [ trans[ node ] for node in inputgraph.nodes() ]
        tmpedges = [ ( trans[e[0]], trans[e[1]], e[-1][EDGETYPE] ) \
                        for e in inputgraph.edges( data=True ) ]
        try:
            self.inputdatastate = datastate( mother_flowgraph, tmpnodes, \
                                                                    tmpedges )
        except datastate_not_connected_error as err:
            err.args = (*err.args, f"factoryleaf {factoryleaf} hash broken "\
                            "input/output- datagraph." )
            raise err

        outputgraph = factoryleaf.poststatus
        tmpnodes = [ trans[ node ] for node in outputgraph.nodes() ]
        tmpedges = [ ( trans[e[0]], trans[e[1]], e[-1][EDGETYPE] ) \
                        for e in outputgraph.edges( data=True ) ]
        tmpstate = datastate( mother_flowgraph, tmpnodes, tmpedges )
        for tmp_conclusioneffect in extra_conclusions:
            tmpstate = tmp_conclusioneffect.operate_on( tmpstate )
        self.outputdatastate = tmpstate
        del( tmpstate )

        self._created_edge_functions = dict()


    def _get_cost( self ):
        return self.factoryleaf.cost
    cost = property( fget=_get_cost )

    def _get_antitrans( self ):
        return { value: key for key, value in self.trans.items() }
    antitrans = property( fget = _get_antitrans )

    def addition_nodes( self ):
        new = self.outputdatastate.nodes
        old = self.inputdatastate.nodes
        return new.difference( old )

    def remove_nodes( self ):
        new = self.outputdatastate.nodes
        old = self.inputdatastate.nodes
        return old.difference( new )

    def additional_edges_with_newnodes( self, nodeset ):
        """
        Add all edges, where both nodes are within the new nodeset
        """
        out_edges = self.outputdatastate.edges
        return [ edge for edge in out_edges \
                        if (edge[1] in nodeset and edge[0] in nodeset )]

    def extend_datanode( self, superdatastate ):
        if self.inputdatastate.issubset_to( superdatastate ):
            my_add = self.addition_nodes()
            my_remove = self.remove_nodes()
            if not superdatastate.nodes.intersection( my_add ):
                powerset_addnodes = _custom_powerset( my_add )
                for addnodes in powerset_addnodes:
                    returndatastate = self._create_nextdatastate( addnodes, \
                                                            superdatastate )
                    if returndatastate:
                        yield returndatastate

    def get_edge_function( self, input_datastate ):
        if input_datastate in self._created_edge_functions:
            return self._created_edge_functions[ input_datastate ]
        else:
            new_edge_function = self._create_new_edge_function( input_datastate)
            self._created_edge_functions[ input_datastate ] = new_edge_function
            return new_edge_function


    def _create_nextdatastate( self, addnodes, input_datastate, ):
        tmpnodes = input_datastate.nodes.union( addnodes )
        tmpnodes = tmpnodes.difference( self.remove_nodes() )

        addedges = self.additional_edges_with_newnodes( tmpnodes )

        tmpedges = input_datastate.edges.union( addedges )
        tmpedges = frozenset( edge for edge in tmpedges \
                                    if ( edge[1] in tmpnodes \
                                    and edge[0] in tmpnodes ) )
        tmpnodes = only_nodes_connected_to_given_nodes( tmpnodes, \
                                    [ (edge[0],edge[1]) for edge in tmpedges], \
                                    addnodes )
        tmpedges = frozenset( edge for edge in tmpedges \
                                    if ( edge[1] in tmpnodes \
                                    and edge[0] in tmpnodes ) )
        try:
            return datastate( self.mother_flowgraph, tmpnodes, tmpedges )
        except datastate_not_connected_error:
            return None


    def _create_dict_inputstate_with_newnodes_to_outputstate( \
                                                    self, input_datastate ):
        possible_outputstate = {}
        my_add = self.addition_nodes()
        my_remove = self.remove_nodes()
        for addnodes in _custom_powerset( my_add ):

            returndatastate = self._create_nextdatastate( addnodes, \
                                                            input_datastate )
            if returndatastate:
                addnodes_factleaf = ( self.antitrans[ node ] \
                                        for node in addnodes)
                possible_outputstate[ frozenset( addnodes_factleaf ) ] \
                                                            = returndatastate
        return possible_outputstate



    def _create_new_edge_function( self, input_datastate ):
        possible_outputstate = \
                    self._create_dict_inputstate_with_newnodes_to_outputstate( \
                                                            input_datastate )

        transition_function = self.factoryleaf.call_function

        mytrans = self.trans
        myantitrans = self.antitrans
        mother_flowgraph = self.mother_flowgraph
        inputdatatrans = tuple( (factkey, key) \
                            for factkey, key in mytrans.items() \
                            if key in input_datastate.nodes )
        def edge_transition_function():
            foo_input = { factkey: mother_flowgraph.data[key] \
                            for factkey, key in inputdatatrans }

            try:
                foo_output = transition_function( **foo_input )
            except TypeError as err:
                err.args = ( *err.args, "happened at {self.factoryleaf}" )
                raise err
            try:
                for factkey, single_output in foo_output.items():
                    mother_flowgraph.data[ mytrans[ factkey ] ] = single_output
            except AttributeError as err:
                err.args = (*err.args, f"{self.factoryleaf} has given wrong "\
                            +"output", f"got: {foo_output}")
                raise err

            mother_flowgraph.datastate = possible_outputstate[ \
                                            frozenset(foo_output.keys()) ]

        return edge_transition_function




class conclusion_process():
    def __init__( self, inputgraph, outputgraph, datatype_to_node, \
                            motherleaf, node_to_datatype, \
                            factleaf_to_process_translator, cost=1.0 ):
        self.inputgraph = self._duplicate_and_filter_graph( inputgraph )
        self.outputgraph = self._duplicate_and_filter_graph( outputgraph )
        self.motherleaf = motherleaf
        self.node_to_datatype = node_to_datatype 
        self.datatype_to_node = datatype_to_node
        self.cost = cost
        self.antitrans = factleaf_to_process_translator

        self.add_edges = self._create_add_edges( outputgraph, inputgraph )

    def _create_add_edges( self, outgraph, ingraph ):
        add_edges = set( outgraph.edges( keys=True ) )\
                            .difference( ingraph.edges( keys=True ) )
        edgetypes = netx.get_edge_attributes( outgraph, EDGETYPE )
        return [ (edge[0],edge[1],edgetypes[ edge ]) for edge in add_edges ]

    def _duplicate_and_filter_graph( self, graph ):
        tmpgraph = netx.MultiDiGraph()
        tmpgraph.add_nodes_from( graph.nodes() )
        tmpgraph.add_edges_from( graph.edges( data=True ) )

        return tmpgraph


def datastate_from_graph( motherflowgraph, mydatagraph ):
    node_to_datatype = motherflowgraph.node_to_datatype
    nodes, edges = _transform_datagraph_to_nodes_edges( mydatagraph )
    return datastate( motherflowgraph, nodes, edges )


def _transform_datagraph_to_nodes_edges( mydatagraph ):
    nodes = frozenset( mydatagraph.nodes() )
    edgetype = netx.get_edge_attributes( mydatagraph, EDGETYPE )
    edges = ( (e[0],e[1], edgetype[ e ]) \
            for e in mydatagraph.edges( keys=True ) )
    edges = frozenset( edges )
    return nodes, edges

class datastate():
    def __init__( self, mother_flowgraph, nodes, edges ):
        self._flowgraph = mother_flowgraph
        self.nodes, self.edges = frozenset( nodes ), frozenset( edges )

        if not self.is_connected():
            nodesandtypes = {node: mother_flowgraph.node_to_datatype[node] \
                                for node in nodes }
            raise datastate_not_connected_error( \
                                f"nodes are: {nodesandtypes}. "\
                                +f"Edges are {edges}" )

    def _get_node_to_datatype( self ):
        return self._flowgraph.node_to_datatype

    node_to_datatype = property( fget = _get_node_to_datatype )

    def is_connected( self ):
        testgraph = netx.Graph()
        for node in self.nodes:
            testgraph.add_node( node )
        for edge in self.edges:
            testgraph.add_edge( edge[0], edge[1] )
        return netx.is_connected( testgraph )

    def __repr__( self ):
        return f"data({tuple(self.nodes)}, {tuple(self.edges)})"

    def reachable_with_process( self, myprocess ):
        if myprocess.valid_for_nodelist( ( self.nodes, self.edges ) ):
            for node_add, edge_add in myprocess.additions:
                tmpnode = self.nodes.union( node_add )
                tmpedge = self.edges.union( edge_add )
                yield( datastate( self._flowgraph, tmpnode, tmpedge ) )

    def __hash__( self ):
        return ( self.nodes, self.edges ).__hash__()

    def weisfeil_hash( self ):
        replicate_graph = netx.MultiDiGraph()
        replicate_graph.add_nodes_from( self.nodes )
        #tmpedges = { ((e0, e1), e2) for e0, e1, e2 in self.edges }
        for e0, e1, data in self.edges:
            replicate_graph.add_edge( e0, e1, eattr=repr(data) )
        tmp = self.node_to_datatype
        tmp = { node: repr(value) for node, value in tmp.items() }
        netx.set_node_attributes( replicate_graph, tmp, "nattr" )
        return int( weisfeiler_lehman_graph_hash( replicate_graph, node_attr="nattr", edge_attr="eattr" ), 16 )

    def issubset_to( self, other_datastate ):
        chk1 = all([ node in other_datastate.nodes for node in self.nodes ])
        chk2 = all([ edge in other_datastate.edges for edge in self.edges ])
        return chk1 and chk2

    def __eq__( self, other ):
        if other.__hash__:
            return self.__hash__() == other.__hash__()
        else:
            return False


class flowgraph( netx.MultiDiGraph ):
    """
    :param newestdatagraphs: private data
    :param node_to_datatype: dictionary to examine which node is 
                            which datatype corresponds to nodes; 
                            see Object.nodes()
    :param set_startgraphs: Mmmhhh
    """
    def __init__( self, node_to_datatype ):
        super().__init__()
        self.newestdatagraphs = set()
        self.node_to_datatype = node_to_datatype


    def _reverse_node_to_datatype( self ):
        tmpdictionary = {}
        for nodeid, datatype in self.node_to_datatype:
            tmplist = tmpdictionary.setdefault( datatype, list() )
            tmplist.append( nodeid )
            del( tmplist )
        return tmpdictionary
    datatype_to_nodelist = property( fget = _reverse_node_to_datatype )


    def datastate_to( self, mydatagraph ):
        #create one possible translation
        nodelist = list( mydatagraph.nodes() )
        nodeattr = netx.get_node_attributes( mydatagraph, DATATYPE )
        nodetypelist = [ nodeattr[ node ] for node in nodelist ]
        possible_translation = [ self.datatype_to_nodelist[ nodetype ] \
                                    for nodetype in nodetypelist ]
        equivalent_nodes = [ tmptrans \
                    for tmptrans in itertools.product( *possible_translation ) \
                    if max( Counter(tmptrans).values() ) == 1 ]
        translation = { nodelist[i]: equivalent_nodes[0][i] \
                            for i in range( len( nodelist) ) }

        #use translation to get equivalent datastate
        relabeled_datagraph = netx.relabel_nodes( mydatagraph, translation )
        nodes, edges = _transform_datagraph_to_nodes_edges( \
                                                    self.nodedatatypelist, \
                                                    relabeled_datagraph )
        return datastate( self, nodes, edges )


    def set_startgraphs( self, startdatagraphs ):
        tmplist = []
        for node in startdatagraphs:
            self.add_node( node )
            tmplist.append( node )
        self.newestdatagraphs = tmplist


    def _get_datatype_to_node( self ):
        datatype_to_node = {}
        for node, datatype in self.node_to_datatype.items():
            tmplist = datatype_to_node.setdefault( datatype, list() )
            tmplist.append( node )
        del( tmplist )
        return datatype_to_node

    datatype_to_node = property( fget = _get_datatype_to_node )


    def translator( self, *graphs ):
        """
        :type graphs: networkx.Graph
        :todo: This function must be rehauled
        """
        graphnode_to_datatype = {}
        for graph in graphs:
            graph.raise_exception_if_not_valid()
            graphnode_to_datatype.update( netx.get_node_attributes( graph, \
                                                                    DATATYPE ))
        datatype_to_node = self.datatype_to_node
        possible_translations = create_possible_translation_of_nodelist( \
                                            graphnode_to_datatype, \
                                            datatype_to_node )
        return possible_translations

        possible_translation = {}
        alldata = {}
        alledgedata = {}
        for graph in graphs:
            data = netx.get_node_attributes( graph, DATATYPE )
            if set( graph.nodes() ) != data.keys():
                raise KeyError( )
            alldata.update( data )
            edgedata = netx.get_edge_attributes( graph, EDGETYPE )
            alledgedata.update( edgedata )
        del( data, edgedata )
        graph_nodes = list( alldata.keys() )
        alldata = [ alldata[key] for key in graph_nodes ]
        try:
            possible_alternative_nodes = [ datatype_to_node[ datatype ] \
                                        for datatype in alldata ]
        except Exception as err:
            err.args = (*err.args, "list of available nodes from "\
                                    +f"flowgraph: {datatype_to_node}" )
            raise err
        possible_translations = itertools.product( *possible_alternative_nodes )
        possible_translations = [ trans for trans in possible_translations \
                                    if max( Counter( trans ).values() ) == 1 ]

        foundtranslation = None
        for nodelist in possible_translations:
            trans = { graph_nodes[i]: nodelist[i] for i in range(len(nodelist))}
            tmpedges = [(trans[ edge[0] ], trans[ edge[1] ], data) \
                        for edge, data in alledgedata.items() ]
            tmpedges = frozenset( tmpedges )
            tmpnodes = frozenset( trans.values() )
            for datastate in self.nodes():
                datanodes, dataedges = datastate.nodes, datastate.edges
                if len( tmpnodes.difference( datanodes ) )==0\
                        and len( tmpedges.difference( dataedges ) ) ==0:
                    foundtranslation = trans
                    # return foundtranslation ?
                    break
            if foundtranslation:
                break
        del( tmpedges, tmpnodes )
        if not foundtranslation:
            all_nodes =set(itertools.chain(*(graph.nodes()\
                                            for graph in graphs)))
            raise KeyError( "Couldnt find possible translation for given"\
                            +" datagraph. You can get a complete list of"\
                            +"of possible datagraphs with the method"\
                            +" thisobject.nodes()", \
                            f"for given graph {all_nodes} "\
                            +"searched with following translations "\
                            +f"{possible_translations} reachable datastate "\
                            +"of flowgraph; see flowgraph.nodes()"  )

        return foundtranslation
        

    def get_superstates_to( self, tmpdatastate ):
        issubset = lambda s, superstate: not set( s ).difference( superstate )
        return [ state for state in self.nodes() \
                if issubset( tmpdatastate.nodes, state.nodes ) \
                and issubset( tmpdatastate.edges,state.edges ) ]

    def extend_visible_datagraphs_fully( self, processlist ):
        while self.newestdatagraphs:
            oldnodes = list( self.nodes() )
            tmpset = set()
            tmplist = []
            next_newestdatagraphs = []
            for tmpdatastate, factleaf_effect in itertools.product( \
                                        self.newestdatagraphs, processlist ):
                lll = factleaf_effect.extend_datanode( tmpdatastate )
                for newdatastate in lll:
                    myfoo = factleaf_effect.get_edge_function( tmpdatastate )
                    self.add_edge( tmpdatastate, newdatastate, \
                                    edgetype = factleaf_effect, \
                                    edgefunction = myfoo, \
                                    weight = factleaf_effect.cost )
                    next_newestdatagraphs.append( newdatastate )
            self.newestdatagraphs = set( next_newestdatagraphs )\
                                    .difference( oldnodes )
        return



def translate_factoryleaf_to_datastateeffect( givenflowgraph, \
                                        datatype_to_node, factoryleaflist, \
                                        node_to_datatype, conclusionlist ):
    """
    :type my_factory_leaf: .classes.factory_leaf
    :type datatype_to_node: dictionary
    :param datatype_to_node: This projects a datatype to a list of possible
                            id's (int)
    :rtype: list, type( list[i] ) == process
    """
    processlist = []
    for factleaf in factoryleaflist:
        all_nodes, factleaf_node_to_datatype \
                        =  _extract_info_from_factleaf( factleaf )
        possible_translations = create_possible_translation_of_nodelist( \
                                        factleaf_node_to_datatype, \
                                        datatype_to_node )
        # possible_translations is now a list of dictionaries
        # every dictionary projects the nodes of the factleaf_graphs unto 
        # the node_collections 'datatype_to_node'

        for singletrans in possible_translations:
            try:
                bubu = factoryleaf_effect( givenflowgraph, factleaf, \
                                        singletrans, conclusionlist )
            except datastate_not_connected_error as err:
                err.args = (*err.args, f"happened with factoryleaf {factleaf}")
                raise err
            yield( bubu )


def create_possible_translation_of_nodelist( \
                                inputnode_to_datatype, datatype_to_outnode ):
    possiblenodeslist_list = []
    all_nodes = list( inputnode_to_datatype.keys() )
    for node in all_nodes:
        possible_nodes_for_singletype \
                = datatype_to_outnode[ inputnode_to_datatype[ node ] ]
        possiblenodeslist_list.append(  possible_nodes_for_singletype  )

    equivnodeslists = itertools.product( *possiblenodeslist_list )
    equivalent_nodelist_to_in_out_graph \
                        = [ trans for trans in equivnodeslists \
                            if max(Counter(trans).values()) == 1 ]
    del( equivnodeslists )

    possible_translations = [ list(itertools.zip_longest( all_nodes, trans))
                        for trans in equivalent_nodelist_to_in_out_graph ]
    possible_translations = [ { oldnode: newnode \
                            for oldnode, newnode in singletrans }
                            for singletrans in possible_translations ]
    return possible_translations


def translate_conclusion_leaf( givenflowgraph, datatype_to_node, \
                                node_to_datatype, conclusionleaf_list ):
    translated_conclusionlist = []
    for conclusion in conclusionleaf_list:
        all_nodes, factleaf_node_to_datatype \
                        =  _extract_info_from_factleaf( conclusion )
        try:
            possible_translations = create_possible_translation_of_nodelist( \
                                        factleaf_node_to_datatype, \
                                        datatype_to_node )
        #catch error if not all datatypes of conclusion is are used
        except KeyError: 
            possible_translations = list()
        for singletrans in possible_translations:
            bubu = conclusionleaf_effect( givenflowgraph, conclusion, \
                                            singletrans)

            translated_conclusionlist.append( bubu )
    return translated_conclusionlist


def _extract_info_from_factleaf( factleaf ):
    """
    :type factleaf: .processes.factory_leaf
    """
    # extract information from factoryleaflist
    inputgraph = factleaf.prestatus #.copy()
    outputgraph = factleaf.poststatus #.copy()
    #inputnodes = set( inputgraph.nodes() )
    all_nodes = set( inputgraph.nodes() )\
                        .union( outputgraph.nodes() )
    datatype_dict = netx.get_node_attributes( inputgraph, DATATYPE )
    datatype_dict.update( netx.get_node_attributes( outputgraph, DATATYPE))
    return all_nodes, datatype_dict





def get_my_nodelists( processlist ):
    """
    This method return a list of datatypes. This list of datatypes functions
    as nodes that i use. If in the processes a datatype is used multiple
    times, there are multiple instances of that datatype in the list

    use strings as integers
    """
    max_occurences = get_datanode_maximal_occurence( processlist )
    node_type = {}
    datatype_to_node = {}
    myid = 0
    for datatype, occur in max_occurences.items():
        for x in range( occur ):
            nodeid = f"d{myid}" #example 'd1'
            myid = myid + 1
            #nodelist.append( datatype )
            node_type[ nodeid ] = datatype
            datatypelist = datatype_to_node.setdefault( datatype, list() )
            datatypelist.append( nodeid )
            del( datatypelist ) #this deletes the symbol not the list itself
    return node_type, datatype_to_node



def _custom_powerset(iterable):
    "powerset([1,2,3]) --> (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    #iterable = list( iterable )
    list_of_lists = list()
    for length in range( 1, len( iterable ) +1 ):
        list_of_lists.append( 
                itertools.combinations( iterable, length ) 
                )
    return itertools.chain( *list_of_lists )

def only_nodes_connected_to_given_nodes( mynodes, myedges, addnodes ):
    if len( addnodes ) == 0:
        return mynodes
    asd = netx.Graph()
    asd.add_nodes_from( mynodes )
    asd.add_edges_from( myedges )
    components = netx.algorithms.components.connected_components( asd )
    thereisnewconnected = lambda mylist: any([ n in mylist for n in addnodes ])
    components = [ single for single in components \
                    if thereisnewconnected( single ) ]
    return frozenset( itertools.chain( *components ) )
