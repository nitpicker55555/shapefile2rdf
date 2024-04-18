
import psycopg2
import time
from shapely.geometry import shape
import geopandas as gpd
from shapely.wkt import loads
from shapely.geometry import mapping
# from draw_geo import draw_geo_map
from SPARQLWrapper import SPARQLWrapper, JSON
from tqdm import tqdm
from bounding_box import find_boundbox
from shapely import wkb
from shapely import wkt
from itertools import islice
import copy
from shapely.geometry import base
globals_dict = {}
global_id_attribute={}
global_id_geo={}
# sparql = SPARQLWrapper("http://127.0.0.1:7200/repositories/osm_search")

conn_params = "dbname='osm_database' user='postgres' host='localhost' password='9417941'"
conn = psycopg2.connect(conn_params)
cur = conn.cursor()
def cur_action(query):
    try:
        rows = cur.execute(query)
        return rows
    except psycopg2.Error as e:
        cur.execute("ROLLBACK;")
        raise Exception(f"SQL error: {e}")


def set_bounding_box(region_name):
    if region_name!=None:
        globals_dict["bounding_box_region_name"] = region_name
        globals_dict['bounding_coordinates'], globals_dict['bounding_wkb'], response_str = find_boundbox(region_name)

        # print(wkb.loads(bytes.fromhex(globals_dict['bounding_wkb'])))

        geo_dict = {
                globals_dict["bounding_box_region_name"]: (wkb.loads(bytes.fromhex((globals_dict['bounding_wkb']))))}



        return {'geo_map':geo_dict}
    else:
        return None


def list_all_graph_name():
    """

    :return:目前所有的数据库
    {'graph': {'type': 'uri', 'value': 'http://example.com/buildings'}}
    """
    query = """
    SELECT DISTINCT ?graph
WHERE {
  GRAPH ?graph { ?s ?p ?o }
}

    """
    graph_list = []
    feed_back = ask_soil(query, "")
    for i in feed_back:
        graph_list.append(i['graph']['value'])
    return graph_list


def types_of_graph(graph_name):
    """

    :param graph_name: 需要查找的数据库
    :return: 输出数据库的所有type,不重复

PREFIX ns1: <http://example.org/property/>

SELECT DISTINCT ?fclass
WHERE {
  GRAPH <http://example.com/landuse> {
    ?entity ns1:fclass ?fclass .
  }
}


{'fclass': {'type': 'literal', 'value': 'building'}}
    """

    if "soil" not in graph_name:
        query = """
        PREFIX ns1: <http://example.org/property/>

        SELECT DISTINCT ?fclass
        WHERE {
          GRAPH <%s> {
            ?entity ns1:fclass ?fclass .
          }
        }

            """ % graph_name
    else:

        query = """
    PREFIX ns1: <http://example.org/property/>

    SELECT DISTINCT ?fclass
    WHERE {
      GRAPH <%s> {
        ?entity ns1:uebk25_l ?fclass .
      }
    }

        """ % graph_name
    type_list = []
    feed_back = ask_soil(query, graph_name)
    for i in feed_back:
        type_list.append(i['fclass']['value'])
    return type_list
def ids_of_attribute(graph_name, bounding_box_coordinats=None):
    if 'bounding_coordinates' in globals_dict:
        bounding_box_coordinats = globals_dict['bounding_coordinates']
        min_lat, max_lat, min_lon, max_lon = bounding_box_coordinats
    attributes_set = set()
    # if single_type=="building":

    # 定义边界框

    srid = 4326  # 假设使用WGS 84


    if graph_name=='soil':
        fclass='uebk25_l'
        graph_name='soilnoraml'
        srid=25832
    elif graph_name=="buildings":
        fclass='name'
    else:
        fclass='fclass'
    if bounding_box_coordinats is not None:
    # 执行查询
        bounding_query = f"""
        SELECT DISTINCT {fclass}
        FROM {graph_name}
        WHERE ST_Within(geom, ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat}, {srid}))
        """
    else:
        bounding_query = f"""
        SELECT DISTINCT {fclass} 
        FROM {graph_name}
        """
    # print(bounding_query)


    rows = cur_action(bounding_query)


    for row in rows:
        attributes_set.add(row[0])
    return attributes_set
