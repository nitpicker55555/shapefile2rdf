from geo_functions import *
a=time.time()
def residential_near_swamp():
    set_bounding_box("munich ismaning")
    id1=(ids_of_type('land_use', 'residential'))
    #
    id2 = (ids_of_type('buildings', 'building'))
    id_soil = (ids_of_type('http://example.com/soil', 'all'))
    # id3=geo_calculate(id1,id2,'buffer',10)
    # 65c, 66b, 73c, 73f, 74
    # 75, 75c,79,61a
    # ['77','78','78a']
    (geo_calculate(id2, id_soil, 'contains'))
def buildings_in_forest():
    set_bounding_box("munich ismaning")
    # id1=(ids_of_type('land_use', 'farmland'))
    #
    id2 = (ids_of_type('buildings', 'building'))
    id_soil = (ids_of_type('http://example.com/soil', 'all'))
    # id3=geo_calculate(id1,id2,'buffer',10)
    # 65c, 66b, 73c, 73f, 74
    # 75, 75c,79,61a
    # ['77','78','78a']
    print(geo_calculate(id2, id_soil, 'contains'))
def buildings_in_farmland_soil_type():
    set_bounding_box("munich ismaning")
    # id1=(ids_of_type('land_use', 'farmland'))
    #
    id2 = (ids_of_type('buildings', 'building'))
    id_soil = (ids_of_type('http://example.com/soil', 'all'))
    # id3=geo_calculate(id1,id2,'buffer',10)
    # 65c, 66b, 73c, 73f, 74
    # 75, 75c,79,61a
    # ['77','78','78a']
    print(geo_calculate(id2, id_soil, 'contains'))
def farmland_in_wrong_soil_type():
    set_bounding_box("munich ismaning")
    # id1=(ids_of_type('land_use', 'farmland'))
    #
    id2 = (ids_of_type('buildings', 'building'))
    id_soil = (ids_of_type('http://example.com/soil', 'all'))
    # id3=geo_calculate(id1,id2,'buffer',10)
    # 65c, 66b, 73c, 73f, 74
    # 75, 75c,79,61a
    # ['77','78','78a']
    print(geo_calculate(id2, id_soil, 'contains'))
def buildings_in_wrong_soil_type():
    set_bounding_box("munich ismaning")
    # id1=(ids_of_type('land_use', 'farmland'))
    #
    id2 = (ids_of_type('buildings', 'building'))
    id_soil = (ids_of_type('http://example.com/soil', 'all'))
    # id3=geo_calculate(id1,id2,'buffer',10)
    # 65c, 66b, 73c, 73f, 74
    # 75, 75c,79,61a
    # ['77','78','78a']
    print(geo_calculate(id2, id_soil, 'contains'))

# print(types_of_graph('http://example.com/landuse'))
# ['meadow', 'park', 'forest', 'farmland', 'farmyard', 'residential', 'grass', 'scrub', 'recreation_ground', 'industrial', 'commercial', 'allotments', 'retail', 'nature_reserve', 'cemetery', 'quarry', 'orchard', 'heath', 'military', 'vineyard']

set_bounding_box("munich ismaning")
# id1=(ids_of_type('land_use', 'farmland'))
#
id2=(ids_of_type('buildings', 'building'))
id_soil=(ids_of_type('http://example.com/soil','all'))
# id3=geo_calculate(id1,id2,'buffer',10)
#65c, 66b, 73c, 73f, 74
# 75, 75c,79,61a
# ['77','78','78a']
print(geo_calculate(id2, id_soil, 'contains'))
print(time.time()-a)