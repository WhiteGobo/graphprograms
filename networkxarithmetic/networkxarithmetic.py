import networkx as netx
import numpy as _np
MYDTYPE  = _np.float64

import hashlib
import time

class NoStartvalueGiven_Error( Exception ):
    pass
class CycleToTree_Error( Exception ):
    pass

class graphcontainer():
    def __init__( self ):
        """
        this class generates code via a graph.
        :var calc_dict: identifies how a node with the corresponding edge will
                    progress in time
        :var calc_graph: defines the nodes, which hold all values an the 
                    interaction between those nodes.
        """
        self.compiled_code = None
        self.calc_dict = {}
        self.edge_dict = {}
        self.calc_graph = None
        self.time_graph = None
        self.extra_globals = None

    def transferdatatograph( self ):
        returngraph = netx.Graph()
        returngraph.add_nodes_from( self.codegraph )
        valueid_to_node_dict = dict()
        for pair in self.value_to_node_and_attribute:
            nodestovalueid = valueid_to_node_dict.setdefault( pair[1], list() )
            nodestovalueid.append( pair[0] )
        for valueid in valueid_to_node_dict:
            myvalues = dict()
            for node in valueid_to_node_dict[ valueid ]:
                i = self.value_to_node_and_attribute.index((node, valueid))
                y = self.values[i]
                myvalues.update({ node: y })
            netx.set_node_attributes( returngraph, myvalues, valueid )
        return returngraph

    def cycle( self ):
        self.values = self.cyclefunction( *self.values )

    def update_calclibrary( self, calc_dict ):
        """
        Calclib-key correspond to node-attribute 'calctype'
        calc_dict must contain methods to generate codesnippets and reserve
        dataspace
        :type calc_dict: dictionary
        """
        self.calc_dict.update( calc_dict )

    def update_edgelibrary( self, edge_dict ):
        """
        Edgelib-key correspond to edge-attribute 'edgetype'
        edge_dict assign tuple of (outnodetype, innodetype, edgename) a method
        to create the code
        foo return a codegraph
        """
        self.edge_dict.update( edge_dict )

    def createcode_with_graph( self, graph, numba_support=False ):
        """
        the calc_dict must contain methods for all node in graph
        :type graph: networkx.MultiDiGraph
        """
        self.codegraph = netx.MultiDiGraph( graph )
        self._generate_datacontainer()
        self._generate_code( self.codesnippet_graph, numba_support )


    def _generate_codedatafornodes( self, codegraph ):
        """
        :todo: rename self.codegraph and codegraph
        """
        self.value_to_node_and_attribute = []
        dataname_list = []
        startvalue_list = []
        valuename_list = []
        valuename_to_graphvalue = {} # {"value123(hash)": (nodeid, "attr")}
        nodes = self.codegraph.nodes( data = True )
        # generate nodes
        for nodeinfo in nodes:
            tmpnode = nodeinfo[0]
            tmpdata = nodeinfo[1]
            try:
                nodetypedata_dict, codesnippet, function_globals \
                        = self.calc_dict[ tmpdata["calctype"] ]()
            except KeyError as err:
                err.args = tuple([*err.args, "calclibrary doesnt include "\
                                            +"this key"])
                raise  err
            self.extra_globals.update( function_globals )
            for nodetype_datakey in nodetypedata_dict:
                tmp_valuename = tovaluename(tmpnode,  nodetype_datakey )
                valuename_to_graphvalue.update( {\
                            tmp_valuename: \
                            ( tmpnode, nodetype_datakey )
                            })
                valuename_list.append( tmp_valuename )
                # use as starting value value given in graph
                # and else the default value given via nodetypedata_dict
                startvalue = nodes[tmpnode].setdefault( nodetype_datakey, \
                                            nodetypedata_dict[nodetype_datakey])
                if startvalue == None:
                    raise NoStartvalueGiven_Error(\
                            "node %s with " %( str(tmpnode) ) \
                            +"nodetype %s needs a "%(tmpdata["calctype"])\
                            +"starting value for %s" %(str(nodetype_datakey))  )
                #dataname_list.append( dataname )
                startvalue_list.append( startvalue )
                self.value_to_node_and_attribute.append( \
                                            (tmpnode, nodetype_datakey))

            # replace codeplaceholders with datamapping
            _replace_nodecodesnippet_placeholders( codesnippet, dataname_list,\
                                                   str(tmpnode), tmpnode )
            # rename nodes
            tmpmapping = { node:str(tmpnode)+str(node) \
                                     for node in codesnippet.nodes() }
            codegraph.update( netx.relabel_nodes(codesnippet, tmpmapping) )
        return codegraph, dataname_list, startvalue_list, \
                        valuename_to_graphvalue, tuple( valuename_list )


    def _generate_codedata_for_edges( self, codegraph, dataname_list ):
        """
        :todo: rename codegraph and self.codegraph names doesnt say anything
        """
        for edgeinfo in self.codegraph.edges( data = True, keys = True ):
            tmpdata = edgeinfo[3]
            edgekey = edgeinfo[2]
            tmpnodeout = edgeinfo[0]
            tmpnodein = edgeinfo[1]
            otherattributes = dict(edgeinfo[3])
            otherattributes.pop("edgetype")
            outtype = self.codegraph.nodes()[ tmpnodeout ][ "calctype" ]
            intype = self.codegraph.nodes()[ tmpnodein ][ "calctype" ]

            # create code template, not usable until valuenames are replaced
            edgecommand = self.edge_dict[ (outtype, intype,tmpdata["edgetype"])]
            try:
                codenode, after_nodeout, after_nodein, \
                    before_nodeout, before_nodein, function_globals \
                    = edgecommand( **otherattributes  )
            except TypeError as err:
                err.args = ( *err.args, ("the edge between %s(%s) and %s(%s) "\
                                +"with command %s has attributes %s")%( \
                                    str(tmpnodeout), outtype, str(tmpnodein), \
                                        intype, str(edgekey), otherattributes ))
                raise err
            except Exception as err:
                err.args = ( *err.args, "happend at edgetype from %s to %s" \
                                    %(outtype, intype))
                raise err
            self.extra_globals.update( function_globals )
            try:
                _replace_edgecodesnippet_placeholders( codenode, \
                                dataname_list, str(tmpnodein), str(tmpnodeout), tmpnodein, tmpnodeout )
            except ValueError as err:
                err.args = ( *err.args, "node name w type are innode: " \
                                + "%s w %s; " %( tmpnodein, intype ) \
                                + "outnode: %s w %s" %( tmpnodeout, outtype, )
                            )
                raise err
            except KeyError as err:
                err.args = (*err.args, "check value-attribute of edgetype"\
                        + "(%s, %s, %s)"%(intype, outtype, tmpdata["edgetype"]))
                raise err

            # rename identifier for codesnippet in graph
            tmpmapping = { node:str(tmpnodeout)+str(tmpnodein) \
                                + str(edgekey) +str(node) \
                                     for node in codenode.nodes() }
            # :todo: this seemes like a duplicate
            codenode = netx.relabel_nodes( codenode, tmpmapping )
            codegraph.update( netx.relabel_nodes( codenode, tmpmapping) )
            # i should check here if every node has a code attribute but this
            # will be checked later in the code generation

            # create edges for timing of the code(outnode is exec. after innode)
            for nodetype in after_nodeout:
                codegraph.add_edge( str(tmpnodeout)+nodetype, *codenode.nodes())
            for nodetype in after_nodein:
                codegraph.add_edge( str(tmpnodein)+nodetype, *codenode.nodes())
            for nodetype in before_nodeout:
                codegraph.add_edge( *codenode.nodes(), str(tmpnodeout)+nodetype)
            for nodetype in before_nodein:
                codegraph.add_edge( *codenode.nodes(), str(tmpnodein)+nodetype)
        return codegraph

    def _generate_datacontainer( self ):
        """
        generates the code without edges with all the data containers needed by
        the nodes
        :raises NoStartvalueGiven_Error: raise exception if a default value is 
                            set to None and no startvalue is given by the graph
        """
        self.extra_globals = {} #create new
        codegraph = netx.DiGraph()
        codegraph, dataname_list, startvalue_list, valuename_to_graphvalue, valuename_order = \
                    self._generate_codedatafornodes( codegraph )

        codegraph = self._generate_codedata_for_edges( codegraph, dataname_list)

        # after this there should be th codegraph for _generate_code
        self.valuename_to_graphvalue = valuename_to_graphvalue
        self.valuename_order = valuename_order
        self.dataname_list = dataname_list
        self.startvalue_list = startvalue_list
        self.values = _np.array( startvalue_list, dtype = MYDTYPE )
        self.codesnippet_graph = codegraph



    def _generate_code( self, codesnippet_graph, numba_support ):
        nodelayers=[]
        tmpsubgraph = netx.DiGraph( codesnippet_graph )
        tmplastlength = len(tmpsubgraph)
        while len(tmpsubgraph) > 0:
            withoutneighbor = [x for x in tmpsubgraph.nodes() \
                                if len( list(tmpsubgraph.predecessors(x))) ==0]
            nodelayers.append( withoutneighbor )
            tmpsubgraph.remove_nodes_from( withoutneighbor )
            if tmplastlength == len(tmpsubgraph):
                raise CycleToTree_Error("couldnt create valid functionorder")
            tmplastlength = len(tmpsubgraph)

        nodetocode_dict = netx.get_node_attributes( codesnippet_graph, "code")
        if numba_support:
            usedvaluesdict = netx.get_node_attributes( codesnippet_graph, \
                                                                "usedvalues")
            mycode, number_functions = _smallfunction_combinecode( \
                                                self.valuename_order, \
                                                nodetocode_dict, nodelayers,\
                                                usedvaluesdict)
        else:
            mycode = _combinecode( self.valuename_order, \
                                                nodetocode_dict, nodelayers)
            number_functions = 1

        return_array = [None] * (number_functions+1)
        myglobals = {"return_array":return_array, "np":_np}
        if numba_support:
            import numba
            myglobals.update( {"njit":numba.njit} )
        myglobals.update( self.extra_globals )
        try:
            cmd_code = compile( mycode, "networkxarithmetic", "exec" )
        except SyntaxError:
            print( "Produced Code: \n", mycode )
            raise
        exec( cmd_code, myglobals )

        if numba_support:
            self.cyclefunction = return_array[-1]
        else:
            self.cyclefunction = return_array[0]
        self.compiled_code = mycode

