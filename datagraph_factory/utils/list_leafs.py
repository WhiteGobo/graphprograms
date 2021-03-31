import inspect
import itertools
from ..datagraph import datatype, edgetype
from ..processes import factory_leaf, conclusion_leaf


#def list_submodules( module ):
#    for submodule in iter_modules( module.__path__ ):
#        print( submodule.name )


def get_all_datatypes( module ):
    prefixes = { module: module.__name__ }
    tmp_modulelist = set([ module, ])
    visited_modules = set()
    found_datatypes = dict()
    found_conclusionleafs = dict()
    found_factoryleafs = dict()
    found_edgetypes = dict()
    while tmp_modulelist:
        cur_module = tmp_modulelist.pop()
        visited_modules.add( cur_module )
        for member in inspect.getmembers( cur_module ):
            curprefix = prefixes[ cur_module ]
            if inspect.ismodule( member[1] ):
                foundmodule = member[1]
                modulename_as_imported = member[0]
                prefixes[ foundmodule ] = ".".join(( curprefix, \
                                                    modulename_as_imported ))
                if foundmodule not in visited_modules:
                    tmp_modulelist.add( foundmodule )
            elif inspect.isclass( member[1] ):
                if issubclass( member[1], datatype ) and (member[1]!=datatype):
                    pathto = ".".join((curprefix, member[0]))
                    found_datatypes[ pathto ] = member[1]
                    del( pathto )
            elif isinstance( member[1], edgetype ):
                pathto = ".".join((curprefix, member[0]))
                found_edgetypes[ pathto ] = member[1]
                del( pathto )
            elif isinstance( member[1], conclusion_leaf ):
                pathto = ".".join((curprefix, member[0]))
                found_conclusionleafs[ pathto ] = member[ 1 ]
                del( pathto )
            elif isinstance( member[1], factory_leaf ):
                pathto = ".".join((curprefix, member[0]))
                found_factoryleafs[ pathto ] = member[ 1 ]
                del( pathto )

    return found_datatypes, found_edgetypes, found_factoryleafs, \
            found_conclusionleafs

def list_available_edges_with_datatype( datatype, module, seconddatatype=None ):
    dtypes, found_edgetypes, fact_leafs, cc_leafs = get_all_datatypes( module )
    edgetype_with_datatypepair_set = set()
    for edge in found_edgetypes.values():
        datatypepairs = edge.get_source_target_pair_function()
        for datatype_pair in datatypepairs:
            if datatype in datatype_pair:
                edgetype_with_datatypepair_set.add( (edge, datatype_pair) )
    if seconddatatype != None:
        edgetype_with_datatypepair_set = [ (edge, datatype_pair) \
                    for edge, datatype_pair in edgetype_with_datatypepair_set \
                    if seconddatatype in datatype_pair ]
    return edgetype_with_datatypepair_set