def ids_of_type(graph_name, single_type, bounding_box_coordinats=None):


    """
    globals_dict["bounding_box_region_name"]=region_name
    globals_dict['bounding_coordinates'],globals_dict['bounding_wkb']=find_boundbox(region_name)

    """
    if 'bounding_coordinates' in globals_dict:
        bounding_box_coordinats = globals_dict['bounding_coordinates']
        min_lat, max_lat, min_lon, max_lon = bounding_box_coordinats
    if isinstance(single_type,set):
        single_type=list(single_type)
    if '..' not in graph_name:
    # if single_type=="building":

        # 定义边界框

        srid = 4326  # 假设使用WGS 84

        single_type = str(single_type)
        if '[' in single_type:

            single_type = single_type.replace("[", "(").replace("]", ")")

        else:
            single_type = f"{single_type}"

        if graph_name=='soil':
            fclass='uebk25_l'
            graph_name='soilnoraml'
            srid=25832
        elif graph_name=='buildings' and '(' in single_type:
            fclass='name'

        else:
            fclass='fclass'
        if bounding_box_coordinats is not None:
            if single_type!='all':
                if '(' in single_type:
                    fclass_row = f"AND {fclass} in {single_type};"
                else:
                    fclass_row=f"AND {fclass} = '{single_type}';"
            else:fclass_row=''
        # 执行查询
            bounding_query = f"""
            SELECT *
            FROM {graph_name}
            WHERE ST_Within(geom, ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat}, {srid}))
            %s
            """%fclass_row
        else:
            if single_type!='all':
                if '(' in single_type:
                    fclass_row = f"WHERE {fclass} in {single_type};"
                else:
                    fclass_row=f"WHERE {fclass} = '{single_type}';"
            else:fclass_row=''
            bounding_query = f"""
            SELECT * 
            FROM {graph_name}
            %s
            """%fclass_row
        # print(bounding_query)

        rows = cur_action(bounding_query)


        # 获取查询结果
        rows = cur.fetchall()
        result_dict = {}
        for row in rows:
            # result_dict[row[2] + "_" + row[3]+"_"+row[4]] = mapping(wkb.loads(bytes.fromhex(row[6])))
            if graph_name=='soilnoraml':
                result_dict['soil' + "_" + str(row[6]) + "_" + str(row[0])] = (wkb.loads(bytes.fromhex(row[-1]))) #result_dict _分割的前两位是展示在地图上的
                global_id_attribute['soil' + "_" + str(row[6]) + "_" + str(row[0])]=  str(row[6])

                """
                'Vorherrschend Anmoorgley und Moorgley, gering verbreitet Gley über Niedermoor, humusreicher Gley und Nassgley, teilweise degradiert'
                '66b: Fast ausschließlich Anmoorgley aus Lehm bis Schluff, selten Ton (See- oder Flusssediment); im Untergrund carbonathaltig'
                """
            else:
                global_id_attribute[graph_name+ "_" + str(row[2])+"_"+str(row[4])] =  str(row[2]+str(row[3]))
                result_dict[graph_name+ "_" + str(row[2])+"_"+str(row[4])] = (wkb.loads(bytes.fromhex(row[6])))
            # break
            global_id_geo.update(result_dict)
        feed_back=result_dict
    else:
        soil_dict = {
            '61a': '61a: Bodenkomplex: Vorherrschend Anmoorgley und Pseudogley, gering verbreitet Podsol aus (Kryo-)Sandschutt (Granit oder Gneis) über Sandschutt bis Sandgrus (Basislage, verfestigt)',
            '62c': '62c: Fast ausschließlich kalkhaltiger Anmoorgley aus Schluff bis Lehm (Flussmergel oder Alm) über tiefem Carbonatsandkies (Schotter)',
            '65c': '65c: Fast ausschließlich Anmoorgley, Niedermoorgley und Nassgley aus Lehmsand bis Lehm (Talsediment); im Untergrund carbonathaltig',
            '66b': '66b: Fast ausschließlich Anmoorgley aus Lehm bis Schluff, selten Ton (See- oder Flusssediment); im Untergrund carbonathaltig',
            '67': '67: Fast ausschließlich Gley über Niedermoor und Niedermoor-Gley aus Wechsellagerungen von (Carbonat-)Lehm bis Schluff und Torf über Carbonatsandkies (Schotter)',
            '72c': '72c: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Sand (Talsediment)',
            '72f': '72f: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Sand (Substrate unterschiedlicher Herkunft); außerhalb rezenter Talbereiche',
            '64c': '64c: Fast ausschließlich kalkhaltiger Anmoorgley aus Schluff bis Lehm (Flussmergel) über Carbonatsandkies (Schotter), gering verbreitet aus Talsediment',
            '73c': '73c: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Schluff bis Lehm, selten aus Ton (Talsediment)',
            '73f': '73f: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Schluff bis Lehm, selten aus Ton (Substrate unterschiedlicher Herkunft); außerhalb rezenter Talbereiche',
            '74': '74: Fast ausschließlich Gley über Niedermoor und Niedermoor-Gley aus Wechsellagerungen von Lehm und Torf über Sand bis Lehm (Talsediment)',
            '75': '75: Fast ausschließlich Moorgley, Anmoorgley und Oxigley aus Lehmgrus bis Sandgrus (Talsediment)',
            '75c': '75c: Bodenkomplex: Vorherrschend Gley und Anmoorgley, gering verbreitet Moorgley aus (Kryo-)Sandschutt (Granit oder Gneis), selten Niedermoor aus Torf',
            '77': '77: Fast ausschließlich Kalkniedermoor und Kalkerdniedermoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum; verbreitet mit Wiesenkalk durchsetzt',
            '78': '78: Vorherrschend Niedermoor und Erdniedermoor, gering verbreitet Übergangsmoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum',
            '78a': '78a: Fast ausschließlich Niedermoor und Übergangsmoor aus Torf über kristallinen Substraten mit weitem Bodenartenspektrum',
            '79': '79: Fast ausschließlich Hochmoor und Erdhochmoor aus Torf',
            '80a': '80a: Fast ausschließlich (flacher) Gley über Niedermoor aus (flachen) mineralischen Ablagerungen mit weitem Bodenartenspektrum über Torf, vergesellschaftet mit (Kalk)Erdniedermoor',
            '80b': '80b: Überwiegend (Gley-)Rendzina und kalkhaltiger Gley über Niedermoor aus Alm über Torf, engräumig vergesellschaftet mit Kalkniedermoor und Kalkerdniedermoor aus Torf',
            '850': '850: Bodenkomplex: Humusgleye, Moorgleye, Anmoorgleye und Niedermoore aus alpinen Substraten mit weitem Bodenartenspektrum'}
        if isinstance(single_type, list):
            replace_list = []
            for i in single_type:
                if ":" in i:
                    i = i.split(":")[0]
                if i in soil_dict:
                    replace_list.append(soil_dict[i])
                else:
                    replace_list.append(i)
            if replace_list!=[]:
                single_type = replace_list
        else:
            if ":" in single_type:
                single_type = single_type.split(":")[0]
                single_type=soil_dict[single_type]
        single_type = str(single_type)
        if '[' in single_type:
            single_type = single_type.replace("[", "(").replace("]", ")")

        else:
            single_type = f"('{single_type}')"
        """
    
        :param single_type: 需要查找的type
        :return: 返回id列表
        {
        'osmId': {'type': 'literal', 'value': '18825773'},
        'wkt': {
            'datatype': 'http://www.opengis.net/ont/geosparql#wktLiteral',
            'type': 'literal', 'value': 'POLYGON ((11.6016729 48.0834...
            }
        }
        """

        """
        PREFIX ns1: <http://example.org/property/>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
    PREFIX sf: <http://www.opengis.net/ont/sf#>
    
    SELECT ?osmId ?wkt
    WHERE {
      GRAPH <http://example.com/buildings> {
        ?entity ns1:fclass "building" .
        ?entity ns1:osm_id ?osmId .
        ?entity geo:asWKT ?wkt .
      }
    
      # 创建一个边界框的多边形，用指定的坐标
      BIND("POLYGON((11.5971976 48.2168632, 11.6851890 48.2168632, 11.6851890 48.2732260, 11.5971976 48.2732260, 11.5971976 48.2168632))"^^geo:wktLiteral AS ?bbox) .
    
      # 检查元素是否与边界框相交
      FILTER(geof:sfIntersects(?wkt, ?bbox))
    }
    
        """
        fclass = "fclass"
        osm_id = "osm_id"
        bounding_box_str = ""
        building_type = ""
        if bounding_box_coordinats is not None:
            min_lat, max_lat, min_lon, max_lon = bounding_box_coordinats
            polygon_wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
            bounding_box_str = f'BIND("{polygon_wkt}"^^geo:wktLiteral AS ?bbox) .'
            bounding_box_str += "\nFILTER(geof:sfIntersects(?wkt, ?bbox))"
        if "soil" in graph_name:
            fclass = 'uebk25_l'
            osm_id = 'soil_id'
        if "building" in graph_name:
            building_type = "\n?entity ns1:type ?type ."
        if "all" not in single_type:
            fclass_filter = f'\nFILTER(?fclass IN {single_type})'
        else:
            fclass_filter = ""
        query = """
    PREFIX ns1: <http://example.org/property/>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
        SELECT ?osmId ?wkt ?fclass ?type
        WHERE {
          GRAPH <%s> {
            ?entity ns1:%s ?fclass .
            ?entity ns1:%s ?osmId .
            %s
            ?entity geo:asWKT ?wkt .
            %s
          }
            # 创建一个边界框的多边形，用指定的坐标
            %s
        }
    
    
            """ % (graph_name, fclass, osm_id, fclass_filter, building_type, bounding_box_str)
        print(query)
        feed_back = ask_soil(query, graph_name)
    print(len(feed_back))



    if "bounding_box_region_name" in globals_dict:
        geo_dict = {globals_dict["bounding_box_region_name"]:  (wkb.loads(bytes.fromhex((globals_dict['bounding_wkb']))))}
    else:
        geo_dict = {}

    geo_dict.update((feed_back))
    # html=draw_geo_map(geo_dict, "geo")
    # print(html)

    return {'id_list':feed_back,'geo_map':geo_dict}


