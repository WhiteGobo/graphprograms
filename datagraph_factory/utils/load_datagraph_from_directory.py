from ..datagraph import DATATYPE
from ..constants import BLUEPRINT_FILENAME

def load_datagraph_from_directory( folderpath ):
    blueprint_file = os.path.join( folderpath, BLUEPRINT_FILENAME )
    mydatagraph = load_datagraph_blueprint( blueprint_file )
    loadable_datanodes = [ nodename for nodename in mydatagraph.nodes() \
                            if mydatagraph.nodes[nodename][DATATYPE].saveable ]
    #mydata = dict()
    mydata = mydatagraph
    for nodename in loadable_datanodes:
        datafile = os.path.join( folderpath, nodename )
        try:
            tmpdata = mydatagraph.nodes[node][DATATYPE].load_from( datafile, \
                                                            add_suffix=True )
            mydata[ nodename ] = tmpdata
        except FileNotFoundError:
            pass
    return mydata
