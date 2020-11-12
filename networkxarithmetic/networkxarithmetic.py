import networkx as netx
import numpy as _np
MYDTYPE  = _np.float64

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
        self.calc_dict = {}
        self.edge_dict = {}
        self.calc_graph = None
        self.time_graph = None
        self.extra_globals = None

    def cycle( self ):
        self.values = self.cyclefunction( self.values )

    def update_calclibrary( self, calc_dict ):
        """
        calc_dict must contain methods to generate codesnippets and reserve
        dataspace
        :type calc_dict: dictionary
        """
        self.calc_dict.update( calc_dict )

    def update_edgelibrary( self, edge_dict ):
        """
        edge_dict assign tuple of (outnodetype, innodetype, edgename) a method
        to create the code
        foo return a codegraph
        """
        self.edge_dict.update( edge_dict )

    def createcode_with_graph( self, graph ):
        """
        the calc_dict must contain methods for all node in graph
        :type graph: networkx.MultiDiGraph
        """
        self.codegraph = netx.MultiDiGraph( graph )
        self._generate_datacontainer()
        self._generate_code()

    def _generate_datacontainer( self ):
        """
        :raises NoStartvalueGiven_Error: raise exception if a default value is 
                            set to None and no startvalue is given by the graph
        """
        self.extra_globals = {} #create new
        dataname_list = []
        startvalue_list = []
        codegraph = netx.DiGraph()
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
                dataname = str(tmpnode) + nodetype_datakey
                # use as starting value value given in graph
                # and else the default value given via nodetypedata_dict
                startvalue = nodes[tmpnode].setdefault( nodetype_datakey, \
                                            nodetypedata_dict[nodetype_datakey])
                if startvalue == None:
                    raise NoStartvalueGiven_Error(\
                            "node %s with " %( str(tmpnode) ) \
                            +"nodetype %s needs a "%(tmpdata["calctype"])\
                            +"starting value for %s" %(str(nodetype_datakey))  )
                dataname_list.append( dataname )
                startvalue_list.append( startvalue )

            # replace codeplaceholders with datamapping
            _replace_nodecodesnippet_placeholders( codesnippet, dataname_list,\
                                                   str(tmpnode) )
            # rename nodes
            tmpmapping = { node:str(tmpnode)+str(node) \
                                     for node in codesnippet.nodes() }
            codegraph.update( netx.relabel_nodes(codesnippet, tmpmapping) )

        # generate edges
        for edgeinfo in self.codegraph.edges( data = True, keys = True ):
            tmpdata = edgeinfo[3]
            edgekey = edgeinfo[2]
            tmpnodeout = edgeinfo[0]
            tmpnodein = edgeinfo[1]
            outtype = self.codegraph.nodes()[ tmpnodeout ][ "calctype" ]
            intype = self.codegraph.nodes()[ tmpnodein ][ "calctype" ]

            # create code template, not usable until valuenames are replaced
            codenode, after_nodeout, after_nodein, \
                    before_nodeout, before_nodein \
                    = self.edge_dict[ (outtype, intype,tmpdata["edgetype"]) ]()
            try:
                _replace_edgecodesnippet_placeholders( codenode, \
                                dataname_list, str(tmpnodein), str(tmpnodeout) )
            except ValueError as err:
                err.args = ( *err.args, "node name w type are innode: " \
                                + "%s w %s; " %( tmpnodein, intype ) \
                                + "outnode: %s w %s" %( tmpnodeout, outtype, )
                            )
                raise err
            # rename identifier for codesnippet in graph
            tmpmapping = { tmpdata["edgetype"]:
                    str(tmpnodeout)+str(tmpnodein) \
                    + str(edgekey) + tmpdata["edgetype"] }
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
                            

        # after this there should be th codegraph for _generate_code
        self.dataname_list = dataname_list
        self.startvalue_list = startvalue_list
        self.values = _np.array( startvalue_list, dtype = MYDTYPE )
        self.codegraph = codegraph

                
                            
    def _generate_code( self ):
        nodelayers=[]
        tmpsubgraph = netx.DiGraph( self.codegraph )
        tmplastlength = len(tmpsubgraph)
        while len(tmpsubgraph) > 0:
            withoutneighbor = [x for x in tmpsubgraph.nodes() \
                                if len( list(tmpsubgraph.predecessors(x))) ==0]
            nodelayers.append( withoutneighbor )
            tmpsubgraph.remove_nodes_from( withoutneighbor )
            if tmplastlength == len(tmpsubgraph):
                raise CycleToTree_Error("couldnt create valid functionorder")
            tmplastlength = len(tmpsubgraph)

        mycode = "def cycle( value ):\n"
        for layer in nodelayers:
            for node in layer:
                try:
                    for line in self.codegraph.nodes()[ node ]["code"]:
                        mycode = mycode +"\t" +line + "\n"
                except KeyError as err:
                    err.args = ( *err.args, "most likely an edge was made "\
                                    + "between not compatible nodes, problem "\
                                    "timing node is: %s" %( str(node) ))
                    raise err
        mycode = mycode + "\treturn value\n"
        mycode = mycode + "return_array[0] = cycle\n"

        return_array = [None]
        myglobals = {"return_array":return_array, "np":_np}
        myglobals.update( self.extra_globals )
        cmd_code = compile( mycode, "networkxarithmetic", "exec" )
        exec( cmd_code, myglobals )
        self.cyclefunction = return_array[0]
        #self.cyclefunction = numba.njit( return_array[0] )

dict_valueidentifier_translator = {
        "in":"innode", "target":"innode", "outedge":"innode",
        "out":"outnode", "source":"outnode", "inedge":"outnode",
        }

def _replace_edgecodesnippet_placeholders( codesnippet, \
                                    dataname_list, innodename, outnodename ):
    """
    translates, the codesnippets given by the functions saved in the edgelibrary
    into usable code by the cyclefunction. this function only uses a array
    with name values
    :todo: replace innode and outnode with source and target
    """
    codenodes = codesnippet.nodes(data=True)
    for tmpnode in codenodes:
        tmpdata = tmpnode[1]
        for i in range( len(tmpdata["code"]) ):
            values=[]
            for x in tmpdata["values"][i]:
                valueidentifier = dict_valueidentifier_translator[ x[0] ]
                if valueidentifier == "innode":
                    values.append( innodename + x[1] )
                elif valueidentifier == "outnode":
                    values.append( outnodename + x[1] )
                else:
                    raise Exception()
            try:
                valueplaces = tuple([ dataname_list.index(x) for x in values ])
            except ValueError as err:
                err.args = (*err.args, "make sure value in "\
                                        +"codenode is a list with tuples, "\
                                        +"e.g. [(1,)] not [(1)]",)
                raise err
            tmpdata["code"][i] = tmpdata["code"][i] % valueplaces

def _replace_nodecodesnippet_placeholders( codesnippet, \
                                    dataname_list, nodename):
    codenodes = codesnippet.nodes(data=True)
    for tmpnode in codenodes:
        tmpdata = tmpnode[1]
        for i in range( len(tmpdata["code"]) ):
            values = [ nodename + single \
                            for single in tmpdata["values"][i]]
            try:
                valueplaces = tuple([ dataname_list.index(x) for x in values ])
            except ValueError as err:
                raise type(err)(*err.args, "make sure value in "\
                                        +"codenode is a list with tuples, "\
                                        +"e.g. [(1,)] not [(1)]" )
            tmpdata["code"][i] = tmpdata["code"][i] % valueplaces
