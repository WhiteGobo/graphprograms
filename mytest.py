import unittest
from datagraph_factory.classes import factory_leaf
from datagraph_factory.datagraph import datagraph, datatype, edgetype
from datagraph_factory.find_process_path import main as findpath


class test_graph( unittest.TestCase ):
    def test_datagraph_factory( self ):
        #use:
        #tuplesum, isnegative, threetuple, property_tuplesum, 
        #property_isnegative, sumup
        findpath()
        pass


class threetuple( datatype ):
    a = 1
    b = 2
    c = 3

class tuplesum( datatype ):
    def __init__( self, name ):
        super().__init__( str( name )+"tuplesum", "this is a sum" )
        self.mysum = None

class isnegative( datatype ):
    def __init__( self, name ):
        super().__init__( name + "isnegative", "source is negative" )

class property_tuplesum( edgetype ):
    nodetype_source = threetuple
    nodetype_target = tuplesum

class property_isnegative( edgetype ):
    nodetype_source = threetuple
    nodetype_target = isnegative

class sumup( datafactory_leaf ):
    tmp = datagraph()
    tmp.add_node( 0, datatype = threetuple )
    prestatus = tmp.copy()
    tmp.add_node( 1, datatype = tuplesum )
    tmp.add_edge( 0, 1, edgetype = property_tuplesum )
    poststatus = tmp.copy()
    del( tmp )

    cost = 1



if __name__=="__main__":
    unittest.main()
