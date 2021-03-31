#import graphviz as gv
import networkx as netx
import pydot
import io
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
from collections import Counter
import copy
import subprocess
import time
import os.path


import tempfile

#colorlist = ["blue1", "brown", "burlywood", "cadetblue", "chartreuse", "chocolate", "coral", "cornflowerblue", "cornsilk" ]
colorlist = ["blueviolet", "brown", "cadetblue", "chartreuse", \
        "chocolate", "coral", "cornflowerblue", "cornsilk", "crimson", \
        "cyan", "darkblue", "darkcyan", "darkgoldenrod", "darkgray", \
        "darkgreen", "darkgrey", "darkkhaki", "darkmagenta", "burlywood", \
        "darkolivegreen", "darkorange", "darkorchid", "darkred", \
        "darksalmon", "darkseagreen", "darkslateblue", "darkslategray", \
        "darkslategrey", "darkturquoise", "darkviolet", "deeppink", \
        "deepskyblue", "dimgray", "dimgrey", "dodgerblue", "firebrick", \
        "floralwhite", "forestgreen", "fuchsia", "gainsboro", "ghostwhite", \
        "gold", "goldenrod", "gray", "grey", "green", "greenyellow", \
        "honeydew", "hotpink", "indianred", "indigo", "ivory", "khaki", \
        "lavender", "lavenderblush", "lawngreen", "lemonchiffon", "lightblue",\
        "lightcoral", "lightcyan", "lightgoldenrodyellow", "lightgray", \
        "lightgreen", "lightgrey", "lightpink", "lightsalmon", \
        "lightseagreen", "lightskyblue"]


def myvis( myflowgraph ):
    flowgraph_list = split_graph_to_subgraphs( myflowgraph )
    #flowgraph_list = [ myflowgraph, ]

    plt.figure()
    graph_axes = plt.axes([ 0.0, 0.05, 0.9, 0.9 ])
    radio_axes = plt.axes([0.9, 0.05, 0.08, 0.9])
    #plt.figure()
    #legendaxis = plt.axes()

    asd = myshower( flowgraph_list, graph_axes, radio_axes )
    #plt.imshow( mypic )
    return

    print("\nnode in datastate to nodetype:\n")
    for i in myflowgraph.node_to_datatype.items():
        print(i)
    plt.show()


class myshower():
    def __init__( self, subflowgraph_list, draw_axes, radio_axes ):
        subflowgraph_list = list( subflowgraph_list )
        radiolabellist = []
        flowgraph_pic_dict = {}
        #datastate_superdict = {}
        factoryleaf_to_color, factoryleaf_to_label \
                = create_stylesheets( subflowgraph_list )

        myorganise = lambda singlegraph, filepath: organise_subflowgraphs(\
                                                singlegraph, \
                                                factoryleaf_to_color, \
                                                factoryleaf_to_label,\
                                                filepath,\
                                                filetype="svg")

    
        with tempfile.TemporaryDirectory() as tmpdirname:
            topicname = lambda i: "/".join((tmpdirname, \
                                            "flowgraph%2i.svg"%(i)))
            all_pictures = [ myorganise( singlegraph, topicname( i ) ) \
                            for i, singlegraph \
                            in enumerate(subflowgraph_list) ]
            try:
                for process in all_pictures:
                    process.wait()
            except AttributeError:
                input("Press any key to end program. "\
                        "All temporary data will be lost")
        return


        all_pictures = [ myorganise( singlegraph ) for singlegraph in subflowgraph_list ]
        picdict = { repr(i): all_pictures[i] for i in range(len(all_pictures))}

        self.switch_flowgraphbuttons \
                = self.create_switchflowgraph( radio_axes, draw_axes, picdict)


    def create_switchflowgraph( self, radio_axes, draw_axes, picdict ):#, \
                                                #datastate_selector_axes ):
        labels = list( picdict.keys() )

        switch_flowgraphbuttons = RadioButtons( radio_axes, picdict.keys() )
        startlabel = labels[0]

        def myfoo( radiolabel ):
            draw_axes.clear()
            draw_axes.imshow( picdict[ radiolabel ] )#[0] )

            plt.sca( draw_axes )
            plt.draw()
        switch_flowgraphbuttons.on_clicked( myfoo )

        myfoo( startlabel )

        return switch_flowgraphbuttons

    def _set_radiobutton_for_datastates( self, value ):
        self._radiobutton_datastates = value
    switch_datastates = property( fset = _set_radiobutton_for_datastates )


def compress_flowgraph( single_subgraph ):
    old_to_compressed = {snod: snod.weisfeil_hash() \
                            for snod in single_subgraph.nodes()}
    anticompress = { value:key for key, value in old_to_compressed.items() }
    otoc = old_to_compressed
    edges = set( (otoc[src], otoc[trg], data["edgetype"].factoryleaf) \
                for src, trg, k, data \
                in single_subgraph.edges( data=True, keys=True ) )
    single_subgraph = netx.MultiDiGraph()
    single_subgraph.add_nodes_from( anticompress.values() )
    for a, b, c in edges:
        single_subgraph.add_edge( anticompress[a], anticompress[b], \
                                    edgetype = c)
    return single_subgraph


