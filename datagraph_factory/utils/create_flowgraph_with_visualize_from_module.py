import argparse
import importlib.util
from . import list_leafs
import os.path
from ..visualize import plot_flowgraph
from .asdf_flowgraph_plot import myvis as plot_flowgraph
from ..find_process_path import create_flowgraph_for_datanodes

def get_args():
    parser = argparse.ArgumentParser( description="get an overview over "\
                            +"all parts of "\
                            +"datagraph-factory that is used in that file" )
    parser.add_argument( "modulefile", type=str )
    parser.add_argument( "--moduledepth", "-d", dest='moduledepth', \
                            type=int, default=0, \
                            help="depth of being a submodule. For example "\
                            "with depth 1: 'path/to/file.py' -> 'to.file'" )
    parser.add_argument( "--dont-plot",dest="dont_plot", \
                        help="Trigger to deactivate plotting. instead just "\
                        +"all available leafs, datatypes and edgetypes",\
                        action='store_true')
    args = parser.parse_args()
    modulefile = os.path.abspath( args.modulefile )
    return modulefile, args.moduledepth, not args.dont_plot

def main( modulefile, depth, plot_trigger ):
    modulename = split_modulepath_to_modulename( modulefile, depth )
    spec = importlib.util.spec_from_file_location( modulename, modulefile )
    if spec == None:
        raise Exception( f"couldnt load module '{modulefile}'")
    mymodule = importlib.util.module_from_spec( spec )
    spec.loader.exec_module( mymodule )
    datatypes, edgetypes, factleafs, conclusions \
                    = list_leafs.get_all_datatypes( mymodule )

    if plot_trigger:
        myflowgraph = create_flowgraph_for_datanodes( factleafs.values(), \
                                                    conclusions.values())
        plot_flowgraph( myflowgraph )
    else:
        print_types_and_leafs( datatypes, edgetypes, factleafs, conclusions )


def print_types_and_leafs( datatypes, edgetypes, factleafs, conclusions ):
    print( "datatypes: " )
    for i in datatypes:
        print( i )
    print( "edgetypes: " )
    for i in edgetypes:
        print( i )
    print( "factleafs: " )
    for i in factleafs:
        print( i )
    print( "conclusions: " )
    for i in conclusions:
        print( i )


def split_modulepath_to_modulename( path_to_file, depth ):
    mylist = []
    tmppath = path_to_file
    for i in range( depth + 1 ):
        tmppath, tail = os.path.split( tmppath )
        mylist.insert( 0, tail )
    tmpmodule = ".".join( mylist )
    return tmpmodule[:-3] #remove '.py'


if __name__=="__main__":
    modulefile, depth, plot_trigger = get_args()
    main( modulefile, depth, plot_trigger )
       