def ask_soil(query, map):
    # SPARQL查询来提取所有的ns1:kategorie实体
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    # 执行查询并获取结果
    results = sparql.query().convert()

    # 遍历并打印结果
    result_dict = {}

    try:
        if results["results"]["bindings"][0]['wkt']:
            pass

        for result in results["results"]["bindings"]:
            # print(result)

            wkt = result['wkt']['value']
            osm_id = result['osmId']['value']
            fclass = result['fclass']['value']

            # 将WKT字符串转换为几何对象
            geometry = (loads(wkt))

            # 添加到列表
            if "type" in result:
                result_dict.update(
                    {map.split("/")[-1] + "_" + fclass + "/" + result['type']['value'] + "/_" + str(osm_id): geometry})
            else:
                result_dict.update({map.split("/")[-1] + "_" + fclass + "_" + str(osm_id): geometry})
        return result_dict
    except:
        result_list = []
        for result in results["results"]["bindings"]:
            result_list.append(result)
        # print(result_list)
        return result_list


def get_geo_via_id(graph_name, id):
    if "/" not in graph_name:
        graph_name = "http://example.com/" + graph_name
    if "_" in id:
        id = id.split("_")[-1]
    """

    :param graph_name:
    :param id:
    :return:
    """
    if "soil" not in graph_name:

        query = """
PREFIX ns1: <http://example.org/property/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
SELECT ?element ?wkt ?osmId 
WHERE {
    GRAPH <%s>{
        ?element ns1:osm_id ?osmId .
        FILTER(?osmId = "%s")
        ?element geo:asWKT ?wkt .
    }
}


    """ % (graph_name, id)
    else:
        query = """
PREFIX ns1: <http://example.org/property/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
SELECT ?element ?wkt ?osmId 
WHERE {
    GRAPH <%s>{
        ?element ns1:soil_id ?osmId .
        FILTER(?osmId = "%s")
        ?element geo:asWKT ?wkt .
    }
}


    """ % (graph_name, id)
    # print(query)
    feed_back = ask_soil(query, graph_name)
    return feed_back
