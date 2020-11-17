#/bin/env/ python

import unittest
import networkxarithmetic as arit
import networkx as netx

_singlenodegraph_graphml = """
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <key id="d0" for="node" attr.name="calctype" attr.type="string" />
  <graph edgedefault="directed">
    <node id="1">
      <data key="d0">ladder</data>
    </node>
  </graph>
</graphml>
"""

_twonodesgraph_graphml = """
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <key id="d1" for="edge" attr.name="edgetype" attr.type="string" />
  <key id="d0" for="node" attr.name="calctype" attr.type="string" />
  <graph edgedefault="directed">
    <node id="1">
      <data key="d0">ladder</data>
    </node>
    <node id="2">
      <data key="d0">adder</data>
    </node>
    <edge source="1" target="2" id="0">
      <data key="d1">push</data>
    </edge>
  </graph>
</graphml>
"""

_transferweight1graph_graphml = """
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <key id="d1" for="edge" attr.name="edgetype" attr.type="string" />
  <key id="d2" for="edge" attr.name="weight" attr.type="float" />
  <key id="d0" for="node" attr.name="calctype" attr.type="string" />
  <graph edgedefault="directed">
    <node id="1">
      <data key="d0">ladder</data>
    </node>
    <node id="2">
      <data key="d0">adder</data>
    </node>
    <edge source="1" target="2" id="0">
      <data key="d1">constmul</data>
      <data key="d2">1.0</data>
    </edge>
  </graph>
</graphml>
"""
_transferweight15graph_graphml = """
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <key id="d1" for="edge" attr.name="edgetype" attr.type="string" />
  <key id="d2" for="edge" attr.name="weight" attr.type="float" />
  <key id="d0" for="node" attr.name="calctype" attr.type="string" />
  <graph edgedefault="directed">
    <node id="1">
      <data key="d0">ladder</data>
    </node>
    <node id="2">
      <data key="d0">adder</data>
    </node>
    <edge source="1" target="2" id="0">
      <data key="d1">constmul</data>
      <data key="d2">1.5</data>
    </edge>
  </graph>
</graphml>
"""

# retrieve data nodeid-given:
# nodedata = graph.nodes( data=True )[nodeid]
# out_edges = graph.edges( nodeid, data=True )
def _ladder_code():
    # data_dict will be proccesed for data space, use strings as ids, as they
    # can correspond to node attributes for start values.
    # default values will be written in ladder code
    # when default value is None there will be an error if no value is given
    # in the graph
    nodedata = { "lout":0 }

    # the code snippets will be stored in a DiGraph
    # edges will determine the order in which the codesnippets will be executed
    # nodes should have as identifer a string (or string-like)
    # codesnippets will data with value[%d]
    # temporary data can be used
    code_graph = netx.DiGraph()
    code_graph.add_node( "ladderup", code=["%s = %s + 1"],
                                    values=[("lout", "lout")])
    # extra function can be given by a dictionary as third returnvalue
    # keys must be strings correspdoning to codesnippets
    #def foo():
    #    pass
    #functiondictionary = { "fo":foo } # fo can be used in codesnippets
    functiondictionary = {}
    return nodedata, code_graph, functiondictionary

def adder_code():
    data_dict={ "aout":0 }
    code_graph = netx.DiGraph()
    code_graph.add_node( "reset", code=["%s = 0"],
                                values=[("aout",)])
    code_graph.add_node( "sum", code=[], values=[])
    code_graph.add_edge( "reset", "sum" ) # reset will be executed before sum
    functiondictionary = {}
    return data_dict, code_graph, functiondictionary

def nodefault_code():
    data_dict={ "myvalue":None }
    code_graph = netx.DiGraph()
    functiondictionary = {}
    return data_dict, code_graph, functiondictionary

def extraglobal_code():
    data_dict={ "myvalue":0 }
    def mygiveone():
        return 1
    functiondictionary = { "giveone":mygiveone }
    code_graph = netx.DiGraph()
    code_graph.add_node( "reset", code=["%s = giveone()"],
                                values=[("myvalue",)])
    return data_dict, code_graph, functiondictionary