dict_valueidentifier_translator = {
        "in":"innode", "target":"innode", "outedge":"innode",
        "out":"outnode", "source":"outnode", "inedge":"outnode",
        }

def _smallfunction_combinecode( valuename_ordered, nodetocode_dict, nodelayers,\
                                    usedvaluesdict, numba_support=True):
    mynumber = 2000
    len_nodelayers = [ len(layer) for layer in nodelayers ]
    asd = [ sum(len_nodelayers[0:i]) for i in range(len(len_nodelayers))]
    i=0
    qwe = []
    yy = []
    while i < len(asd):
        mydiff = asd[i] - mynumber
        if mydiff>0:
            yy.append(nodelayers[i][0:mydiff])
            qwe.append(yy)
            yy = [ nodelayers[i][mydiff:] ]
        else:
            yy.append(nodelayers[i])
        i=i+1
    qwe.append( yy )
    codeoffunctions_list = []
    #gcode = "".join(("@njit\n","def cycle( ", ",".join(valuename_ordered), "):\n"))
    gcode = "".join(("def cycle( ", ",".join(valuename_ordered), "):\n"))
    gcodelist = []
    for i in range(len(qwe)):
        usedvalues = set()
        for layer in nodelayers:
            for node in layer:
                usedvalues = usedvalues.union( set(usedvaluesdict[node]) )
        usedvalues = list(usedvalues)
        usedvalues.sort( key=valuename_ordered.index )
        #newcode =  _combinecode( valuename_ordered, nodetocode_dict, \
        #                                            nodelayers,i )
        newcode =  _combinecode( usedvalues, nodetocode_dict, \
                                                    nodelayers, i )
        codeoffunctions_list.append( "@njit\n" + newcode )
        gcodelist.append( "\t" + ",".join(usedvalues) +"= cycle%d("%(i) \
                                + ",".join(usedvalues) +")\n")
    gcode = "".join( (gcode, *gcodelist, "\treturn "+",".join(valuename_ordered)))
    gcode = "".join( (gcode, "\nreturn_array[%d] = cycle"%(len(qwe)+1)))

    returncode = "".join((
                    "".join(codeoffunctions_list),
                    gcode
                ))
    return returncode, len(qwe)+1
    return "".join(codeoffunctions_list), len(qwe)+1


