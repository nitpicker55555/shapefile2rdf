from rdflib import Graph, Literal, URIRef
from rdflib.namespace import XSD
def repair():
    import re

    def modify_ttl_file(input_path, output_path):
        with open(input_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # 匹配所有geo:asWKT的字面值并加上数据类型
        modified_content = re.sub(
            r'(geo:asWKT\s+")([^"]+)(")',
            r'\1\2\3^^<http://www.opengis.net/ont/geosparql#wktLiteral>',
            content
        )

        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(modified_content)

    # 修改文件的路径
    input_path = r"C:\Users\Morning\Desktop\hiwi\ttl_query\osm_land_use.ttl"
    output_path = r'C:\Users\Morning\Desktop\hiwi\ttl_query\modified_osm.ttl'

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


repair_polygon()