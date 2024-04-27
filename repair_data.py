import os
import re
from pyproj import Proj, Transformer
import shapely
from pyproj import Transformer
import re
import shapely.wkt
from shapely.ops import transform as shapely_transform
from tqdm import tqdm
def repair(input_path,output_path=None):
    if output_path==None:
        output_path=input_path.replace(".ttl","_repaired.ttl")

    import re

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


    # 将修改后的图保存到文件
    # g.serialize(destination="C:\\Users\\Morning\\Desktop\\hiwi\\ttl_query\\modified_shape_file.ttl", format="turtle")
def crs_transfer(input_file_path,output_file_path=None):

    from functools import partial
    if output_file_path==None:
        output_file_path=os.path.dirname(input_file_path)+"\\"+os.path.basename(input_file_path).replace(".ttl","_4326.ttl")

    def transform_wkt(wkt, transformer):
        """转换WKT字符串的坐标系"""
        geometry = shapely.wkt.loads(wkt)
        transformed_geometry = shapely_transform(transformer.transform, geometry)
        return transformed_geometry.wkt

    def main(input_file, output_file):
        # 设置源和目标坐标系
        transformer = Transformer.from_proj(
            Proj(init='epsg:25832'),  # ETRS89 / UTM zone 32N
            Proj(init='epsg:4326')  # WGS 84
        )

        # 读取文件
        with open(input_file, 'r') as file:
            content = file.read()

        # 查找所有WKT字符串
        wkt_pattern = r'geo:asWKT\s+"([^"]+)"\^\^\<http://www\.opengis\.net/ont/geosparql\#wktLiteral\>'
        # wkt_pattern = r'POLYGON \(\((.*?)\)\)'
        wkt_strings = re.findall(wkt_pattern, content)

        # 转换WKT字符串
        for i, wkt in tqdm(enumerate(wkt_strings),total=len(wkt_strings)):
            transformed_wkt = transform_wkt(wkt, transformer)
            content = content.replace(wkt, transformed_wkt)
            # print(f'Processed {i + 1}/{len(wkt_strings)} geometries')

        # 写入新文件
        with open(output_file, 'w') as file:
            file.write(content)
        print('Transformation complete. Output saved to:', output_file)

    main(input_file_path, output_file_path)

    # # 运行脚本
    # input_path = r"C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\soil_modified.ttl"
    # output_path = r"C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\soil_modified.ttl"

def add_index():
    import re

    def main(input_file, output_file):
        # 设置源和目标坐标系

        # 读取文件
        with open(input_file, 'r') as file:
            content = file.read()

        # 查找所有主语和对应的WKT字符串
        pattern = r'(<http://example\.org/data/\d+>)\s+(.*?geo:asWKT\s+"([^"]+)"\^\^\<http://www\.opengis\.net/ont/geosparql\#wktLiteral\>)'
        matches = re.findall(pattern, content, re.DOTALL)

        # 转换WKT字符串并添加新的谓语-宾语对
        for i, (subject, wkt_data, wkt) in enumerate(matches):

            soil_id_statement = f';\n    ns1:soil_id "{i + 1}" '
            content = content.replace(wkt_data, wkt_data + soil_id_statement)
            print(f'Processed {i + 1}/{len(matches)} geometries')

        # 写入新文件
        with open(output_file, 'w') as file:
            file.write(content)
        print('Transformation complete. Output saved to:', output_file)

    # 运行脚本
    input_file_path = r'C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\modified_Moore_Bayern_4326.ttl'  # 替换为你的输入文件路径
    output_file_path = r'C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\modified_Moore_Bayern_4326_index.ttl'  # 替换为你的输出文件路径
    main(input_file_path, output_file_path)


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


    file_path = r"C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\Moore_Bayern.ttl"
    output_path = r"C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\modified_Moore_Bayern.ttl"

    g = read_ttl(file_path)
    geometries = extract_geometries(g)
    repaired_geometries = repair_geometries(geometries)
    g = update_ttl(g, repaired_geometries)
    save_ttl(g, output_path)

    print(f"Fixed TTL file saved at: {output_path}")