def geojson_to_wkt(geojson_dict):
    """
    Convert a dictionary of GeoJSON objects to a list of WKT strings.

    :param geojson_dict: Dictionary with GeoJSON objects as values.
    :return: List of WKT strings.
    """
    wkt_list = []

    for geojson in geojson_dict.values():
        # Convert the GeoJSON object to a Shapely geometry
        geometry = shape(geojson)
        # Convert the Shapely geometry to a WKT string
        wkt_list.append(geometry)
    for i in wkt_list:
        print(i)
        break
        # if not isinstance(geometry, base.BaseGeometry):
        #     print(f"对象 {geometry} 不是有效的 shapely 几何类型。")
        # else:
        #     # 有效性检查
        #     if not geometry.is_valid:
        #         print(f"几何对象 {geometry} 无效。")
        #     # 简单性检查（仅对 LineString 和 Polygon 有效）
        #     if hasattr(geometry, "is_simple") and not geometry.is_simple:
        #         print(f"几何对象 {geometry} 不是简单的。")
        #
        # # 类型检查

    return wkt_list
def osmid_attribute():
    query="""
    SELECT id, uebk25_l
    FROM bayern_soil_map_25832
    WHERE id IN (1, 2, 3);

    """
def area_calculate(data_list1_original,top_num=None):

    data_list1 = copy.deepcopy(data_list1_original)
    if isinstance(data_list1, dict) and 'id_list' in data_list1: #ids_of_type return的id_list是可以直接计算的字典
        data_list1 = data_list1['id_list']

        list_2_geo1 = {i:[(global_id_geo[i]).area,global_id_geo[i]] for i in data_list1}
        data_list1=list_2_geo1
        sorted_dict=dict(sorted(data_list1.items(), key=lambda item: item[1][0], reverse=True))
        if top_num!=None:
            top_dict=dict(islice(sorted_dict.items(), top_num))
        else:
            top_dict=sorted_dict
        area_list = {key: value[0] for key, value in top_dict.items()}
        geo_dict = {key: value[1] for key, value in top_dict.items()}

        return {'area_list':area_list,'geo_map':geo_dict,'id_list':geo_dict}

