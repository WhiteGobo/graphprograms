import unittest
from .processes import factory_leaf, conclusion_leaf
from .datagraph import datagraph, datatype, edgetype
from .find_process_path import create_flowgraph_for_datanodes

from .constants import DATAGRAPH_DATATYPE as DATATYPE
from .constants import DATAGRAPH_EDGETYPE as EDGETYPE
from .linear_factorybranch import create_linear_function


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
        tmpgraph.add_node( "myinput", **{DATATYPE: threetuple} )
        inputgraph = tmpgraph.copy()
        tmpgraph.add_node( "targetprop_negative", **{DATATYPE: isnegative} )
        outputgraph = tmpgraph.copy()
        tmpgraph.add_edge( "myinput", "targetprop_negative", \
                            **{ EDGETYPE: property_isnegative } )
        outputgraph_with_edge = tmpgraph.copy()
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
            self.assertEqual( len( asd ), 2 )
        except AssertionError as err:
            err.args = (*err.args, "factoryleaf didnt produced right output" )
            raise err


        def testfoo():
            create_linear_function( flowgraph, \
                            inputgraph, outputgraph_with_edge, verbosity =1 )
        try:
            self.assertRaises( KeyError, testfoo )
        except AssertionError as err:
            err.args = (*err.args, "This function should have thrown an error"
                        "because it cant find with given factoryleafs"
                        " a solution to given problem")
            raise err

        flowgraph_with_conclusion = create_flowgraph_for_datanodes( \
                                        (sumup, check_isnegative), \
                                        (conclusion_sumisnegative_so_is_tuple,))
        #asd_with_conclusionleaf = create_linear_function( \
        #                    flowgraph_with_conclusion, \
        #                    inputgraph, outputgraph_with_edge, verbosity =1 )
        #asd_with_conclusionleaf = myfoo( myinput = threetuple(a,b,c) )
        #print( asd_with_conclusionleaf )

        #from .visualizer import visualize_flowgraph
        #visualize_flowgraph( flowgraph_with_conclusion )




class threetuple( datatype ):
    def __init__( self, a=1,b=2,c=3):
        self.a = a
        self.b = b
        self.c = c

class tuplesum( datatype ):
    def __init__( self, val ):
        self.val = val

class isnegative( datatype ):
    pass

class ispositive( datatype ):
    pass

class property_tuplesum( edgetype ):
    nodetype_source = threetuple
    nodetype_target = tuplesum

class property_isnegative( edgetype ):
    nodetype_source = threetuple
    nodetype_target = isnegative

class property_ispositive( edgetype ):
    nodetype_source = threetuple
    nodetype_target = ispositive

tmp = datagraph()
tmp.add_node( "tuple", threetuple )
tmp.add_node( "sum", tuplesum )
tmp.add_edge( "tuple", "sum", property_tuplesum )
tmp.add_node( "isneg", isnegative )
tmp.add_edge( "sum", "isneg", property_isnegative )
prestatus = tmp.copy()
tmp.add_edge( "tuple", "isneg", property_isnegative )
poststatus = tmp.copy()
del( tmp )
conclusion_sumisnegative_so_is_tuple = conclusion_leaf( prestatus, poststatus )
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
sumup = factory_leaf( prestatus, poststatus, sumfunction )
del( prestatus, poststatus, sumfunction, tmp )


tmp = datagraph()
tmp.add_node( "q", threetuple )
tmp.add_node( "b", tuplesum )
tmp.add_edge( "q", "b", property_tuplesum )
prestatus = tmp.copy()
tmp.add_node( "c", isnegative )
tmp.add_node( "d", ispositive )
tmp.add_edge( "b", "c", property_isnegative )
tmp.add_edge( "b", "d", property_ispositive )
poststatus = tmp.copy()
del( tmp )

def call_function( q, b ):
    if b.val < 0:
        return { "c": isnegative() }
    else:
        return { "d": ispositive() }
check_isnegative = factory_leaf( prestatus, poststatus, call_function )
del( prestatus, poststatus, call_function )



if __name__=="__main__":
    unittest.main()
