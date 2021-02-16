import networkx as netx
from .processes import get_all_processes, get_datanode_maximal_occurence
import itertools
import math
from collections import Counter
from .constants import DATAGRAPH_DATATYPE as DATATYPE
from .constants import DATAGRAPH_EDGETYPE as EDGETYPE

def create_flowgraph_for_datanodes( factoryleaf_list, conclusionleaf_list=[]):
    """
    :rtype: flowgraph
    :type factoryleaf_list: iterable
    :type *factoryleaf_list: process.factoryleaf
    """
    factoryleaf_list = list( factoryleaf_list )
    node_to_datatype, datatype_to_node = get_my_nodelists( factoryleaf_list )

    conclusionlist = translate_conclusion_leaf( datatype_to_node,\
                                        node_to_datatype, conclusionleaf_list )
    all_processes = translate_factoryleaf_to_process( datatype_to_node, \
                                        factoryleaf_list, node_to_datatype, \
                                        conclusionlist )

    visible_datagraphs = flowgraph( node_to_datatype )
    visible_datagraphs.set_startgraphs( all_processes )
    visible_datagraphs.extend_visible_datagraphs_fully( all_processes )
    return visible_datagraphs

class process():
    def __init__( self, inputgraph, outputgraph, datatype_to_node, \
                            motherleaf, node_to_datatype, \
                            factleaf_to_process_translator, \
                            extra_conclusions, cost=1.0 ):
        self.inputgraph = self._duplicate_and_filter_graph( inputgraph, None )
        self.outputgraph = self._duplicate_and_filter_graph( outputgraph, \
                                                        extra_conclusions )
        self.extra_conclusions = extra_conclusions
        self.motherleaf = motherleaf
        self.node_to_datatype = node_to_datatype 
        self.datatype_to_node = datatype_to_node
        self.cost = cost
        self.antitrans = factleaf_to_process_translator

        self.add_edges = self._create_add_edges( outputgraph, inputgraph )

        self.delete_nodes = set( self.inputgraph.nodes() )\
                                        .difference( self.outputgraph.nodes() )
        self.exclusion_criterion = set( self.outputgraph.nodes() )\
                                        .difference( self.inputgraph.nodes() )

    def _create_add_edges( self, outgraph, ingraph ):
        add_edges = set( outgraph.edges( keys=True ) )\
                            .difference( ingraph.edges( keys=True ) )
        edgetypes = netx.get_edge_attributes( outgraph, EDGETYPE )
        return [ (edge[0],edge[1],edgetypes[ edge ]) for edge in add_edges ]

    def _duplicate_and_filter_graph( self, graph, extra_conclusions ):
        tmpgraph = netx.MultiDiGraph()
        tmpgraph.add_nodes_from( graph.nodes() )
        tmpgraph.add_edges_from( graph.edges( data=True ) )

        if extra_conclusions:
            for a in extra_conclusions:
                a.add_extra_edge_through_conclusion( a, tmpgraph )

        return tmpgraph

    def __call__( self, **args ):
        """
        :todo: get rid of object_generation 'self.motherleaf()'
        """
        trans = self.translation
        antitrans = self.antitrans
        args = { trans[key]: args[ key ] for key in self.inputgraph.nodes()}
        #args = { trans[key]: value for key, value in args.items() }
        returnval = self.motherleaf( **args )
        try:
            filtered_return = { antitrans[key]: value \
                                for key, value in returnval.items() }
        except AttributeError as err:
            err.args = (*err.args, f"factory_leaf {self.motherleaf} "\
                                    +"returned not a dictionary")
            raise err

        return filtered_return


    def _get_translation_process_to_factleaf( self ):
        return { value:key for key, value in self.antitrans.items() }

    translation = property( fget=_get_translation_process_to_factleaf )

    def _get_additional_nodes_and_edges_through_process( self ):
        tmpsets = _custom_powerset( self.exclusion_criterion )
        tmpsets = [ set( self.inputgraph.nodes() ).union( single )\
                        for single in tmpsets ]
        newgraphs = [ self.outputgraph.subgraph( nodeset ) \
                        for nodeset in tmpsets ]
        newedges = [ set( tmpG.edges( keys=True ) )\
                        .difference( self.inputgraph.edges( keys=True ) )\
                        for tmpG in newgraphs ]
        edgetype = netx.get_edge_attributes( self.outputgraph, EDGETYPE )
        newedges = [ set(( e[0],e[1],edgetype[e] ) for e in tmplist ) \
                    for tmplist in newedges ]
        newnodes = [ set( tmpG.nodes() ).difference( self.inputgraph.nodes() )\
                        for tmpG in newgraphs ]
        return list( itertools.zip_longest( newnodes, newedges ) )


    additions = property(fget =_get_additional_nodes_and_edges_through_process )

    def valid_for_nodelist( self, nodeedgelist ):
        """
        :todo: use a datastate instead of a datagraph
        """
        nodelist = nodeedgelist[0]
        edgelist = nodeedgelist[1]
        condition1 = not any( [ node in nodelist \
                            for node in self.exclusion_criterion ] )
        condition2 = all( [ node in nodelist \
                            for node in self.inputgraph.nodes() ] )
        condition3 = all( [ (edge[0],edge[1],edge[-1][EDGETYPE]) in edgelist \
                            for edge in self.inputgraph.edges(data=True) ] )
        return all( ( condition1, condition2, condition3 ) )

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

    def _get_node_to_datatype( self ):
        return self._flowgraph.node_to_datatype

    node_to_datatype = property( fget = _get_node_to_datatype )

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
    def __init__( self, node_to_datatype, startprocesslist = None ):
        super().__init__()
        self.newestdatagraphs = set()
        self.node_to_datatype = node_to_datatype
        if startprocesslist:
            self.set_startgraphs( startprocesslist )

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

    def set_startgraphs( self, startprocesslist ):
        tmpset = set()
        for tmpprocess in startprocesslist:
            nextnode = datastate_from_graph( self, \
                                       tmpprocess.inputgraph)
            self.add_node( nextnode )
            tmpset.add( nextnode )
        self.newestdatagraphs = tmpset


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
        # error control every shared node must  not conflict with oneanother
        for graph in graphs:
            graph.raise_exception_if_not_valid()

        datatype_to_node = self.datatype_to_node

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
            err.args = (*err.args, f"list of available nodes from flowgraph: {datatype_to_node}" )
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
            tmpset = set()
            tmplist = []
            for tmpdatastate in self.newestdatagraphs:
                asd = [ ((tmpdatastate,), \
                        tmpdatastate.reachable_with_process( tmpprocess ), \
                        (tmpprocess,))\
                        for tmpprocess in processlist ]
                asd = ( itertools.product( *elist ) for elist in asd )
                asd = itertools.chain( *asd )
                tmplist.append( asd )
            edges = itertools.chain( *tmplist )

            oldnodes = tuple( self.nodes() )
            for oldgraph, newgraph, myprocess, in edges:
                tmpset.add( newgraph )
                self.add_node( newgraph )
                self.add_edge( oldgraph, newgraph, edgetype = myprocess, \
                                                    weight = myprocess.cost )
            self.newestdatagraphs = tmpset.difference( oldnodes )
       