def geo_calculate(data_list1_original, data_list2_original, mode, buffer_number=0):
    if mode=='area_calculate':
        return area_calculate(data_list2_original,buffer_number)
    #data_list1.keys() <class 'shapely.geometry.polygon.Polygon'>
    """
    buildings in forest

    :param data_list1_original:  bigger element as object forest 宾语
    :param data_list2_original:  smaller element as subject buildings 主语
    :param mode:
    :param buffer_number:
    :return:
    """
    data_list1=copy.deepcopy(data_list1_original)
    data_list2=copy.deepcopy(data_list2_original)

    if isinstance(data_list1, str):
        data_list1 = globals_dict[data_list1]
        data_list2 = globals_dict[data_list2]

    elif isinstance(data_list1,list): #list是geo_calculate return的subject或Object的键值
        list_2_geo1 = {i:global_id_geo[i] for i in data_list1}
        data_list1=list_2_geo1
    if isinstance(data_list1, dict) and 'id_list' in data_list1: #ids_of_type return的id_list是可以直接计算的字典
        data_list1 = data_list1['id_list']

    if isinstance(data_list2,dict) and 'id_list' in data_list2:
        data_list2=data_list2['id_list']
    if  isinstance(data_list2,list):
        list_2_geo2 = {i:global_id_geo[i] for i in data_list2}
        data_list2=list_2_geo2

    # print("len datalist1", len(data_list1))
    # print("len datalist2", len(data_list2))
    # gseries1 = gpd.GeoSeries([shape(geojson) for geojson in data_list1.values()])
    # gseries2= gpd.GeoSeries([shape(geojson) for geojson in data_list2.values()])

    # data_list1=data_list1[:300]
    # for i in data_list1:
    #     print(type(data_list1[i]))
    #     break
    # for i in data_list2:
    #     print(data_list2[i])
    #     break
    gseries1 = gpd.GeoSeries(list(data_list1.values()))
    gseries1.index = list(data_list1.keys())
    # print(gseries1.index)
    gseries2 = gpd.GeoSeries(list(data_list2.values()))
    gseries2.index = list(data_list2.keys())


    gseries1 = gseries1.set_crs("EPSG:4326", allow_override=True)
    gseries1 = gseries1.to_crs("EPSG:32632")
    gseries2 = gseries2.set_crs("EPSG:4326", allow_override=True)
    gseries2 = gseries2.to_crs("EPSG:32632")
    # gseries2 = gpd.GeoSeries([(item['wkt']) for item in data_list2])
    # gseries2.index = [item['osmId'] for item in data_list2]

    # 创建空间索引
    sindex = gseries2.sindex
    result_list = []
    all_id_list = []
    osmId1_dict = {}
    parent_dict=[]
    child_dict=[]
    if mode == "contains":
        # 检查包含关系

        for osmId1, geom1 in gseries1.items():
            possible_matches_index = list(sindex.intersection(geom1.bounds))
            possible_matches = gseries2.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.contains(geom1)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                all_id_list.append(osmId1)
                osmId1_dict[osmId1]=geom1
                all_id_list.extend(matching_osmIds)
                parent_dict.extend(matching_osmIds)
                child_dict.append(osmId1)
                # result_list.append(f"set1 id {osmId1} in set2 id {matching_osmIds}")
                print(f"set1 id {osmId1} in set2 id {matching_osmIds}")
        print(len(osmId1_dict))


    elif mode == "buffer":
        for osmId1, geom1 in tqdm(gseries1.items(), desc="buffer"):
            # osmId1 is smaller element : subject
            # matching_osmIds is bigger element : object
            # 创建缓冲区（100米）
            buffer = geom1.buffer(buffer_number)

            possible_matches_index = list(sindex.intersection(buffer.bounds))
            possible_matches = gseries2.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.intersects(buffer)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                all_id_list.append(osmId1)
                osmId1_dict[osmId1]=geom1
                all_id_list.extend(matching_osmIds)
                parent_dict.extend(matching_osmIds)
                child_dict.append(osmId1)
                # result_list.append(f"set1 id {osmId1} in buffer of set2 id {matching_osmIds} ")
                # print(f"set1 id {osmId1} in buffer of set2 id {matching_osmIds} ")

    elif mode == "intersects":
        # 检查交叉关系
        for osmId1, geom1 in gseries1.items():
            possible_matches_index = list(sindex.intersection(geom1.bounds))
            possible_matches = gseries2.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.intersects(geom1)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                # result_list.append(f"set1 id {osmId1} intersects with set2 id {matching_osmIds}")
                all_id_list.append(osmId1)
                osmId1_dict[osmId1]=geom1
                all_id_list.extend(matching_osmIds)
                parent_dict.extend(matching_osmIds)
                child_dict.append(osmId1)
                # print(f"set1 id {osmId1} intersects with set2 id {matching_osmIds}")

    elif mode == "shortest_distance":
        min_distance = float('inf')
        closest_pair = (None, None)

        # 计算两个列表中每对元素间的距离，并找出最小值
        for item1 in data_list1:
            geom1 = (data_list1[item1])
            for item2 in data_list2:
                geom2 = (data_list1[item2])
                distance = geom1.distance(geom2)
                if distance < min_distance:
                    min_distance = distance
                    closest_pair = (item1, item2)
        # print("distance between set1 id " + str(closest_pair[0]) + " set2 id " + str(
        #     closest_pair[1]) + " is closest: " + str(min_distance) + " m")

        result_list.append("distance between set1 id " + str(closest_pair[0]) + " set2 id " + str(
            closest_pair[1]) + " is closest: " + str(min_distance) + " m")
    elif mode == "single_distance":
        distance = list(data_list1[0].values())[0].distance(list(data_list2[0].values())[0])
        # print(distance)
    """
        globals_dict["bounding_box_region_name"]=region_name
    globals_dict['bounding_coordinates'],globals_dict['bounding_wkb']=find_boundbox(region_name)

    """

    if "bounding_box_region_name" in globals_dict:
        # geo_dict = {globals_dict["bounding_box_region_name"]: wkb.loads(bytes.fromhex(globals_dict['bounding_wkb']))}
        geo_dict = {globals_dict["bounding_box_region_name"]: (wkb.loads(bytes.fromhex((globals_dict['bounding_wkb']))))}
    else:
        geo_dict = {}
    data_list1.update(data_list2)
    geo_dict.update(transfer_id_list_2_geo_dict(all_id_list, data_list1))

    print(len(geo_dict))

    # html=draw_geo_map(geo_dict, "geo")
    # with open('my_list.pkl', 'wb') as file:
    #     pickle.dump(osmId1_list, file)


    return {'object':{'id_list':parent_dict},'subject':{'id_list':child_dict},'geo_map':geo_dict}
    # return {'subject_id_list':parent_dict,'object_id_list':child_dict,'geo_map':geo_dict}
    # return child_dict,parent_dict,geo_dict
    # return geo_dict


