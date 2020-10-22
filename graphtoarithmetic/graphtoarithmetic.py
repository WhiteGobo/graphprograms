import numpy as np
import numba
from numba import jit
MYDTYPE = np.float64

class EdgeTypeError( Exception ):
    pass

class graphcontainer():
    savename = "array" #must correspond to cycle_function,see __init_cycle
    def __init__( self, graph, creation_library, cycles = 2 ):
        """
        :type creation_library: dictionary
        :variable creation_library: library maps identifer of graph to a
                        class, use identifier "default" for default class
        """
        self.cycles = cycles
        self.cycle_functions = list( range( self.cycles ) )
        print( self.cycle_functions )
        self.nodedict, self.savespace_list, self.savespace = None, None, None
        self.creation_library = creation_library
        self.default_verticeclass = \
                    self.creation_library.setdefault( "default", None )
        self.__init_savespace( graph )
        self.__init_cycle_one( graph )

    def __init_cycle_one( self, graph ):
        nodes = self.nodedict

        return_array = [None]
        cmds = list( range(self.cycles) )
        myglobals = {"return_array":return_array, "np":np}
        for edge in graph.edges():
            myglobals.update( nodes[ edge[0] ].extraglobals )
        #create functions
        for i in range( self.cycles ):
            cmds[i] = "def cycle%d( %s ):\n" % ( i, self.savename )
        for edge in graph.edges():
            superlist_cmds = nodes[ edge[0] ].edgeto( nodes[ edge[1] ] )
            for i in range( self.cycles ):
                for tmpcmd in superlist_cmds[i]:
                    cmds[i] = cmds[i] +"\t" + tmpcmd + "\n"
        for i in range( self.cycles ):
            cmds[i] = cmds[i] \
                    + "\n\treturn %s\n" % (self.savename) \
                    + "\nreturn_array[0] = cycle%d" %( i )
            # !ersetze graphcontainer
            cmd_code = compile( cmds[i], "graphcontainer", "exec" )
            exec( cmd_code, myglobals )
            self.cycle_functions[i] = numba.jit( return_array[0] )

    def __init_savespace( self, graph ):
        self.savespace_list = []
        self.nodedict = {}
        for tmpnode in graph.nodes():
            vertice_generator = self.creation_library.setdefault( tmpnode, \
                                self.default_verticeclass )
            try:
                tmpvertice = vertice_generator( self.savename, self )
            except TypeError as err:
                errmsg = "missing generator for vertice %s," %(repr(tmpnode))\
                        + "Try 'default' keyword in creation_library"
                raise KeyError(errmsg) from err

            init_values = tmpvertice.init_values
            indexlist = []
            for value in init_values:
                #mind the ordering
                current_i = len( self.savespace_list )
                self.savespace_list.append( value )
                #
                indexlist.append( current_i )
            tmpvertice.value_index = tuple( indexlist )
            self.nodedict.update({ tmpnode: tmpvertice })
        self.savespace = np.array( self.savespace_list, dtype=MYDTYPE )

    def cycle( self ):
        for i in range( self.cycles ):
            self.savespace = self.cycle_functions[i]( self.savespace )

class graphvertice():
    init_values = tuple()

    def __init__( self, savename, graphcontainer, extraglobals = {} ):
        self.value_index = None
        self.graphcontainer = graphcontainer
        self.edge_library = {}
        self.arrayname = savename
        self.extraglobals = extraglobals

    def edgeto( self, other ):
        try:
            return self.edge_library[ type(other) ]( other )
        except KeyError as err:
            errmsg = "verticetype %s cant edgeto verticetype %s" \
                    % ( type(self), type(other) )
            raise EdgeTypeError(errmsg) from err

    def getvalue( self, index ):
        return self.graphcontainer.savespace[ self.value_index[index] ]
    def setvalue( self, index, value ):
        self.graphcontainer.savespace[ self.value_index[index] ] = value



