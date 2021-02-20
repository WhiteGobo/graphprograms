#import graphviz as gv
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
    #graph_axes = plt.axes([ 0.0, 0.55, 0.9, 0.4 ])
    #radio_axes = plt.axes([0.9, 0.55, 0.08, 0.4])
    #datagraph_axes = plt.axes([0.0, 0.05, 0.9, 0.4])
    #datagraph_selector_axes = plt.axes([0.9, 0.05, 0.08, 0.4])
    graph_axes = plt.axes([ 0.0, 0.05, 0.9, 0.9 ])
    radio_axes = plt.axes([0.9, 0.05, 0.08, 0.9])
    plt.figure()
    datagraph_axes = plt.axes([0.0, 0.05, 0.9, 0.9])
    datagraph_selector_axes = plt.axes([0.9, 0.05, 0.08, 0.9])
    plt.figure()
    legendaxis = plt.axes()

    asd = myshower( flowgraph_list, graph_axes, radio_axes, datagraph_axes, \
                                            datagraph_selector_axes, legendaxis)
    #plt.imshow( mypic )

    print("\nnode in datastate to nodetype:\n")
    for i in myflowgraph.node_to_datatype.items():
        print(i)

    plt.show()

class myshower():
    def __init__( self, subflowgraph_list, draw_axes, radio_axes, \
                                    datagraph_axes, datagraph_selector_axes, \
                                    legendaxis ):
        subflowgraph_list = list( subflowgraph_list )
        radiolabellist = []
        flowgraph_pic_dict = {}
        datastate_superdict = {}
        factoryleaf_to_color = create_colordict( subflowgraph_list )
        create_legend( legendaxis, factoryleaf_to_color )
        all_pictures = [ organise_subflowgraphs( singlegraph, \
                                                    factoryleaf_to_color ) \
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
        datastate_axes.clear()
        try:
            datastate_axes.imshow( datastate_pics_dict[radiolabel] )
        except Exception as err:
            err.args = (*err.args, datastate_pics_dict.keys() )
            raise err
        plt.draw()
    return myfoo



def organise_subflowgraphs( single_subgraph, factoryleaf_to_color ):
    datastate_dict = {}
    graph_picture = None

    intgraph = netx.convert_node_labels_to_integers( single_subgraph, \
            label_attribute = "datastate")

    int_to_datastate = netx.get_node_attributes( intgraph, "datastate" )
    for i in intgraph.nodes():
        datastate_dict[repr(i)] = datastate_to_picture( int_to_datastate[i] )

    graph_picture = subflowgraph_to_picture( single_subgraph, \
                                                factoryleaf_to_color )

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

def _set_edgecolor( netxgraph, factory_leaf_to_color ):
    input_data = netx.get_edge_attributes( netxgraph, "edgetype" )
    input_data = { key: value.factoryleaf for key, value in input_data.items()}
    color_dict = { key: factory_leaf_to_color[ value ] \
                    for key, value in input_data.items() }
    netx.set_edge_attributes(netxgraph, color_dict, "color" )

def subflowgraph_to_picture( mysubflowgraph, factoryleaf_to_color ):
    #mapping = lambda x: repr( x )
    #netx.relabel_nodes( copyofflowgraph, mapping, copy = False )
    copyofflowgraph = netx.convert_node_labels_to_integers( mysubflowgraph )
    _set_edgecolor( copyofflowgraph, factoryleaf_to_color )
    m = netx.drawing.nx_pydot.to_pydot( copyofflowgraph )
    mybytes = m.create_png()
    filelikebytes = io.BytesIO( mybytes )
    mypic = mpimg.imread( filelikebytes )
    return mypic


def create_legend( legendaxis, factleaf_to_color ):
    colorgraph = netx.Graph()
    lastnode = None
    for factleaf, color in factleaf_to_color.items():
        if factleaf.name:
            nodename = factleaf.name
        else:
            nodename = repr( factleaf )
        colorgraph.add_node( nodename, color=color )
        if lastnode:
            colorgraph.add_edge( nodename, lastnode )
        lastnode=nodename

    m = netx.drawing.nx_pydot.to_pydot( colorgraph )
    mybytes = m.create_png()
    filelikebytes = io.BytesIO( mybytes )
    mypic = mpimg.imread( filelikebytes )
    legendaxis.imshow( mypic )



def split_graph_to_subgraphs( supergraph ):
    multigraph = netx.MultiDiGraph( supergraph )
    asd = netx.Graph( supergraph )
    subgraph_sets = netx.connected_components( asd )
    return [ multigraph.subgraph( myset ) for myset in subgraph_sets ]

def create_colordict( subflowgraph_list ):
    all_factoryleafs = set()
    for singlegraph in subflowgraph_list:
        input_data = netx.get_edge_attributes( singlegraph, "edgetype" )
        all_factoryleafs = all_factoryleafs.union( value.factoryleaf \
                                            for value in input_data.values())
    #factoryleaf_to_color ={ factleaf: "blue" for factleaf in all_factoryleafs }
    colorlist = ["blue1", "brown", "burlywood", "cadetblue", "chartreuse", "chocolate", "coral", "cornflowerblue", "cornsilk" ]
    coloriter = iter( colorlist )
    factoryleaf_to_color = { factleaf: coloriter.__next__() \
                            for factleaf in all_factoryleafs }
    return factoryleaf_to_color