def _combinecode( valuename_ordered, nodetocode_dict, nodelayers,returnindex=0):
    mycode = "def cycle%d( "%(returnindex)
    for valuename in valuename_ordered:
        mycode = mycode + valuename + ", "
    mycode = mycode + "):\n"

    for layer in nodelayers:
        for node in layer:
            try:
                lines = "\n\t".join(nodetocode_dict[ node ])
                #lines = "\n\t".join( tmpnodes()[ node ][ "code" ])
            except KeyError as err:
                err.args = ( *err.args, "most likely an edge was made "\
                                + "between not compatible nodes, problem "\
                                "timing node is: %s" %( str(node) ))
                raise err
            mycode = "".join((mycode, "\t", lines, "\n"))

    mycode = mycode + "\treturn " + ",".join(valuename_ordered) + ","
    mycode = mycode + "\nreturn_array[%d] = cycle%d\n" %(returnindex, returnindex )
    return mycode

def _replace_edgecodesnippet_placeholders( codesnippet, \
                                            dataname_list, innodename, \
                                            outnodename, innode, outnode ):
    """
    translates, the codesnippets given by the functions saved in the edgelibrary
    into usable code by the cyclefunction. this function only uses a array
    with name values
    :todo: replace innode and outnode with source and target
    """
    codenodes = codesnippet.nodes(data=True)
    for tmpnode in codenodes:
        tmpdata = tmpnode[1]
        usedvalues = set()
        for i in range( len(tmpdata["code"]) ):
            values=[]
            valuenames = []
            for x in tmpdata["values"][i]:
                valueidentifier = dict_valueidentifier_translator[ x[0] ]
                if valueidentifier == "innode":
                    values.append( innodename + x[1] )
                    valuenames.append( tovaluename( innode, x[1]))
                elif valueidentifier == "outnode":
                    values.append( outnodename + x[1] )
                    valuenames.append( tovaluename( outnode, x[1]))
                else:
                    raise Exception()
            try:
                tmpdata["code"][i] = tmpdata["code"][i] % tuple(valuenames)
            except TypeError as err:
                err.args = ( *err.args, ("between nodes %s and %s a function"\
                            +"line %s is formatted with values %s") \
                            %( innodename, outnodename, tmpdata["code"][i], \
                            values ))
                raise err
            usedvalues = usedvalues.union( valuenames )
        codesnippet.nodes[tmpnode[0]]["usedvalues"] = usedvalues