def organise_subflowgraphs( single_subgraph, factoryleaf_to_color, \
                            factoryleaf_to_label, filepath, \
                            filetype="svg" ):
    single_subgraph = compress_flowgraph( single_subgraph )
    intgraph = netx.convert_node_labels_to_integers( single_subgraph, \
                                                    label_attribute = "datastate")
    for node, data in intgraph.nodes( data=True ):
        datastategraph = datastate_to_graph( data["datastate"] )
        intgraph.nodes[ node ]["datastate graph"] = datastategraph
        for dnode in datastategraph.nodes():
            datatype = datastategraph.nodes[ dnode ]["datatype"]
            datastategraph.nodes[ dnode ]["label"] = datatype.__name__
        for dedge_all in datastategraph.edges( keys=True, data=True ):
            dedge, data = dedge_all[:-1], dedge_all[-1]
            edgename = data["edgename"]
            datastategraph.edges[ dedge ]["label"] = repr(edgename)

    for edge_all in intgraph.edges( data=True, keys=True ):
        edge, data = edge_all[:-1], edge_all[-1]
        intgraph.edges[edge]["color"] = factoryleaf_to_color[ data["edgetype"] ]
        intgraph.edges[edge]["label"] = factoryleaf_to_label[ data["edgetype"] ]

    
    graph_picture = None

    #with tempfile.TemporaryDirectory() as tmpdirname:
    for i in intgraph.nodes():
        pngfilename = "-".join(( filepath, f"my{i}.svg" ))
        #pngfilename = "-".join(( filepath, f"{i}.png" ))
        datastategraph_to_picture( intgraph.nodes[i]["datastate graph"], \
                                    pngfilename, filetype="svg" )
        intgraph.nodes[i]["image"] = pngfilename
        intgraph.nodes[i]["label"] = ""

    graph_picture = subflowgraph_to_picture( intgraph, filepath, filetype )

    return graph_picture


def datastategraph_to_picture( tmpG, filename, filetype="svg" ):
    m = netx.drawing.nx_pydot.to_pydot( tmpG )
    if filetype == "svg":
        mybytes = m.create_svg()
    elif filetype == "png":
        mybytes = m.create_png()
    with open( filename, "wb" ) as pngtmpfile:
        pngtmpfile.write( mybytes )

def datastate_to_graph( mydatastate ):
    nodes, edges = mydatastate.nodes, mydatastate.edges
    node_to_datatype = mydatastate.node_to_datatype
    tmpG = netx.MultiDiGraph()
    for node in nodes:
        tmpG.add_node( node, datatype = node_to_datatype[ node ] )
    for edge in edges:
        tmpG.add_edge( edge[0], edge[1], edgename=edge[-1] )
    return tmpG


def subflowgraph_to_picture( mysubflowgraph, filename, filetype ):
    copyofflowgraph = netx.MultiDiGraph()
    
    copyofflowgraph.add_nodes_from( mysubflowgraph.nodes() )
    for cop_attr in ("image","label"):
        trans_attr = netx.get_node_attributes(mysubflowgraph, cop_attr)
        netx.set_node_attributes( copyofflowgraph, trans_attr, cop_attr)

    copyofflowgraph.add_edges_from( mysubflowgraph.edges() )
    for cop_attr in ("color", "label"):
        trans_attr = netx.get_edge_attributes(mysubflowgraph, cop_attr)
        netx.set_edge_attributes( copyofflowgraph, trans_attr, cop_attr)

    m = netx.drawing.nx_pydot.to_pydot( copyofflowgraph )
    #mybytes = m.create_png()
    #filelikebytes = io.BytesIO( mybytes )
    #mypic = mpimg.imread( filelikebytes )
    #return mypic
    if filetype == "svg":
        mybytes = m.create_svg()
    elif filetype == "png":
        mybytes = m.create_png()
    with open( filename, "wb" ) as pngtmpfile:
        pngtmpfile.write( mybytes )
    look_process = subprocess.call(["xdg-open", pngtmpfile.name])
    return look_process


def split_graph_to_subgraphs( supergraph ):
    multigraph = netx.MultiDiGraph( supergraph )
    asd = netx.Graph( supergraph )
    subgraph_sets = netx.connected_components( asd )
    return [ multigraph.subgraph( myset ) for myset in subgraph_sets ]


def create_stylesheets( subflowgraph_list ):
    factoryleaf_to_color = create_colordict( subflowgraph_list )
    factoryleaf_to_label = create_labeldict( subflowgraph_list )
    return factoryleaf_to_color, factoryleaf_to_label



def create_colordict( subflowgraph_list ):
    all_factoryleafs = set()
    for singlegraph in subflowgraph_list:
        input_data = netx.get_edge_attributes( singlegraph, "edgetype" )
        all_factoryleafs = all_factoryleafs.union( value.factoryleaf \
                                            for value in input_data.values())
    #factoryleaf_to_color ={ factleaf: "blue" for factleaf in all_factoryleafs }
    coloriter = iter( colorlist )
    factoryleaf_to_color = { factleaf: coloriter.__next__() \
                            for factleaf in all_factoryleafs }
    return factoryleaf_to_color


def create_labeldict( subflowgraph_list ):
    all_factoryleafs = set()
    for singlegraph in subflowgraph_list:
        input_data = netx.get_edge_attributes( singlegraph, "edgetype" )
        all_factoryleafs = all_factoryleafs.union( value.factoryleaf \
                                            for value in input_data.values())
    factoryleaf_to_color = { factleaf: factleaf.name 
                            for factleaf in all_factoryleafs }
    return factoryleaf_to_color
