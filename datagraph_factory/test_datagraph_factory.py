import unittest
from .processes import factory_leaf, conclusion_leaf
from .datagraph import datagraph, datatype, edgetype
from .find_process_path import create_flowgraph_for_datanodes
from . import find_process_path
from . import linear_factorybranch

from .constants import DATAGRAPH_DATATYPE as DATATYPE
from .constants import DATAGRAPH_EDGETYPE as EDGETYPE
from .linear_factorybranch import create_linear_function
from .linear_factorybranch import FailstateReached


class test_graph( unittest.TestCase ):

    def test_factory_leaf( self ):
        a,b,c = 3,4,5
        asd = sumup( mytuple = threetuple(a,b,c) )
        self.assertEqual( asd["mysum"].val, a+b+c )

    def test_datagraph_factory( self ):
        #use:
        #tuplesum, isnegative, threetuple, property_tuplesum, 
        #property_isnegative, sumup

        flowgraph = create_flowgraph_for_datanodes( (sumup, check_isnegative) )

        tmpgraph = datagraph()
        tmpgraph.add_node( "myinput", threetuple )
        inputgraph = tmpgraph.copy()
        tmpgraph.add_node( "mysum", tuplesum )
        tmpgraph.add_node( "targetprop_negative", property_valuesign )
        tmpgraph.add_edge( "mysum", "targetprop_negative", \
                            property_isnegative )
        outputgraph_without_edge = tmpgraph.copy()
        tmpgraph.add_edge( "myinput", "targetprop_negative", \
                            property_isnegative )
        outputgraph_with_wrong_edge = tmpgraph.copy()
        tmpgraph.remove_edge( "myinput", "targetprop_negative", 0 )
        tmpgraph.add_edge( "myinput", "mysum", property_tuplesum )
        outputgraph = tmpgraph.copy()
        del( tmpgraph )

        myfoo = create_linear_function( flowgraph, inputgraph, outputgraph )

        a, b, c = 2, 4, -7
        asd = myfoo( myinput = threetuple(a,b,c) )
        try:
            self.assertTrue( "myinput" in asd)
        except AssertionError as err:
            err.args = (*err.args, "factoryleaf didnt return anything useful",\
                        f"returned data to nodes {asd.keys()}, should had "\
                        +"returned only to 'myinput' and 'targetprop_negative'")
        try:
            self.assertTrue( "targetprop_negative" in asd )
            self.assertEqual( len( asd ), 3 )
        except AssertionError as err:
            err.args = (*err.args, "factoryleaf didnt produced right output", \
                        asd )
            raise err


        def testfoo():
            create_linear_function( flowgraph, \
                            inputgraph, outputgraph_without_edge, \
                            verbosity =1 )
        try:
            self.assertRaises( find_process_path.datastate_not_connected_error,\
                                testfoo )
        except AssertionError as err:
            err.args = (*err.args, "This function should have thrown an error"
                        "because it the outputgraph isnt connected" )
            raise err

        def testfoo():
            create_linear_function( flowgraph, \
                            inputgraph, outputgraph_with_wrong_edge, \
                            verbosity =1 )
        try:
            self.assertRaises( linear_factorybranch.NoPathToOutput,\
                                testfoo )
        except AssertionError as err:
            err.args = (*err.args, "This function should have thrown an error"
                        "because it cant find with given factoryleafs"
                        " a solution to given problem")
            raise err


    def test_datagraph_factory_with_conclusionlist( self ):
        tmpgraph = datagraph()
        tmpgraph.add_node( "myinput", threetuple )
        inputgraph = tmpgraph.copy()
        tmpgraph.add_node( "targetprop_negative", property_valuesign )
        outputgraph = tmpgraph.copy()
        tmpgraph.add_edge( "myinput", "targetprop_negative", \
                            property_isnegative )
        outputgraph_with_edge = tmpgraph.copy()
        del( tmpgraph )

        flowgraph_with_conclusion = create_flowgraph_for_datanodes( \
                                        (sumup, check_isnegative), \
                                        (conclusion_sumisnegative_so_is_tuple,\
                                        conclusion_sumispositive_so_is_tuple))
        #softtest there should be 8 possible constellations
        self.assertEqual( len( flowgraph_with_conclusion.nodes()), 8 )

        myfoo = create_linear_function( \
                            flowgraph_with_conclusion, \
                            inputgraph, outputgraph_with_edge, verbosity =1 )
        a, b, c = 2, 4, -7
        asd_with_conclusionleaf = myfoo( myinput = threetuple(a,b,c) )

        # This tests if output has all the nodes and so the translation found
        self.assertEqual( set(outputgraph_with_edge.nodes()), \
                            asd_with_conclusionleaf.keys() )
        def testfoo():
            a, b, c = 2, 4, 7
            myfoo( myinput = threetuple(a,b,c) )
        self.assertRaises( FailstateReached, testfoo )

        #from .visualizer import visualize_flowgraph
        #visualize_flowgraph( flowgraph_with_conclusion )

    def test_dataremover( self ):
        used_factoryleafs = ( \
                sumup, check_isnegative, \
                threetuple_spawning_from_origin, \
                threetuple_decrease_ifpositive )
        #used_factoryleafs = ( \
        #        #sumup, check_isnegative, \
        #        threetuple_decrease_ifpositive, \
        #        )
        tmpgraph = datagraph()
        tmpgraph.add_node( "myinput", threetuple_origin )
        inputgraph = tmpgraph.copy()
        tmpgraph.add_node( "mynegative", threetuple )
        tmpgraph.add_node( "targetprop_negative", property_valuesign )
        tmpgraph.add_edge( "myinput", "mynegative", spawns_threetuple )
        tmpgraph.add_edge( "mynegative", "targetprop_negative", \
                            property_isnegative )
        outputgraph = tmpgraph.copy()
        del( tmpgraph )

        myflowgraph = create_flowgraph_for_datanodes( \
                                        used_factoryleafs, \
                                        (conclusion_sumisnegative_so_is_tuple,\
                                        conclusion_sumispositive_so_is_tuple))
        #from .visualize import plot_flowgraph
        #plot_flowgraph( myflowgraph )

        asd = [ q for q in myflowgraph.edges(keys=True,data=True) if q[0].nodes == set(('d4', 'd2', 'd5', 'd0')) and len(q[1].nodes)==6 ]
        #for i in myflowgraph.edges():
        for a,b, key, data in asd:
            print( data )
            print( a.edges )
            print( b.nodes )
            print( b.edges )
            print(" \n\n\n")

        myfoo = create_linear_function( \
                            myflowgraph, inputgraph, \
                            outputgraph, verbosity=1 )
        a, b, c = 0,4,2
        asd = myfoo( myinput=threetuple_origin( a,b,c ) )
        outputtuple = asd["mynegative"]
        self.assertEqual( -outputtuple.a, outputtuple.b + outputtuple.c + 1)