#
# print(all_graph_name)
# list_type_of_graph_name('http://example.com/landuse')
def id_2_attributes(id_list):

    if isinstance(id_list, dict) and 'id_list' in id_list: #ids_of_type return的id_list是可以直接计算的字典
        id_list = id_list['id_list']
    # print(id_list)

    element_count = {}

    # Iterate over each element in the input list
    for element in id_list:
        # If the element is already in the dictionary, increment its count
        attribute=global_id_attribute[element]
        if attribute in element_count:
            element_count[attribute] += 1
        # If the element is not in the dictionary, add it with a count of 1
        else:
            element_count[attribute] = 1

    return dict(sorted(element_count.items(), key=lambda item: item[1], reverse=True))

def transfer_id_list_2_geo_dict(id_list, raw_dict=None):
    result_dict = {}
    for i in tqdm(id_list, desc="generating map..."):
        result_dict[i] = raw_dict[i]
    return result_dict
def ttl_read(path):
    from rdflib import Graph
    result_dict= {}
    predicate_dict={}
    g = Graph()

    # 解析TTL文件
    g.parse(path, format="ttl")

    # 遍历图形中的所有三元组并打印它们
    u=0
    for subj, pred, obj in g:
        if str(pred) not in predicate_dict:
            predicate_dict[str(pred)]=set()
        predicate_dict[str(pred)].add(obj)
        if str(subj) not in result_dict:
            result_dict[str(subj)]={}
        result_dict[str(subj)][str(pred)]=str(obj)


    return result_dict,predicate_dict
