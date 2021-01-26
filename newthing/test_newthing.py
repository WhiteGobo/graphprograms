import unittest
from .graphtoflowcontrol import nodefunctioncontainer
from .graphtoflowcontrol import NODECLASS, NODEFUNCTION, EDGETYPE
from .graphtoflowcontrol import cyprogra
import networkx as netx

class TestNewThing( unittest.TestCase ):
    def test_singlenode( self ):
        # generate graph
        mygraph = netx.Graph()
        data = { NODECLASS: printstartend }
        mygraph.add_node( 0, **data )

        #generate cyprogra
        myprogram = cyprogra( mygraph )

        #cycle cyprogra
        myprogram.cycle()
        #get returnvalues of cyprogra
        asd = myprogram.return_to_graph()

        self.assertEqual( 2, asd.nodes(data=True)[0]["customint"] )

    def test_nodepair( self ):
        mygraph = netx.Graph()
        data = { NODECLASS: printstartend }
        mygraph.add_node( 0, **data )
        mygraph.add_node( 1, **data )
        #see printstartend.gespraech for needed variables
        mygraph.add_edge( 0, 1, **{EDGETYPE:"gespraech", "text":"joahist text"})

        myprogram = cyprogra( mygraph )
        myprogram.cycle()
        asd = myprogram.return_to_graph()

        self.assertEqual( 2, asd.nodes(data=True)[0]["customint"] )
        self.assertEqual( 4, asd.nodes(data=True)[1]["customint"] )



class printstartend( nodefunctioncontainer ):
    def __init__( self ):
        super().__init__()

        self.customint = 0
        self.init_timing_graph()
        self.init_edgelibrary()

    def init_timing_graph( self ):
        guckguckattr = {NODEFUNCTION: self.guckguck}
        self.timing_graph.add_node( "guckguck", **guckguckattr )

        tschuessattr = {NODEFUNCTION: self.tschuess}
        self.timing_graph.add_node( "tschuess", **tschuessattr )

        self.timing_graph.add_edge( "guckguck", "tschuess" )

    def init_edgelibrary( self ):
        edgetype = "gespraech"
        gespraech_after_self = ["guckguck"]
        gespraech_after_other = ["guckguck"]
        gespraech_before_self = ["tschuess"]
        gespraech_before_other = ["tschuess"]
        self.add_possible_edge_to( printstartend, edgetype, \
                                self.gespraech, \
                                gespraech_after_self, gespraech_before_self, \
                                gespraech_after_other, gespraech_before_other)
    
    def guckguck( self ):
        self.customint = 1

    def tschuess( self ):
        self.customint = self.customint * 2

    def gespraech( self, other, text ):
        other.customint = self.customint + other.customint


if __name__=="__main__":
    unittest.main()