def _replace_nodecodesnippet_placeholders( codesnippet, \
                                    dataname_list, nodename, node):
    codenodes = codesnippet.nodes(data=True)
    for tmpnode in codenodes:
        tmpdata = tmpnode[1]
        usedvalues = set()
        for i in range( len(tmpdata["code"]) ):
            valuenames = tuple([tovaluename( node, datakey ) \
                        for datakey in tmpdata["values"][i] ])
            tmpdata["code"][i] = tmpdata["code"][i] % valuenames
            usedvalues = usedvalues.union( valuenames )
        codesnippet.nodes[tmpnode[0]]["usedvalues"] = usedvalues
            #values = [ nodename + single \
            #                for single in tmpdata["values"][i]]
            #try:
            #    valueplaces = tuple([ dataname_list.index(x) for x in values ])
            #except ValueError as err:
            #    raise type(err)(*err.args, "make sure value in "\
            #                            +"codenode is a list with tuples, "\
            #                            +"e.g. [(1,)] not [(1)]" )
            #tmpdata["code"][i] = tmpdata["code"][i] % valueplaces

def tovaluename( node, nodetype_datakey ):
    """
    :todo: replace str(nodetype_datakey) to nodetype_datakey
    """
    return "value" + str( hashlib.sha1(\
            (str(node) + nodetype_datakey).encode('utf-8') ).hexdigest() )