def search_attribute(dict_,key,value):
    if isinstance(value,list):
        pass
    else:
        value=[value]
    result_dict= {}
    geo_asWKT_key=''

    for subject in dict_:
        if geo_asWKT_key=='':
            for keys in dict_[subject]:
                if "asWKT" in str(keys):
                    geo_asWKT_key=keys
                    break
        else:
            break
    # print(geo_asWKT_key)
    for subject in dict_:
        if key in dict_[subject]:
            for v in value:
                if v in dict_[subject][key]:
                # print(" as")
                # print(dict_[subject][geo_asWKT_key],type((wkt.loads(dict_[subject][geo_asWKT_key]))))

                    result_dict[f"{key}_{v}_{subject}"]=((wkt.loads(dict_[subject][geo_asWKT_key])))
                # break
    # print(len(result_dict))
    # html=draw_geo_map(result_dict,"geo")
    print(len(result_dict))
    return result_dict
def get_table_for_sql():
    query = """
            SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
            """

def sql_debug():
    def sql_get_tabel():
        query = """
        SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
        """

    # 数据库连接参数
    # engine = create_engine('postgresql://postgres:9417941@localhost:5432/osm_database')

    set_bounding_box('munich maxvorstadt')
    # 创建连接
    bounding_box_coordinats = globals_dict['bounding_coordinates']
    min_lat, max_lat, min_lon, max_lon = bounding_box_coordinats
    # 定义边界框

    srid = 4326  # 假设使用WGS 84

    # 执行查询
    bounding_query = f"""
    SELECT *
    FROM buildings
    WHERE ST_Intersects(geom, ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat}, {srid}));
    """
    print(bounding_query)

    attribute_query = f"""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'buildings';
    """

    query = """
    SELECT * FROM buildings;

    """
    start_time = time.time()
    from shapely.wkb import loads
    rows = cur_action(bounding_query)

    end_time = time.time()
    print(end_time - start_time)
    # 打印结果
    print(len(rows))
    result_dict = {}
    start_time = time.time()
    for row in rows:
        result_dict[row[2] + "_" + row[3]+"_" + row[4]] = (wkb.loads(bytes.fromhex(row[6])))
        # print(row)
        # crs = CRS.from_user_input(loads((row[6]), hex=True).srid)
        # print(crs.to_epsg())

        break
    print(result_dict)
    end_time = time.time()
    print(end_time - start_time)
    geo_dict = {
        globals_dict["bounding_box_region_name"]: mapping(wkb.loads(bytes.fromhex((globals_dict['bounding_wkb']))))}
    geo_dict.update(result_dict)
    # draw_geo_map(geo_dict, 'geo')
    # 关闭连接
    cur.close()
    conn.close()
#

# set_bounding_box("munich ismaning")
#
#
# # id_buildings=ids_of_type('buildings','building')
# id_farmland=ids_of_type('landuse','farmland')
# id_soil=ids_of_type('soil','62c')
# buildings_near_farmland=geo_calculate(id_soil,id_farmland,'contains',10)
# print(id_2_attributes(buildings_near_farmland['subject']))
# id1=ids_of_type('buildings','building')


# a=[
#     "forest",
#     "nature_reserve",
#     "scrub"
#   ]
# ids_of_type('landuse',a)
# subject_dict,predicate_dict=ttl_read(r'C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\modified_Moore_Bayern_4326_index.ttl')
# id1=search_attribute(subject_dict,'http://example.org/property/uebk25_l',["62c","64c","80b"])
# id2=ids_of_type('buildings', 'building')
# geo_calculate(id1,id2,'buffer',100)
# search_attribute(subject_dict,'http://example.org/property/uebk25_l',["62c","64c","80b"])
# dict_,predicate_list=ttl_read(r'C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\modified_Moore_Bayern_4326_index.ttl')
# print(predicate_list.keys())
# print(predicate_list['http://example.org/property/uebk25_l'])
# print(search_attribute(dict_,'http://example.org/property/kategorie','Vorherrschend Niedermoor und Erdniedermoor, teilweise degradiert'))
# print(predicate_list)
# aa=["78: Vorherrschend Niedermoor und Erdniedermoor, gering verbreitet Übergangsmoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum",
#         "79: Fast ausschließlich Hochmoor und Erdhochmoor aus Torf",
#         "65c: Fast ausschließlich Anmoorgley, Niedermoorgley und Nassgley aus Lehmsand bis Lehm (Talsediment); im Untergrund carbonathaltig",
#         "75c: Bodenkomplex: Vorherrschend Gley und Anmoorgley, gering verbreitet Moorgley aus (Kryo-)Sandschutt (Granit oder Gneis), selten Niedermoor aus Torf"
# ]
# ids_of_type('soil',aa)
# set_bounding_box("munich ismaning")
# id2=ids_of_type('buildings','building')
# id1=ids_of_type('landuse','farmland')
# id3=ids_of_type('landuse','forest')
# area=area_calculate(id3,5)
# print(area['id_list'])
# print(id3)

