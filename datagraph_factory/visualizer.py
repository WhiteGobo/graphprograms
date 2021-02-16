import networkx as netx
from .find_process_path import flowgraph
import matplotlib.pyplot as plt

def visualize_flowgraph( myflowgraph:flowgraph ):
    netx.draw_circular( myflowgraph, with_labels=True )
    plt.show()