def laddertoadder_push():
    """
    for type control dont use **edgeattr but value=default instead
    """
    after_execution_nodeout = ["ladderup"]
    after_execution_nodein = ["reset"]
    before_execution_nodeout = []
    before_execution_nodein = ["sum"]
    code_graph = netx.DiGraph()
    # value pair in values must contain if innode('in') or outnode('out') and
    # the valueidentifier of the corresponding node eg ladder has id with 'out'
    code_graph.add_node( "push", code=["%s = %s + %s"],
                        values=[(("in","aout"),("in","aout"),("out","lout"))])

    return code_graph, after_execution_nodeout, after_execution_nodein, \
                    before_execution_nodeout, before_execution_nodein

def laddertoadder_constmul( weight=1 ):
    after_execution_nodeout = ["ladderup"]
    after_execution_nodein = ["reset"]
    before_execution_nodeout = []
    before_execution_nodein = ["sum"]
    code_graph = netx.DiGraph()
    # value pair in values must contain if innode('in') or outnode('out') and
    # the valueidentifier of the corresponding node eg ladder has id with 'out'
    code_graph.add_node( "push", code=["%s = " + "%f*"%(weight) \
                                        + "%s"],
                        values=[(("in","aout"),("out","lout"))])

    return code_graph, after_execution_nodeout, after_execution_nodein, \
                    before_execution_nodeout, before_execution_nodein

def addertoadder_push():
    #after_execution_nodeout = ["sum"]
    #after_execution_nodein = ["reset"]
    #before_execution_nodeout = []
    #before_execution_nodein = ["sum"]
    asd = [["sum"],["reset"],[],["sum"]]
    code_graph = netx.DiGraph()
    code_graph.add_node( "push", code=["%s = %s + %s"],
                        values=[(("in","aout"),("in","aout"),("out","aout"))])

    return code_graph, *asd
    #return code_graph, after_execution_nodeout, after_execution_nodein, \
    #                before_execution_nodeout, before_execution_nodein
    