# a=geo_calculate(id1,id2,'buffer',10)
# cc=geo_calculate(id3,a['subject'],'intersects')
# print(id3)
# print(id_2_attributes(id3))

# print(id_2_attributes(cc['object']['id_list']))
# # print(a)
# print(b)
# for i in aa:
#     print(shape(aa[i]).wkt)
#     break
# geo_calculate(id1,id2,'intersects')
# start_time = time.time()
#
# (ids_of_type('http://example.com/buildings', 'building'))
# end_time = time.time()
# print(end_time - start_time)
# sql()
# import geopandas as gpd
# import matplotlib.pyplot as plt
# from shapely.geometry import Point, Polygon
# import numpy as np
# building_gdf_data = {
#     'Name': [k[0] for k in id2.keys()],
#     'geometry': [(v) for v in id2.values()]
# }
# soil_gdf_data = {
#     'Name': [k[0] for k in id1.keys()],
#     'geometry': [(v) for v in id1.values()]
# }
# # 假设已经加载了建筑和土壤区域的GeoDataFrame：building_gdf 和 soil_gdf
# building_gdf=gpd.GeoDataFrame(building_gdf_data, geometry='geometry')
# soil_gdf=gpd.GeoDataFrame(soil_gdf_data, geometry='geometry')
# # 计算每个建筑到所有土壤区域的最近距离
# def calculate_nearest(row, other_gdf, other_gdf_column='geometry'):
#     """计算GeoDataFrame中每一行与另一个GeoDataFrame中所有几何形状的最近距离"""
#     point = row.geometry
#     # 计算到另一个GeoDataFrame中每个几何形状的距离
#     distances = other_gdf.distance(point)
#     # 返回最小距离
#     return distances.min()
# building_gdf['distance_to_nearest_soil'] = building_gdf.apply(calculate_nearest, other_gdf=soil_gdf, axis=1)
#
# import matplotlib.pyplot as plt
# import pandas as pd
# # 假设 building_gdf['distance_to_nearest_soil'] 存在且包含距离数据
#
# # 定义距离区间和标签
# bins = [0, 0.01, 0.02, 0.03, 0.04, float('inf')]  # 定义距离区间
# labels = ['0-0.01m', '0.01-0.02m', '0.02-0.03m', '0.03-0.04m', '>0.04m']
#
# # 对距离数据进行分类
# categories = pd.cut(building_gdf['distance_to_nearest_soil'], bins=bins, labels=labels, include_lowest=True)
#
# # 计算每个距离区间的建筑数量
# counts = categories.value_counts(sort=False)
#
# # 转换为百分比
# percentages = counts / counts.sum() * 100
#
# # 绘制饼图
# plt.figure(figsize=(8, 8))
# plt.pie(percentages, labels=percentages.index, autopct='%1.1f%%', startangle=140)
# plt.title('Percentage of Buildings by Distance to Nearest Soil Area')
# plt.savefig(r'C:\Users\Morning\Desktop\hiwi\ttl_query\flask_pro\static\plot_20240305003154.png')
#


#
# # # 对每个建筑应用函数，计算到最近土壤区域的距离
# building_gdf['distance_to_nearest_soil'] = building_gdf.apply(calculate_nearest, other_gdf=soil_gdf, axis=1)
#
# # 绘制距离的直方图
# plt.figure(figsize=(10, 6))
# plt.hist(building_gdf['distance_to_nearest_soil'], bins=30, color='skyblue', edgecolor='black')
# plt.title('Distribution of Distances from Buildings to Nearest Soil Area')
# plt.xlabel('Distance (meters)')
# plt.ylabel('Number of Buildings')
# plt.grid(True)
# plt.savefig(r'C:\Users\Morning\Desktop\hiwi\ttl_query\flask_pro\static\plot_20240305001254.png')
# set_bounding_box("munich ismaning")
# print(ids_of_attribute('buildings'))
try:
    print(ids_of_attribute('landuseaa'))
except:
    pass
print(ids_of_attribute('landuseaa'))