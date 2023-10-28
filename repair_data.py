from rdflib import Graph, Literal, URIRef
from rdflib.namespace import XSD
def repair():
    import re

    def modify_ttl_file(input_path, output_path):
        with open(input_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # 匹配所有geo:asWKT的字面值并加上数据类型
        output_str = re.sub(
            r'(geo:asWKT "POLYGON )\[\[(.+?)\]\]"',
            lambda m: m.group(1) + '(' + m.group(2).replace(') (',
                                                            ', ').replace(')] [(','),(') + ')"^^<http://www.opengis.net/ont/geosparql#wktLiteral>',
            content
        )
        output_str = re.sub(
            r'(geo:asWKT "MULTIPOLYGON )\[\[\[(.+?)\]\]\]"',
            lambda m: m.group(1) + '((' + m.group(2).replace(') (', ', ').replace(')]] [[(',
                                                                                  ')),((').replace(')] [(','),(')  + '))"^^<http://www.opengis.net/ont/geosparql#wktLiteral>',
            output_str
        )
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(output_str)

    # 修改文件的路径
    input_path = r"C:\Users\Morning\Desktop\hiwi\ttl_query\osm_land_use2.ttl"
    output_path = r'C:\Users\Morning\Desktop\hiwi\ttl_query\modified_osm2.ttl'

    modify_ttl_file(input_path, output_path)

    # 将修改后的图保存到文件
    # g.serialize(destination="C:\\Users\\Morning\\Desktop\\hiwi\\ttl_query\\modified_shape_file.ttl", format="turtle")
def analyse():
    from rdflib import Graph, Literal, URIRef

    # 加载Turtle文件到图中
    g = Graph()
    g.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\path_to_output.ttl", format="turtle")

    # 定义要检查的数据类型URI
    datatype_to_check = URIRef("http://www.w3.org/2001/XMLSchema#string")

    # 检查指定数据类型的字面量是否存在
    found = False
    for s, p, o in g.triples((None, None, None)):
        if isinstance(o, Literal) and o.datatype == datatype_to_check:
            found = True
            break

    if found:
        print(f"Data type {datatype_to_check} found!")
    else:
        print(f"Data type {datatype_to_check} not found.")
def repair_polygon():
    from rdflib import Graph, Literal
    from rdflib.namespace import Namespace
    from shapely.geometry import shape, mapping
    from shapely.wkt import loads, dumps
    import geopandas as gpd
    import json

    GEO = Namespace("http://www.opengis.net/ont/geosparql#")

    def read_ttl(file_path):
        g = Graph()
        g.parse(file_path, format="turtle")
        return g

    def extract_geometries(graph):
        geometries = []
        for s, p, o in graph.triples((None, GEO.asWKT, None)):
            try:
                # Attempt to load the WKT geometry
                geom = loads(str(o.value))
                geometries.append((s, geom))
            except Exception as e:
                # Log the problematic WKT string for further inspection
                print(f"Error parsing WKT for subject {s}: {o.value}")
        return geometries

    def repair_geometries(geometries):
        repaired = []
        for s, geom in geometries:
            if not geom.is_valid:
                geom = geom.buffer(0)
            repaired.append((s, geom))
        return repaired

    def update_ttl(g, repaired_geometries):
        for s, geom in repaired_geometries:
            g.set((s, GEO.asWKT, Literal(dumps(geom))))
        return g

    def save_ttl(g, output_path):
        g.serialize(destination=output_path, format='turtle')


    file_path = r"C:\Users\Morning\Desktop\hiwi\ttl_query\modified_shape_file.ttl"
    output_path = r"C:\Users\Morning\Desktop\hiwi\ttl_query\modified_shape_file_poly.ttl"

    g = read_ttl(file_path)
    geometries = extract_geometries(g)
    repaired_geometries = repair_geometries(geometries)
    g = update_ttl(g, repaired_geometries)
    save_ttl(g, output_path)

    print(f"Fixed TTL file saved at: {output_path}")


repair()
"""
'MULTIPOLYGON (((11.2850209 48.1052416, 11.2851058 48.1052771, 11.2850297 48.1053693, 11.2855394 48.1055749, 11.2855641 48.1055548, 11.2855907 48.1055619, 11.285527 48.1056328, 11.2858048 48.1057486, 11.2860366 48.1054898, 11.2857606 48.1053728, 11.285865 48.1052416, 11.2859128 48.1052369, 11.2859322 48.1052783, 11.2859641 48.1052936, 11.2859835 48.1052712, 11.2860968 48.1052464, 11.2860791 48.1052109, 11.2861375 48.1051483, 11.2862745 48.1051258, 11.2863123 48.1052197, 11.285974 48.1056075, 11.2859889 48.1056585, 11.2860515 48.1056493, 11.2862221 48.1057169, 11.2862569 48.105677, 11.2860676 48.1056019, 11.2863783 48.1052529, 11.286645 48.1053587, 11.2867156 48.1052635, 11.286682 48.1051961, 11.2865422 48.1052186, 11.2863278 48.1051356, 11.2863189 48.1051142, 11.286297 48.105118, 11.286259 48.1050144, 11.286397 48.1048566, 11.2864684 48.1047749, 11.286509 48.1047647, 11.2865634 48.1046649, 11.2866592 48.1045623, 11.2864656 48.1044824, 11.2865705 48.1043721, 11.2864773 48.1043258, 11.2864242 48.1043778, 11.2862401 48.1044121, 11.2863003 48.1043235, 11.2862366 48.1042845, 11.2860986 48.1042514, 11.2860207 48.1043412, 11.2861216 48.1043826, 11.2861039 48.1043991, 11.2859782 48.1043518, 11.2859163 48.1043601, 11.285796 48.1044842, 11.2858119 48.1045267, 11.2859163 48.1045669, 11.2859004 48.1045894, 11.2858756 48.104574, 11.2858172 48.1045835, 11.2856969 48.1047146, 11.2857128 48.1047489, 11.2857411 48.1047607, 11.2857358 48.1048103, 11.2857659 48.1048281, 11.2856615 48.1049462, 11.2856279 48.1049368, 11.2854633 48.1051424, 11.2855482 48.1051743, 11.2855659 48.1051589, 11.2855907 48.1051696, 11.2855783 48.1051861, 11.285688 48.1052286, 11.2858048 48.1051022, 11.2858561 48.1051258, 11.2856509 48.1053622, 11.2851235 48.1051507, 11.2850209 48.1052416)] [(11.2858528 48.1050336, 11.2859626 48.1049059, 11.2860708 48.1049474, 11.2859609 48.1050751, 11.2858528 48.1050336)] [(11.2860136 48.1048521, 11.2861395 48.1047076, 11.2862486 48.10475, 11.2861227 48.1048945, 11.2860136 48.1048521)),((11.2853242 48.1057898, 11.2856539 48.1059179, 11.2857658 48.1057895, 11.2854361 48.1056613, 11.2853242 48.1057898)),((11.2858193 48.105998, 11.2859027 48.1062284, 11.2859347 48.1062232, 11.2859424 48.1062446, 11.2860264 48.106231, 11.2860181 48.1062082, 11.2860988 48.1061952, 11.2860021 48.1059283, 11.2858935 48.1059458, 11.2859072 48.1059838, 11.2858193 48.105998)),((11.2859205 48.1058029, 11.2862443 48.1059366, 11.2863617 48.1058099, 11.2860378 48.1056762, 11.2859205 48.1058029)))'
"""