class threetuple_origin( datatype ):
    def __init__( self, a, b, c ):
        self.a = a
        self.b = b
        self.c = c

class threetuple( datatype ):
    def __init__( self, a=1,b=2,c=3):
        self.a = a
        self.b = b
        self.c = c

class tuplesum( datatype ):
    def __init__( self, val ):
        self.val = val

class property_valuesign( datatype ):
    pass


spawns_threetuple = edgetype( threetuple_origin, threetuple, \
                                "spawned_threetuple", "" )
property_tuplesum = edgetype( threetuple, tuplesum, "property_tuplesum", "" )

property_isnegative = edgetype( threetuple, property_valuesign, "property_isnegative", "" )

property_ispositive = edgetype( threetuple, property_valuesign, "property_ispositive", "" )

property_tata = edgetype( threetuple, property_valuesign, "property_tata", "" )

tmp = datagraph()
tmp.add_node( "tuple", threetuple )
tmp.add_node( "sum", tuplesum )
tmp.add_edge( "tuple", "sum", property_tuplesum )
tmp.add_node( "isneg", property_valuesign )
tmp.add_edge( "sum", "isneg", property_isnegative )
prestatus = tmp.copy()
tmp.add_edge( "tuple", "isneg", property_isnegative )
poststatus = tmp.copy()
del( tmp )
conclusion_sumisnegative_so_is_tuple = conclusion_leaf( prestatus, poststatus )
del( prestatus, poststatus )


