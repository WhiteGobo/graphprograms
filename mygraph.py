import networkx as net
import numpy as np
import numba
from numba import njit
MYDTYPE = np.float64

class EdgeTypeError( Exception ):
    pass

class graphcontainer():
    savename = "array" #must correspond to cycle_function,see __init_cycle
    def __init__( self, graph, creation_library ):
        """
        :type creation_library: dictionary
        :variable creation_library: library maps identifer of graph to a
                        class, use identifier "default" for default class
        """
        self.creation_library = creation_library
        self.default_verticeclass = \
                    self.creation_library.setdefault( "default", None )
        self.__init_savespace( graph )
        self.__init_cycle_one( graph )

    def __init_cycle_one( self, graph ):
        nodes = self.nodedict

        return_array = [None]
        cmd1 = "def cycle1( %s ):\n" % ( self.savename )
        cmd2 = "def cycle2( %s ):\n" % ( self.savename )
        for edge in graph.edges():
            tmpcmd1, tmpcmd2 = nodes[ edge[0] ].edgeto( nodes[ edge[1] ] )
            cmd1 = cmd1 +"\t" + tmpcmd1 + "\n"
            cmd2 = cmd2 +"\t" + tmpcmd2 + "\n"
        cmd1 = cmd1 + "\n\treturn %s\n" % (self.savename)
        cmd1 = cmd1 + "\nreturn_array[0] = cycle1"
        cmd2 = cmd2 + "\n\treturn %s\n" % (self.savename)
        cmd2 = cmd2 + "\nreturn_array[0] = cycle2"
        cmd_code = compile( cmd1, "graphcontainer", "exec" )
        exec( cmd_code, {"return_array":return_array, "np":np} )
        cycle1_function = return_array[0]
        cmd_code = compile( cmd2, "graphcontainer", "exec" )
        exec( cmd_code, {"return_array":return_array, "np":np} )
        cycle2_function = return_array[0]

        self.cycle1_function = numba.njit( cycle1_function )
        self.cycle2_function = numba.njit( cycle2_function )

    def __init_savespace( self, graph ):
        self.savespace_list = []
        self.nodedict = {}
        for tmpnode in graph.nodes():
            vertice_generator = self.creation_library.setdefault( tmpnode, \
                                self.default_verticeclass)
            try:
                tmpvertice = vertice_generator( self.savename )
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
        self.savespace = self.cycle1_function( self.savespace )
        self.savespace = self.cycle2_function( self.savespace )

class graphvertice():
    init_values = tuple()

    def __init__( self, savename ):
        self.value_index = None
        self.edge_library = {}
        self.arrayname = savename

    def edgeto( self, other ):
        try:
            return self.edge_library[ type(other) ]( other )
        except KeyError as err:
            errmsg = "verticetype %s cant edgeto verticetype %s" \
                    % ( type(self), type(other) )
            raise EdgeTypeError(errmsg) from err



class firstvertice( graphvertice ):
    init_values = tuple([ 0.0, 0.0 ])

    def __init__( self, savename ):
        super().__init__(savename)
        self.edge_library.update({ type(self):self.edgeto_self })

    def edgeto_self( self, other ):
        if other == self:
            selfvalue = "%s[%d]" % (self.arrayname, self.value_index[1])
            othervalue = "%s[%d]" % (self.arrayname, other.value_index[0])
            cmd_first = "%s = %s + (0.8*%s)" \
                    % ( selfvalue, selfvalue, othervalue )
            cmd_second = "%s, %s = %s, 0" % ( othervalue, selfvalue, selfvalue )
        else:
            selfvalue = "%s[%d]" % (self.arrayname, self.value_index[1])
            othervalue = "%s[%d]" % (self.arrayname, other.value_index[0])
            cmd_first = "%s = %s -(0.2*%s) + .2" \
                    % ( selfvalue, selfvalue, othervalue )
            cmd_second = "pass"
        return cmd_first, cmd_second


if __name__=="__main__":
    def create_grid_graph( graph_dict ):
        """
        :type graph_dict: dictionary with vertices as keys and edges as set
        """
        graph = net.DiGraph()
        for vertice in graph_dict.keys():
            graph.add_node( vertice )
        for vertice in graph_dict.keys():
            for target_vertice in  graph_dict[ vertice ]:
                graph.add_edge( vertice, target_vertice )

        return graph

    grid = {
            (0,0):{(0,0), (1,0), (0,1)},
            (1,0):{(1,0), (0,0), (2,0), (1,1)},
            (2,0):{(2,0), (1,0), (2,1)},
            (0,1):{(0,1), (1,1), (0,0), (0,2)},
            (1,1):{(1,1), (0,1), (2,1), (1,0), (1,2)},
            (2,1):{(2,1), (1,1), (2,0), (2,2)},
            (0,2):{(0,2), (1,2), (0,1)},
            (1,2):{(1,2), (0,2), (2,2), (1,1)},
            (2,2):{(2,2), (1,2), (2,1)}
            }
    creation_library = {
            "default":firstvertice,
            (0,0):firstvertice,
            (1,0):firstvertice,
            (2,0):firstvertice,
            (0,1):firstvertice,
            (1,1):firstvertice,
            }
    graph = create_grid_graph( grid )

    mythingis = graphcontainer( graph, creation_library )

    print( mythingis.savespace.reshape((3,6)) )

    from datetime import datetime
    starttime = datetime.now()
    for i in range(2):
        mythingis.cycle()
    endtime = datetime.now()
    print( "needed time: %s" %(repr(endtime - starttime)) )
    print( mythingis.savespace.reshape((3,6)) )

    exit()

