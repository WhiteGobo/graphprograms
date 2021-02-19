import graphviz as gv
import networkx as netx
import pydot
import io
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
import copy

def myvis( myflowgraph ):
    flowgraph_list = split_graph_to_subgraphs( myflowgraph )

    plt.figure()
    graph_axes = plt.axes([ 0.05, 0.05, 0.4, 0.9 ])
    radio_axes = plt.axes([0.45, 0.05, 0.1, 0.9])
    datagraph_axes = plt.axes([0.6, 0.55, 0.3, 0.4])
    datagraph_selector_axes = plt.axes([0.9, 0.05, 0.1, 0.9])
    asd = myshower( flowgraph_list, graph_axes, radio_axes, datagraph_axes, \
                                                    datagraph_selector_axes )
    #plt.imshow( mypic )
    plt.show()

class myshower():
    def __init__( self, subflowgraph_list, draw_axes, radio_axes, \
                                    datagraph_axes, datagraph_selector_axes ):
        subflowgraph_list = list( subflowgraph_list )
        radiolabellist = []
        flowgraph_pic_dict = {}
        datastate_superdict = {}
        all_pictures = [ organise_subflowgraphs( singlegraph ) \
                            for singlegraph in subflowgraph_list ]
        picdict = { repr(i): all_pictures[i] for i in range(len(all_pictures))}

        datastate_switch_functions = self.create_switchdatastate_dict( picdict,\
                                                datagraph_axes, \
                                                datagraph_selector_axes )
        self.switch_flowgraphbuttons \
                = self.create_switchflowgraph( radio_axes, draw_axes, picdict,\
                                                    datagraph_selector_axes, \
                                                    datastate_switch_functions )

    def create_switchdatastate_dict( self, picdict, datastate_axes, \
                                                datastate_selector_axes ):
        datastate_switch_functions = {}
        for key, pics in picdict.items():
            datastate_switch_functions[ key ] \
                    = create_single_datastate_switch_function( pics, key, \
                                                            datastate_axes )
        return datastate_switch_functions


    def create_switchflowgraph( self, radio_axes, draw_axes, picdict, \
                                    datastate_selector_axes, datastate_foo ):
        labels = list( picdict.keys() )

        switch_flowgraphbuttons = RadioButtons( radio_axes, picdict.keys() )
        startlabel = labels[0]

        datastate_keys = { radiokey: list(picdict[ radiokey ][ 1 ].keys()) \
                            for radiokey in picdict }
        def myfoo( radiolabel ):
            draw_axes.clear()
            draw_axes.imshow( picdict[ radiolabel ][0] )

            datastate_selector_axes.clear()
            tmpswitch = RadioButtons( datastate_selector_axes, 
                                            datastate_keys[ radiolabel ] )
            tmpswitch.on_clicked( datastate_foo[ radiolabel ] )
            datastate_foo[radiolabel]( datastate_keys[ radiolabel ][0] )
            self.switch_datastates = tmpswitch #need to keep a reference

            plt.draw()
        switch_flowgraphbuttons.on_clicked( myfoo )

        #draw_axes.imshow( picdict[ startlabel ][0] )
        myfoo( startlabel )

        return switch_flowgraphbuttons

    def _set_radiobutton_for_datastates( self, value ):
        self._radiobutton_datastates = value
    switch_datastates = property( fset = _set_radiobutton_for_datastates )


def create_single_datastate_switch_function( pics, key, datastate_axes ):
    datastate_pics_dict = pics[1]
    def myfoo( radiolabel ):
        print( key )
        datastate_axes.clear()
        try:
            datastate_axes.imshow( datastate_pics_dict[radiolabel] )
        except Exception as err:
            err.args = (*err.args, datastate_pics_dict.keys() )
            raise err
        plt.draw()
    return myfoo



def organise_subflowgraphs( single_subgraph ):
    datastate_dict = {}
    graph_picture = None

    intgraph = netx.convert_node_labels_to_integers( single_subgraph, \
            label_attribute = "datastate")

    int_to_datastate = netx.get_node_attributes( intgraph, "datastate" )
    for i in intgraph.nodes():
        datastate_dict[repr(i)] = datastate_to_picture( int_to_datastate[i] )

    graph_picture = subflowgraph_to_picture( single_subgraph )

    return graph_picture, datastate_dict


def datastate_to_picture( mydatastate ):
    nodes, edges = mydatastate.nodes, mydatastate.edges
    tmpG = netx.MultiDiGraph()
    tmpG.add_nodes_from( nodes )
    for edge in edges:
        tmpG.add_edge( edge[0], edge[1], edgename=edge[-1] )
    m = netx.drawing.nx_pydot.to_pydot( tmpG )
    mybytes = m.create_png()
    filelikebytes = io.BytesIO( mybytes )
    mypic = mpimg.imread( filelikebytes )
    return mypic


def subflowgraph_to_picture( mysubflowgraph ):
    #mapping = lambda x: repr( x )
    #netx.relabel_nodes( copyofflowgraph, mapping, copy = False )
    copyofflowgraph = netx.convert_node_labels_to_integers( mysubflowgraph )
    m = netx.drawing.nx_pydot.to_pydot( copyofflowgraph )
    mybytes = m.create_png()
    filelikebytes = io.BytesIO( mybytes )
    mypic = mpimg.imread( filelikebytes )
    return mypic


def split_graph_to_subgraphs( supergraph ):
    multigraph = netx.MultiDiGraph( supergraph )
    asd = netx.Graph( supergraph )
    subgraph_sets = netx.connected_components( asd )
    return [ multigraph.subgraph( myset ) for myset in subgraph_sets ]


