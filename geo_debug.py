import pickle
import random
import time, os

from rdflib import Graph
import json
import openai
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored
from dotenv import load_dotenv
import geopandas as gpd
from shapely.wkt import loads
from shapely.geometry import Polygon
import ast
from draw_geo import draw_geo_map
from SPARQLWrapper import SPARQLWrapper, JSON
from tqdm import tqdm
from bounding_box import find_boundbox
from shapely import wkb
from shapely import wkt
globals_dict = {}

sparql = SPARQLWrapper("http://127.0.0.1:7200/repositories/osm_search")


def set_bounding_box(region_name):
    if region_name!=None:
        globals_dict["bounding_box_region_name"] = region_name
        globals_dict['bounding_coordinates'], globals_dict['bounding_wkb'], response_str = find_boundbox(region_name)
        return response_str
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


def ids_of_type(graph_name, single_type, bounding_box_coordinats=None):
    """
    globals_dict["bounding_box_region_name"]=region_name
    globals_dict['bounding_coordinates'],globals_dict['bounding_wkb']=find_boundbox(region_name)

    """
    if 'bounding_coordinates' in globals_dict:
        bounding_box_coordinats = globals_dict['bounding_coordinates']
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
    # print(query)
    feed_back = ask_soil(query, graph_name)
    # print(len(feed_back))



    # if "bounding_box_region_name" in globals_dict:
    #     geo_dict = {globals_dict["bounding_box_region_name"]: wkb.loads(bytes.fromhex(globals_dict['bounding_wkb']))}
    # else:
    #     geo_dict = {}

    # geo_dict.update((feed_back))
    # html=draw_geo_map(geo_dict, "geo")
    # print(html)

    return feed_back


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
            geometry = loads(wkt)

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


def geo_calculate(data_list1, data_list2, mode, buffer_number=0):
    if isinstance(data_list1, str):
        data_list1 = globals_dict[data_list1]
        data_list2 = globals_dict[data_list2]
    # print("len datalist1", len(data_list1))
    # print("len datalist2", len(data_list2))


    # data_list1=data_list1[:300]
    gseries1 = gpd.GeoSeries(list(data_list1.values()))
    gseries1.index = list(data_list1.keys())
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
    id_list = []
    osmId1_list = []
    if mode == "contains":
        # 检查包含关系

        for osmId1, geom1 in gseries1.items():
            possible_matches_index = list(sindex.intersection(geom1.bounds))
            possible_matches = gseries2.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.contains(geom1)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                id_list.append(osmId1)
                osmId1_list.append(osmId1)
                id_list.extend(matching_osmIds)
                result_list.append(f"set1 id {osmId1} in set2 id {matching_osmIds}")
                print(f"set1 id {osmId1} in set2 id {matching_osmIds}")
        # print(len(osmId1_list))


    elif mode == "buffer":
        for osmId1, geom1 in tqdm(gseries1.items(), desc="buffer"):
            # 创建缓冲区（100米）
            buffer = geom1.buffer(buffer_number)

            possible_matches_index = list(sindex.intersection(buffer.bounds))
            possible_matches = gseries2.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.intersects(buffer)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                id_list.append(osmId1)
                osmId1_list.append(osmId1)
                id_list.extend(matching_osmIds)
                result_list.append(f"set1 id {osmId1} in buffer of set2 id {matching_osmIds} ")
                # print(f"set1 id {osmId1} in buffer of set2 id {matching_osmIds} ")

    elif mode == "intersects":
        # 检查交叉关系
        for osmId1, geom1 in gseries1.items():
            possible_matches_index = list(sindex.intersection(geom1.bounds))
            possible_matches = gseries2.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.intersects(geom1)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                result_list.append(f"set1 id {osmId1} intersects with set2 id {matching_osmIds}")
                id_list.append(osmId1)
                osmId1_list.append(osmId1)
                id_list.extend(matching_osmIds)
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
        geo_dict = {globals_dict["bounding_box_region_name"]: wkb.loads(bytes.fromhex(globals_dict['bounding_wkb']))}
    else:
        geo_dict = {}
    data_list1.update(data_list2)
    geo_dict.update(transfer_id_list_2_geo_dict(id_list, data_list1))
    html=draw_geo_map(geo_dict, "geo")
    # with open('my_list.pkl', 'wb') as file:
    #     pickle.dump(osmId1_list, file)

    return html


#
# print(all_graph_name)
# list_type_of_graph_name('http://example.com/landuse')


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

                    result_dict[f"{key}_{v}_{subject}"]=(wkt.loads(dict_[subject][geo_asWKT_key]))
                # break
    # print(len(result_dict))
    html=draw_geo_map(result_dict,"geo")
    return html
# set_bounding_box("munich ismaning")
# id1=ids_of_type('http://example.com/landuse','forest')
# id2=ids_of_type('http://example.com/landuse','residential')
# geo_calculate(id1,id2,'intersects')
# dict_,predicate_list=ttl_read(r'C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\modified_Moore_Bayern_4326_index.ttl')
# print(predicate_list.keys())
# print(predicate_list['http://example.org/property/uebk25_l'])
# print(search_attribute(dict_,'http://example.org/property/kategorie','Vorherrschend Niedermoor und Erdniedermoor, teilweise degradiert'))
# print(predicate_list)
# ids_of_type('http://example.com/landuse','forest')
