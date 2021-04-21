import unittest
from .processes import factory_leaf, conclusion_leaf
from .datagraph import datagraph, datatype, edgetype
from .find_process_path import create_flowgraph_for_datanodes
from . import find_process_path
from . import linear_factorybranch

from .constants import DATAGRAPH_DATATYPE as DATATYPE, \
                        DATAGRAPH_EDGETYPE as EDGETYPE
from .linear_factorybranch import create_linear_function
from .linear_factorybranch import FailstateReached
from .linear_factorybranch import DataRescueException

import csv
import tempfile
from . import test_datagraph_factory as mymodule
from .automatic_directory.create_program_from_datagraph import complete_datagraph

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
                            property_sumisnegative )
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
                        +"returned only to 'myinput' and'targetprop_negative'")
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
            self.assertRaises(find_process_path.datastate_not_connected_error,\
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
        tmpgraph.add_node( "myorigin", threetuple_origin )
        tmpgraph.add_node( "myinput", threetuple )
        tmpgraph.add_edge( "myorigin", "myinput", spawns_threetuple )
        inputgraph = tmpgraph.copy()
        tmpgraph.add_node( "targetprop_negative", property_valuesign )
        outputgraph = tmpgraph.copy()
        tmpgraph.add_edge( "myinput", "targetprop_negative", \
                            property_sumisnegative )
        tmpgraph.add_edge( "myorigin", "targetprop_negative", property_strange)
        outputgraph_with_edge = tmpgraph.copy()
        del( tmpgraph )

        flowgraph_with_conclusion = create_flowgraph_for_datanodes( \
                                        (sumup, check_isnegative, \
                                        threetuple_spawning_from_origin), \
                                        (conclusion_sumisnegative_so_is_tuple,\
                                        conclusion_sumispositive_so_is_tuple, \
                                        conclusion_strange))
        #softtest there should be 17 possible constellations
        self.assertEqual( len( flowgraph_with_conclusion.nodes()), 17 )

        myfoo = create_linear_function( \
                            flowgraph_with_conclusion, \
                            inputgraph, outputgraph_with_edge, verbosity =1 )
        a, b, c = 2, 4, -7
        asd_with_conclusionleaf = myfoo( myinput = threetuple(a,b,c), \
                                    myorigin= threetuple_origin(a,b,c) )

        # This tests if output has all the nodes and so the translation found
        self.assertEqual( set(outputgraph_with_edge.nodes()), \
                            asd_with_conclusionleaf.keys() )
        def testfoo():
            a, b, c = 2, 4, 7
            myfoo( myinput = threetuple(a,b,c) )
        self.assertRaises( DataRescueException, testfoo )

    def test_dataremover( self ):
        used_factoryleafs = ( \
                sumup, check_isnegative, \
                threetuple_spawning_from_origin, \
                threetuple_decrease_ifpositive )
        tmpgraph = datagraph()
        tmpgraph.add_node( "myinput", threetuple_origin )
        inputgraph = tmpgraph.copy()
        tmpgraph.add_node( "mynegative", threetuple )
        tmpgraph.add_node( "targetprop_negative", property_valuesign )
        tmpgraph.add_edge( "myinput", "mynegative", spawns_threetuple )
        tmpgraph.add_edge( "mynegative", "targetprop_negative", \
                            property_sumisnegative )
        outputgraph = tmpgraph.copy()
        del( tmpgraph )

        myflowgraph = create_flowgraph_for_datanodes( \
                                        used_factoryleafs, \
                                        (conclusion_sumisnegative_so_is_tuple,\
                                        conclusion_sumispositive_so_is_tuple))
        #from .visualize import plot_flowgraph
        #plot_flowgraph( myflowgraph )

        asd = [ q for q in myflowgraph.edges(keys=True,data=True) \
                    if q[0].nodes == set(('d4', 'd2', 'd5', 'd0')) \
                    and len(q[1].nodes)==6 ]
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

    def test_saving_and_loading( self ):
        used_modules = [ mymodule ]
        tmpgraph = datagraph()
        tmpgraph.add_node( "myinput", threetuple_origin )
        tmpgraph["myinput"] = threetuple_origin(1,2,3)
        from .automatic_directory.filehandler import save_graph, load_graph
        with tempfile.TemporaryDirectory() as tmpdirectory:
            save_graph( tmpgraph, tmpdirectory, used_modules )
            copy_tmpgraph = load_graph( tmpdirectory, used_modules )
        self.assertEqual( tmpgraph[ "myinput" ].b, copy_tmpgraph[ "myinput" ].b)

    def test_completing_graph( self ):
        used_factoryleafs = ( \
                sumup, check_isnegative, \
                threetuple_spawning_from_origin, \
                threetuple_decrease_ifpositive )
        myflowgraph = create_flowgraph_for_datanodes( \
                                        used_factoryleafs, 
                                        (conclusion_sumisnegative_so_is_tuple,\
                                        conclusion_sumispositive_so_is_tuple))

        tmpgraph = datagraph()
        tmpgraph.add_node( "myinput", threetuple_origin )
        tmpgraph["myinput"] = threetuple_origin(1,2,3)
        tmpgraph.add_node( "mypositive", threetuple )
        tmpgraph.add_node( "targetprop_positive", property_valuesign )
        tmpgraph.add_edge( "myinput", "mypositive", spawns_threetuple )
        tmpgraph.add_edge( "mypositive", "targetprop_positive", \
                            property_sumispositive )
        tmpgraph.add_node( "mynegative", threetuple )
        tmpgraph.add_node( "targetprop_negative", property_valuesign )
        tmpgraph.add_edge( "myinput", "mynegative", spawns_threetuple )
        tmpgraph.add_edge( "mynegative", "targetprop_negative", \
                            property_sumisnegative )
        #used_modules = [ mymodule ]

        myflowgraph = complete_datagraph( myflowgraph, tmpgraph )
        qwe =  myflowgraph["mynegative"]
        qwe2 =  myflowgraph["mypositive"]
        self.assertTrue( qwe.a+qwe.b+qwe.c < 0)
        self.assertTrue( qwe2.a+qwe2.b+qwe2.c > 0)
        #raise Exception( qwe.a, qwe.b, qwe.c, qwe2.a, qwe2.b, qwe2.c )


class threetuple_origin( datatype ):
    def __init__( self, a, b, c ):
        self.a = a
        self.b = b
        self.c = c

    def save_as( self, filepath ):
        with open( filepath, "wb" ) as csvfile:
            csvfile.write( self.a.to_bytes( 1, "big" ) )
            csvfile.write( self.b.to_bytes( 1, "big" ) )
            csvfile.write( self.c.to_bytes( 1, "big" ) )

    @classmethod
    def load_from( cls, filepath ):
        with open( filepath, "rb" ) as csvfile:
            a = int.from_bytes( csvfile.read(1), "big" )
            b = int.from_bytes( csvfile.read(1), "big" )
            c = int.from_bytes( csvfile.read(1), "big" )
        return cls( a, b, c )


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


_get_possiblepairs_spawns_threetuple = lambda: tuple((\
                                            (threetuple_origin, threetuple),\
                                            ))
spawns_threetuple = edgetype( _get_possiblepairs_spawns_threetuple, \
                                "spawned_threetuple", "" )

_get_possiblepairs_property_tuplesum = lambda: tuple((\
                                            (threetuple, tuplesum), \
                                            ))
property_tuplesum = edgetype( _get_possiblepairs_property_tuplesum, \
                                            "property_tuplesum", "" )

_get_possiblepairs_property_sumisnegative = lambda: tuple((\
                                            (threetuple, property_valuesign), \
                                            ))
property_sumisnegative = edgetype( _get_possiblepairs_property_sumisnegative, \
                                        "property_isnegative", "" )

_get_possiblepairs_property_isnegative = lambda: tuple((\
                                            (tuplesum, property_valuesign), \
                                            ))
property_isnegative = edgetype( _get_possiblepairs_property_isnegative, \
                                        "property_isnegative", "" )

_get_possiblepairs_property_ispositive = lambda: tuple((\
                                            (tuplesum, property_valuesign), \
                                            ))
property_ispositive = edgetype( _get_possiblepairs_property_ispositive, \
                                        "property_ispositive", "" )

_get_possiblepairs_property_sumispositive = lambda: tuple((\
                                            (threetuple, property_valuesign), \
                                            ))
property_sumispositive = edgetype( _get_possiblepairs_property_sumispositive, \
                                        "property_ispositive", "" )

_get_possiblepairs_strangeproperty = lambda: tuple([ \
                                    (threetuple_origin, property_valuesign),])
property_strange = edgetype( _get_possiblepairs_strangeproperty, "strange", "" )


_get_possiblepairs_property_tata = lambda: tuple((\
                                            (threetuple, property_valuesign), \
                                            ))
property_tata = edgetype( _get_possiblepairs_property_tata, "property_tata", "")

def _generate_datagraph():
    tmp = datagraph()
    tmp.add_node( "tuple", threetuple )
    tmp.add_node( "sum", tuplesum )
    tmp.add_edge( "tuple", "sum", property_tuplesum )
    tmp.add_node( "isneg", property_valuesign )
    tmp.add_edge( "sum", "isneg", property_isnegative )
    prestatus = tmp.copy()
    tmp.add_edge( "tuple", "isneg", property_sumisnegative )
    poststatus = tmp.copy()
    return prestatus, poststatus
conclusion_sumisnegative_so_is_tuple = conclusion_leaf( _generate_datagraph )
del( _generate_datagraph )

def _generate_datagraph():
    tmpgraph = datagraph()
    tmpgraph.add_node( "myorigin", threetuple_origin )
    tmpgraph.add_node( "myinput", threetuple )
    tmpgraph.add_edge( "myorigin", "myinput", spawns_threetuple )
    tmpgraph.add_node( "targetprop_negative", property_valuesign )
    tmpgraph.add_edge( "myinput", "targetprop_negative", \
                        property_sumisnegative )
    prestatus = tmpgraph.copy()
    tmpgraph.add_edge( "myorigin", "targetprop_negative", property_strange)
    poststatus = tmpgraph.copy()
    return prestatus, poststatus
conclusion_strange = conclusion_leaf( _generate_datagraph )
del( _generate_datagraph )


def _generate_datagraph():
    tmp = datagraph()
    tmp.add_node( "tuple", threetuple )
    tmp.add_node( "sum", tuplesum )
    tmp.add_edge( "tuple", "sum", property_tuplesum )
    tmp.add_node( "ispos", property_valuesign )
    tmp.add_edge( "sum", "ispos", property_ispositive )
    prestatus = tmp.copy()
    tmp.add_edge( "tuple", "ispos", property_sumispositive )
    poststatus = tmp.copy()
    return prestatus, poststatus
conclusion_sumispositive_so_is_tuple = conclusion_leaf( _generate_datagraph )
del( _generate_datagraph )




def _generate_datagraph():
    tmp = datagraph()
    tmp.add_node( "mytuple", threetuple )
    prestatus = tmp.copy()
    tmp.add_node( "mysum", tuplesum )
    tmp.add_edge( "mytuple", "mysum", property_tuplesum )
    poststatus = tmp.copy()
    return prestatus, poststatus
def sumfunction( mytuple ):
        erg = mytuple.a + mytuple.b + mytuple.c
        return { "mysum": tuplesum( erg ) }
sumup = factory_leaf( _generate_datagraph, sumfunction, name="sumup" )
#del( prestatus, poststatus, sumfunction, tmp )
del( _generate_datagraph, sumfunction )


def _generate_datagraph():
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
    return prestatus, poststatus
def call_function( q, b ):
    if b.val < 0:
        return { "c": property_valuesign() }
    else:
        return { "d": property_valuesign() }
check_isnegative = factory_leaf( _generate_datagraph, call_function, \
                                                        name="check_sign" )
del( _generate_datagraph, call_function )


def _generate_datagraph():
    tmp = datagraph()
    tmp.add_node( "q", threetuple_origin )
    prestatus = tmp.copy()
    tmp.add_node( "w", threetuple )
    tmp.add_edge( "q", "w", spawns_threetuple )
    poststatus = tmp.copy()
    return prestatus, poststatus
def call_function( q ):
    return { "w": threetuple( q.a, q.b, q.c ) }
threetuple_spawning_from_origin = factory_leaf( _generate_datagraph, \
                                                call_function, name="spawn" )
del( _generate_datagraph, call_function )


def _generate_datagraph():
    tmp = datagraph()
    tmp.add_node( "q", threetuple_origin )
    tmp.add_node( "old", threetuple )
    tmp.add_edge( "q", "old", spawns_threetuple )
    tmp.add_node( "oldval", property_valuesign )
    tmp.add_edge( "old", "oldval", property_sumispositive )
    prestatus = tmp.copy()
    tmp.remove_node( "old" )
    tmp.remove_node( "oldval" )
    tmp.add_node( "new", threetuple )
    tmp.add_edge( "q", "new", spawns_threetuple )
    poststatus = tmp.copy()
    return prestatus, poststatus
def call_function( q, old, oldval ):
    return { "new": threetuple( old.a-1, old.b, old.c ) }
threetuple_decrease_ifpositive = factory_leaf( _generate_datagraph, \
                                                    call_function, cost=2,\
                                                    name="decrease")
del( _generate_datagraph, call_function )


if __name__=="__main__":
    unittest.main()
