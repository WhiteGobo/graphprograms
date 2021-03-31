dutyname_to_knot_dict = {}

def add( myclass ):
    for dutyname in myclass.dutynames:
        possiblelist = dutyname_to_knot_dict.setdefault( dutyname, list() )
        possiblelist.append( myclass )
    #automation if its leaf or something else
    pass

def list_dutynames():
    pass

def dutyname_to_constructed_knots( dutyname ):
    pass