def re_test():
    geo_str="""
    
<http://example.org/data/1> ns1:diff 99 ;
    ns1:leg_einh "101" ;
    ns1:leg_nr 10100 ;
    ns1:leg_text "101: Vorherrschend (Para-)Rendzina und Braunerde, gering verbreitet Terra fusca und Pseudogley aus Bunten Trümmermassen mit weitem Bodenartenspektrum, verbreitet mit flacher Deckschicht aus Schluff bis Lehm" ;
    ns1:objectid 2 ;
    ns1:shape_area 2.123902e+05 ;
    ns1:shape_leng 2.294442e+03 ;
    geo:asWKT "POLYGON ((600809.7873 5387243.8224, 600852.5679000001 5387235.4386, 600890.0143999998 5387237.098099999, 600960.0751999998 5387228.1612, 600985.7065000003 5387218.6655, 600999.2445 5387211.4452, 601042.9713000003 5387166.2741, 601060.0088 5387146.3747000005, 601081.3664999995 5387131.084100001, 601104.4604000002 5387120.926000001, 601162.7632999998 5387078.7037, 601165.1974 5387034.285, 601156.7756000003 5387016.3233, 601138.2253999999 5386996.7754, 601113.2049000002 5386982.787699999, 601081.0295000002 5386974.270500001, 601041.7812999999 5386970.727, 600949.4879000001 5386979.040200001, 600836.6112000002 5387021.117799999, 600799.0773 5387023.2685, 600646.4644999998 5387009.0165, 600600.4330000002 5386995.1405, 600516.3081999999 5386983.330700001, 600485.8174999999 5386984.4454, 600423.7287999997 5387003.698999999, 600360.4029000001 5387046.4739, 600341.6810999997 5387056.7415, 600323.7576000001 5387062.601500001, 600296.9897999996 5387067.613600001, 600212.5767999999 5387064.732899999, 600188.2812000001 5387070.4673, 600168.2726999996 5387083.2477, 600155.7214000002 5387101.947699999, 600147.5908000004 5387122.6974, 600142.4474999998 5387148.5658, 600141.8883999996 5387170.738500001, 600157.7515000002 5387193.431500001, 600182.9216 5387203.611500001, 600216.3477999996 5387212.1152, 600301.6988000004 5387224.536, 600441.6968999999 5387238.417400001, 600478.9578 5387246.384299999, 600512.5832000002 5387246.643200001, 600532.8422999997 5387249.7530000005, 600599.3816 5387254.056700001, 600690.4398999996 5387269.2028, 600727.1506000003 5387272.083799999, 600755.9051000001 5387265.8368999995, 600777.7369999997 5387257.5671999995, 600809.7873 5387243.8224))"^^<http://www.opengis.net/ont/geosparql#wktLiteral> .

<http://example.org/data/10> ns1:diff 99 ;
    ns1:leg_einh "101" ;
    ns1:leg_nr 10100 ;
    ns1:leg_text "101: Vorherrschend (Para-)Rendzina und Braunerde, gering verbreitet Terra fusca und Pseudogley aus Bunten Trümmermassen mit weitem Bodenartenspektrum, verbreitet mit flacher Deckschicht aus Schluff bis Lehm" ;
    ns1:objectid 11 ;
    ns1:shape_area 3.773038e+04 ;
    ns1:shape_leng 7.186545e+02 ;
    geo:asWKT "POLYGON ((615614.3202999998 5390902.6777, 615579.7138999999 5390892.3125, 615531.6117000002 5390894.4223, 615509.2440999998 5390903.547, 615493.2395000001 5390928.929300001, 615472.7618000004 5391017.1642, 615472.1328999996 5391033.1468, 615506.7555 5391068.5241, 615550.7215999998 5391095.264799999, 615576.2202000003 5391108.2733, 615645.8256000001 5391119.014900001, 615683.4512 5391103.4871, 615703.8048999999 5391069.2718, 615697.9524999997 5391040.0284, 615649.0608000001 5390935.0583999995, 615614.3202999998 5390902.6777))"^^<http://www.opengis.net/ont/geosparql#wktLiteral> .    """
    wkt_pattern = r'geo:asWKT\s+"([^"]+)"\^\^\<http://www\.opengis\.net/ont/geosparql\#wktLiteral\>'
    # wkt_pattern = r'POLYGON \(\((.*?)\)\)'
    wkt_strings = re.findall(wkt_pattern, geo_str)
    # print(wkt_strings)
    transformer = Transformer.from_proj(
        Proj(init='epsg:25832'),  # ETRS89 / UTM zone 32N
        Proj(init='epsg:4326')  # WGS 84
    )

    def transform_wkt(wkt, transformer):
        """转换WKT字符串的坐标系"""
        geometry = shapely.wkt.loads(wkt)
        transformed_geometry = shapely_transform(transformer.transform, geometry)
        return transformed_geometry.wkt

    # 转换WKT字符串
    for i, wkt in enumerate(wkt_strings):
        transformed_wkt = transform_wkt(wkt, transformer)
        geo_str = geo_str.replace(wkt, transformed_wkt)
        print(geo_str,'content')
        print(f'Processed {i + 1}/{len(wkt_strings)} geometries')