class TestNetworkxarithmeticMethods( unittest.TestCase ):
    def setUp( self ):
        self.testgraph_singlenode= netx.parse_graphml( \
                                            _singlenodegraph_graphml, \
                                            force_multigraph=True)
        self.testgraph_twonodes= netx.parse_graphml( \
                                            _twonodesgraph_graphml, \
                                            force_multigraph=True)
        self.testgraph_singlenodefault=netx.MultiDiGraph()
        self.testgraph_singlenodefault.add_node( 0, calctype="nodefault")
        self.testgraph_singlewithdefault=netx.MultiDiGraph()
        self.testgraph_singlewithdefault.add_node( 0, calctype="nodefault", \
                                                myvalue=0 )
        self.testgraph_cyclegraph=netx.MultiDiGraph()
        self.testgraph_cyclegraph.add_node( 0, calctype="adder" )
        self.testgraph_cyclegraph.add_node( 1, calctype="adder" )
        self.testgraph_cyclegraph.add_edge( 0, 1, edgetype="push" )
        self.testgraph_cyclegraph.add_edge( 1, 0, edgetype="push" )

        self.testgraph_extraglobal=netx.MultiDiGraph()
        self.testgraph_extraglobal.add_node( 0, calctype="extraglobal" )


        self.code_library = { "ladder":_ladder_code, "adder":adder_code, \
                "nodefault":nodefault_code, "extraglobal":extraglobal_code }
        self.edge_library = { ("ladder", "adder", "push"):laddertoadder_push, \
                            ("adder", "adder", "push"):addertoadder_push, \
                            ("ladder", "adder", "constmul"):laddertoadder_constmul,\
                            }


        self.testgraph_weights1 = netx.parse_graphml( \
                                            _transferweight1graph_graphml, \
                                            force_multigraph=True)
        self.testgraph_weights15 = netx.parse_graphml( \
                                            _transferweight15graph_graphml, \
                                            force_multigraph=True)

    def test_singlenode( self ):
        graphcode1 = arit.graphcontainer()
        graphcode1.update_calclibrary( self.code_library )
        graphcode1.update_edgelibrary( self.edge_library )
        graphcode1.createcode_with_graph( self.testgraph_singlenode )

        self.assertEqual( graphcode1.values[0], 0 )
        graphcode1.cycle()
        self.assertEqual( graphcode1.values[0], 1 )
        graphcode1.cycle()
        self.assertEqual( graphcode1.values[0], 2 )

    def test_twonodes( self ):
        graphcode2 = arit.graphcontainer()
        graphcode2.update_calclibrary( self.code_library )
        graphcode2.update_edgelibrary( self.edge_library )
        graphcode2.createcode_with_graph( self.testgraph_twonodes )

        self.assertEqual( graphcode2.values[0], 0 )
        self.assertEqual( graphcode2.values[1], 0 )
        graphcode2.cycle()
        self.assertEqual( graphcode2.values[0], 1 )
        self.assertEqual( graphcode2.values[1], 1 )
        graphcode2.cycle()
        self.assertEqual( graphcode2.values[0], 2 )
        self.assertEqual( graphcode2.values[1], 2 )

    def test_defaultvalues_witherrortesting( self ):
        graphcode3 = arit.graphcontainer()
        graphcode3.update_calclibrary( self.code_library )
        graphcode3.update_edgelibrary( self.edge_library )
        def testfunction():
            graphcode3.createcode_with_graph( self.testgraph_singlenodefault)
        self.assertRaises( arit.NoStartvalueGiven_Error, testfunction )

        graphcode4 = arit.graphcontainer()
        graphcode4.update_calclibrary( self.code_library )
        graphcode4.update_edgelibrary( self.edge_library )
        graphcode4.createcode_with_graph( self.testgraph_singlewithdefault )

    def test_cyclegrapherror( self ):
        graphcode5 = arit.graphcontainer()
        graphcode5.update_calclibrary( self.code_library )
        graphcode5.update_edgelibrary( self.edge_library )
        def testfunction():
            graphcode5.createcode_with_graph( self.testgraph_cyclegraph )
        self.assertRaises( arit.CycleToTree_Error, testfunction )

    def test_extrafunctions( self ):
        graphcode6 = arit.graphcontainer()
        graphcode6.update_calclibrary( self.code_library )
        graphcode6.update_edgelibrary( self.edge_library )
        graphcode6.createcode_with_graph( self.testgraph_extraglobal )
        self.assertEqual( graphcode6.values[0], 0 )
        graphcode6.cycle()
        self.assertEqual( graphcode6.values[0], 1 )

    def test_useedgeonincompatiblenodes( self ):
        """
        for compatilblity all values and timing nodes must exist
        """
        pass

    def test_usedifferentedgeweights( self ):
        graphcodeweights1 = arit.graphcontainer()
        graphcodeweights1.update_calclibrary( self.code_library )
        graphcodeweights1.update_edgelibrary( self.edge_library )
        graphcodeweights1.createcode_with_graph( self.testgraph_weights1 )
        graphcodeweights1.cycle()
        outputgraph = graphcodeweights1.transferdatatograph()
        self.assertEqual( outputgraph.nodes( data=True )['2']["aout"], 1 )

        graphcodeweights15 = arit.graphcontainer()
        graphcodeweights15.update_calclibrary( self.code_library )
        graphcodeweights15.update_edgelibrary( self.edge_library )
        graphcodeweights15.createcode_with_graph( self.testgraph_weights15 )
        graphcodeweights15.cycle()
        outputgraph = graphcodeweights15.transferdatatograph()
        self.assertEqual( outputgraph.nodes( data=True )['2']["aout"], 1.5 )


if __name__=="__main__":
    unittest.main()
