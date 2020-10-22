from graphtoarithmetic import graphtoarithmetic as mygraph
import networkx as net

graphcontainer_cycles = 2

class firstvertice( mygraph.graphvertice ):
    init_values = tuple([ 0.0, 0.0 ])

    def __init__( self, savename, container ):
        super().__init__( savename, container )
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
        # number of returnvalues has to match the number of cycles of the
        # graphcontainer( default=2 ); see graphcontainer_cycles
        return [cmd_first], [cmd_second]

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


if __name__=="__main__":
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

    mythingis = mygraph.graphcontainer( graph, creation_library,\
                                    cycles = graphcontainer_cycles )

    print( mythingis.savespace.reshape((3,6)) )

    from datetime import datetime
    starttime = datetime.now()
    for i in range(2):
        mythingis.cycle()
    endtime = datetime.now()
    print( "needed time: %s" %(repr(endtime - starttime)) )
    print( mythingis.savespace.reshape((3,6)) )

    exit()