tmp = datagraph()
tmp.add_node( "tuple", threetuple )
tmp.add_node( "sum", tuplesum )
tmp.add_edge( "tuple", "sum", property_tuplesum )
tmp.add_node( "ispos", property_valuesign )
tmp.add_edge( "sum", "ispos", property_ispositive )
prestatus = tmp.copy()
tmp.add_edge( "tuple", "ispos", property_ispositive )
poststatus = tmp.copy()
del( tmp )
conclusion_sumispositive_so_is_tuple = conclusion_leaf( prestatus, poststatus )
del( prestatus, poststatus )




tmp = datagraph()
tmp.add_node( "mytuple", threetuple )
prestatus = tmp.copy()
tmp.add_node( "mysum", tuplesum )
tmp.add_edge( "mytuple", "mysum", property_tuplesum )
poststatus = tmp.copy()
def sumfunction( mytuple ):
        erg = mytuple.a + mytuple.b + mytuple.c
        return { "mysum": tuplesum( erg ) }
sumup = factory_leaf( prestatus, poststatus, sumfunction, name="sumup" )
del( prestatus, poststatus, sumfunction, tmp )


tmp = datagraph()
tmp.add_node( "q", threetuple )
tmp.add_node( "b", tuplesum )
tmp.add_edge( "q", "b", property_tuplesum )
prestatus = tmp.copy()
tmp.add_node( "c", property_valuesign )
tmp.add_node( "d", property_valuesign )
tmp.add_edge( "b", "c", property_isnegative )
tmp.add_edge( "b", "d", property_ispositive )
poststatus = tmp.copy()
del( tmp )

def call_function( q, b ):
    if b.val < 0:
        return { "c": property_valuesign() }
    else:
        return { "d": property_valuesign() }
check_isnegative = factory_leaf( prestatus, poststatus, call_function, \
                                                        name="check_sign" )
del( prestatus, poststatus, call_function )


tmp = datagraph()
tmp.add_node( "q", threetuple_origin )
prestatus = tmp.copy()
tmp.add_node( "w", threetuple )
tmp.add_edge( "q", "w", spawns_threetuple )
poststatus = tmp.copy()
def call_function( q ):
    return { "w": threetuple( q.a, q.b, q.c ) }
threetuple_spawning_from_origin = factory_leaf( prestatus, poststatus, \
                                                call_function, name="spawn" )
del( prestatus, poststatus, call_function, tmp )


tmp = datagraph()
tmp.add_node( "q", threetuple_origin )
tmp.add_node( "old", threetuple )
tmp.add_edge( "q", "old", spawns_threetuple )
tmp.add_node( "oldval", property_valuesign )
tmp.add_edge( "old", "oldval", property_ispositive )
prestatus = tmp.copy()
tmp.remove_node( "old" )
tmp.remove_node( "oldval" )
tmp.add_node( "new", threetuple )
tmp.add_edge( "q", "new", spawns_threetuple )
poststatus = tmp.copy()
def call_function( q, old, oldval ):
    return { "new": threetuple( old.a-1, old.b, old.c ) }
threetuple_decrease_ifpositive = factory_leaf( prestatus, poststatus, \
                                                    call_function, cost=2,\
                                                    name="decrease")
del( prestatus, poststatus, call_function, tmp )


if __name__=="__main__":
    unittest.main()