# re_test()

input_path = r"C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\landuse.ttl"
output_path = r"C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\landuse_repaired.ttl"

repair(input_path)

# add_index()
"""
'MULTIPOLYGON (((11.2850209 48.1052416, 11.2851058 48.1052771, 11.2850297 48.1053693, 11.2855394 48.1055749, 11.2855641 48.1055548, 11.2855907 48.1055619, 11.285527 48.1056328, 11.2858048 48.1057486, 11.2860366 48.1054898, 11.2857606 48.1053728, 11.285865 48.1052416, 11.2859128 48.1052369, 11.2859322 48.1052783, 11.2859641 48.1052936, 11.2859835 48.1052712, 11.2860968 48.1052464, 11.2860791 48.1052109, 11.2861375 48.1051483, 11.2862745 48.1051258, 11.2863123 48.1052197, 11.285974 48.1056075, 11.2859889 48.1056585, 11.2860515 48.1056493, 11.2862221 48.1057169, 11.2862569 48.105677, 11.2860676 48.1056019, 11.2863783 48.1052529, 11.286645 48.1053587, 11.2867156 48.1052635, 11.286682 48.1051961, 11.2865422 48.1052186, 11.2863278 48.1051356, 11.2863189 48.1051142, 11.286297 48.105118, 11.286259 48.1050144, 11.286397 48.1048566, 11.2864684 48.1047749, 11.286509 48.1047647, 11.2865634 48.1046649, 11.2866592 48.1045623, 11.2864656 48.1044824, 11.2865705 48.1043721, 11.2864773 48.1043258, 11.2864242 48.1043778, 11.2862401 48.1044121, 11.2863003 48.1043235, 11.2862366 48.1042845, 11.2860986 48.1042514, 11.2860207 48.1043412, 11.2861216 48.1043826, 11.2861039 48.1043991, 11.2859782 48.1043518, 11.2859163 48.1043601, 11.285796 48.1044842, 11.2858119 48.1045267, 11.2859163 48.1045669, 11.2859004 48.1045894, 11.2858756 48.104574, 11.2858172 48.1045835, 11.2856969 48.1047146, 11.2857128 48.1047489, 11.2857411 48.1047607, 11.2857358 48.1048103, 11.2857659 48.1048281, 11.2856615 48.1049462, 11.2856279 48.1049368, 11.2854633 48.1051424, 11.2855482 48.1051743, 11.2855659 48.1051589, 11.2855907 48.1051696, 11.2855783 48.1051861, 11.285688 48.1052286, 11.2858048 48.1051022, 11.2858561 48.1051258, 11.2856509 48.1053622, 11.2851235 48.1051507, 11.2850209 48.1052416)] [(11.2858528 48.1050336, 11.2859626 48.1049059, 11.2860708 48.1049474, 11.2859609 48.1050751, 11.2858528 48.1050336)] [(11.2860136 48.1048521, 11.2861395 48.1047076, 11.2862486 48.10475, 11.2861227 48.1048945, 11.2860136 48.1048521)),((11.2853242 48.1057898, 11.2856539 48.1059179, 11.2857658 48.1057895, 11.2854361 48.1056613, 11.2853242 48.1057898)),((11.2858193 48.105998, 11.2859027 48.1062284, 11.2859347 48.1062232, 11.2859424 48.1062446, 11.2860264 48.106231, 11.2860181 48.1062082, 11.2860988 48.1061952, 11.2860021 48.1059283, 11.2858935 48.1059458, 11.2859072 48.1059838, 11.2858193 48.105998)),((11.2859205 48.1058029, 11.2862443 48.1059366, 11.2863617 48.1058099, 11.2860378 48.1056762, 11.2859205 48.1058029)))'
"""