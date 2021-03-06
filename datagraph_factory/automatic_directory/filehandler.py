import os.path
import os
import inspect
import networkx as netx
from .. import utils
from ..datagraph import datagraph, datatype, edgetype
from ..constants import \
        DATAGRAPH_DATATYPE as DATATYPE, \
        DATAGRAPH_EDGETYPE as EDGETYPE, \
        DATAGRAPH_CONTAINED_DATA as CONTAINED_DATA, \
        BLUEPRINT_FILENAME as SAVENAME
import logging
logger = logging.getLogger( __name__ )

def save_graph( mydatagraph, directory_path, used_modules, forcenew=False ):
    _check_and_create_save_graph( mydatagraph, directory_path, forcenew )
    #_check_datagraph( mydatagraph )
    datatype_to_name, edgetype_to_name = _create_dict_type_to_name(used_modules)
    savegraph = _create_datagraph_blueprint( mydatagraph, datatype_to_name, \
                                                        edgetype_to_name )
    rootname = ".".join( (SAVENAME, "xml") )
    netx.write_graphml( savegraph, os.path.join( directory_path, rootname ))

    for node, data in mydatagraph.nodes( data=True ):
        if data[ DATATYPE ].saveable:
            try:
                tmpfilepath = os.path.join( directory_path, node )
                data[ CONTAINED_DATA ].save_as( tmpfilepath )
            except AttributeError as err: #catch datatype not having save_as
                #raise err
                logger.debug( f"{node} cant be saved" + str(err.args) )
            except KeyError: #catch if no data exists
                logger.debug( f"{node} has no data" )

def load_graph( directory_path, used_modules ):
    rootname = ".".join( (SAVENAME, "xml") )
    savegraph = netx.read_graphml( os.path.join( directory_path, rootname ),\
                                        force_multigraph=True )
    name_to_datatype, name_to_edgetype =_create_dict_name_to_type(used_modules)
    mydatagraph = _load_datagraph_from_blueprint( savegraph, name_to_datatype,\
                                                            name_to_edgetype )
    for node, data in mydatagraph.nodes( data=True ):
        if data[ DATATYPE ].saveable:
            tmpfilepath = os.path.join( directory_path, node )
            try:
                data[ CONTAINED_DATA ] = data[ DATATYPE ]\
                                        .load_from( tmpfilepath )
            except AttributeError: #g isnt there
                pass
            except TypeError as err:
                raise TypeError( "make sure load_from is decorated "\
                                "as classmethod and uses only 'cls'"\
                                "and 'filepath' as arguments" ) from err
    return mydatagraph


def _create_datagraph_blueprint( mydatagraph, datatype_to_name, \
                                                edgetype_to_name ):
    savegraph = netx.MultiDiGraph()
    for nodename, data in mydatagraph.nodes( data=True ):
        datatype_id = datatype_to_name[ data[ DATATYPE ] ]
        savegraph.add_node( nodename, **{ DATATYPE: datatype_id } )
    for edge_in, edge_out, data in mydatagraph.edges( data=True ):
        edgetype_id = edgetype_to_name[ data[EDGETYPE] ]
        savegraph.add_edge( edge_in, edge_out, **{ EDGETYPE: edgetype_id })
    return savegraph


def _load_datagraph_from_blueprint( savegraph, name_to_datatype, \
                                                name_to_edgetype ):
    if type( savegraph ) != netx.MultiDiGraph:
        raise Exception( "Error in program. "\
                        "savegraph must be 'networkx.MultiDiGraph'" )
    mydatagraph = datagraph()
    for nodename, data in savegraph.nodes( data=True ):
        tmpdatatype = name_to_datatype[ data[ DATATYPE ] ]
        mydatagraph.add_node( nodename, tmpdatatype )
    for edge_in, edge_out, data in savegraph.edges( data=True ):
        tmpedgetype = name_to_edgetype[ data[ EDGETYPE ] ]
        mydatagraph.add_edge( edge_in, edge_out, **{EDGETYPE: tmpedgetype})
    return mydatagraph


def _create_dict_name_to_type( used_modules ):
    for mod in used_modules:
        if not inspect.ismodule( mod ):
            raise TypeError( mod, "'used_modules' must be list of modules" )
    mydatatypes, myedgetypes = dict(), dict()
    for mod in used_modules:
        tmpdatatypes, tmpedgetypes, fact_leafs, conc_leafs \
                = utils.get_all_datatypes( mod )
        del( fact_leafs, conc_leafs )
        mydatatypes.update( tmpdatatypes )
        myedgetypes.update( tmpedgetypes )
        del( tmpdatatypes, tmpedgetypes )
    return mydatatypes, myedgetypes


def _create_dict_type_to_name( used_modules ):
    mydatatypes, myedgetypes = _create_dict_name_to_type( used_modules )
    datatype_to_stringidentifier = { value:key \
                                    for key, value in mydatatypes.items() }
    edgetype_to_stringidentifier = { value:key \
                                    for key, value in myedgetypes.items() }
    return datatype_to_stringidentifier, edgetype_to_stringidentifier


def _check_and_create_save_graph( mydatagraph, directory_path, createnew ):
    if False == createnew:
        if not os.path.exists( directory_path ):
            os.mkdir( directory_path )
    if not os.path.isdir( directory_path ):
        raise Exception("Invalid directory path")
