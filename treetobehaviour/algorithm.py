def create_construction_instruction_to_innerknot( innerknot_class ):
    asdlist = []
    for dutyname in innerknot_class.branchdutylist:
        asdlist.append( possibledutyname_to_constructed_knots() )
    usedlist = [ knotlist[0] for knotlist in asdlist ]
    # here the call method is constructed


def myalgo( innerknot ):
    pass