def translate_factoryleaf_to_process( datatype_to_node, factoryleaflist, \
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

        possiblenodeslist_list = []
        all_nodes = list( all_nodes )
        for node in all_nodes:
            possible_nodes_for_singletype \
                    = datatype_to_node[ factleaf_node_to_datatype[ node ] ]
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
        # possible_translations is now a list of dictionaries
        # every dictionary projects the nodes of the factleaf_graphs unto 
        # the node_collections 'datatype_to_node'


        for singletrans in possible_translations:
            tmpingraph = netx.relabel_nodes( factleaf.prestatus, singletrans )
            tmpoutgraph = netx.relabel_nodes( factleaf.poststatus, singletrans )

            tmpprocess = process( tmpingraph, tmpoutgraph, \
                                        datatype_to_node, factleaf, \
                                        node_to_datatype, singletrans, \
                                        conclusionlist )
            processlist.append( tmpprocess )
            del( tmpprocess )
    return processlist


def translate_conclusion_leaf( datatype_to_node, node_to_datatype, \
                                        conclusionleaf_list ):
    translated_conclusionlist = []
    for conclusion in conclusionleaf_list:
        all_nodes, factleaf_node_to_datatype \
                        =  _extract_info_from_factleaf( conclusion )
        possiblenodeslist_list = []
        all_nodes = list( all_nodes )
        for node in all_nodes:
            possible_nodes_for_singletype \
                    = datatype_to_node[ factleaf_node_to_datatype[ node ] ]
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
        # possible_translations is now a list of dictionaries
        # every dictionary projects the nodes of the factleaf_graphs unto 
        # the node_collections 'datatype_to_node'


        for singletrans in possible_translations:
            tmpingraph = netx.relabel_nodes( conclusion.prestatus, singletrans )
            tmpoutgraph = netx.relabel_nodes( conclusion.poststatus,singletrans)

            conclusion_for_process = conclusion_process( \
                                            tmpingraph, tmpoutgraph, \
                                            datatype_to_node, conclusion, \
                                            node_to_datatype, singletrans )

            translated_conclusionlist.append( conclusion_for_process )


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
    datatype_dict = netx.get_node_attributes( inputgraph, "datatype" )
    datatype_dict.update( netx.get_node_attributes( outputgraph, "datatype"))
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

