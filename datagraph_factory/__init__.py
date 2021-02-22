"""
Datagraph Factory

This Package supports creating programs via input-output-snippets which
then will be put together to create more complex program flows.

Data will be organised with datagraphs( networkx.MultiDiGraph-like objects).
These datagraphs consist of nodes and edges, whereby each node has a
corresponding datagraph_factory.datatype:
    datagraph.add_node( 'some custom id', class( instance of datatype ) )
The corresponding class must descend from datagraph_factory.datatype. 
Data that is to be stored must be accepted by __init__. Eg:
    class mydatatype( datatype ):
        def __init__( self, custom_data ):
            self.custom_data = custom_data

Every node must connected via edges
    datagraph.add_edge( 'first node', 'second node', object:edgetype )
For creation of edgetype use:
    myedgetype = edgetype( firstnodeclass, secondnodeclass, \
                            'name of edgetpye', 'documentation' )

simplest codesnippets can be packed to a factory_leaf:
    def foo_snippet( nodename_from_prestatus ):
        tmp = nodeinputname.customvariable 
        return { nodename_from_poststatus: 
                    nodeoutputtype( customvariable=tmp ) }
    prestatus = create_datagraph1()
    poststatus = create_datagraph2()
    my_snippet  = factory_leaf( prestatus, poststatus, foo_snippet )

additional edges in complex programs can be made with conclusionleafs:
    asdf = conclusion_leaf( prestatus, poststatus )

For complex programs first you must create flowgraphs:
    myflowgraph = create_flowgraph_for_datanodes( 
                        list_of_factoryleafs,
                        list_of_conslutionleafs, 
                        )

These flowgraphs can be used for creation of complex programs. These
programs are themself again factory_leafs and can be used for further
flowgraph creation:
Till now you can only make simple programs with create_linear_function
    mynewfactoryleaf = create_linear_function(
                            myflowgraph, prestatus, poststatus )

"""
from .datagraph import edgetype, datatype, datagraph
from .processes import factory_leaf, conclusion_leaf
from .find_process_path import create_flowgraph_for_datanodes
from .linear_factorybranch import create_linear_function
__all__=[ "edgetype", "datatype", "datagraph", "factory_leaf", "conclusion_leaf", "create_flowgraph_for_datanodes", "create_linear_function", "visualize" ]
