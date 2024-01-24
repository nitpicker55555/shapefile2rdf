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
from geopandas import GeoDataFrame
from openai import OpenAI
load_dotenv()
GPT_MODEL = "gpt-3.5-turbo-1106"
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()
from draw_geo import draw_geo_map
from SPARQLWrapper import SPARQLWrapper, JSON
from tqdm import tqdm
from bounding_box import find_boundbox
from shapely import wkb
globals_dict = {}


# 距离适合农业的土壤最近的居民楼
"""
找到土壤数据库
找到土壤数据库中的所有type名称
找到适合农业的type
反推出这些type的位置和id

计算这些id和居民楼的距离

"""
sparql = SPARQLWrapper("http://127.0.0.1:7200/repositories/osm_search")
def find_bounding_box(region_name):
    globals_dict["bounding_box_region_name"]=region_name
    globals_dict['bounding_coordinates'],globals_dict['bounding_wkb'],response_str=find_boundbox(region_name)
    return response_str
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
    feed_back = ask_soil(query,"")
    for i in feed_back:
        graph_list.append(i['graph']['value'])
    return graph_list


def list_type_of_graph_name(graph_name):
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
    feed_back = ask_soil(query,graph_name)
    for i in feed_back:
        type_list.append(i['fclass']['value'])
    return type_list


def list_id_of_type(graph_name, single_type, bounding_box_coordinats=None):
    """
    globals_dict["bounding_box_region_name"]=region_name
    globals_dict['bounding_coordinates'],globals_dict['bounding_wkb']=find_boundbox(region_name)

    """
    if 'bounding_coordinates' in globals_dict:
        bounding_box_coordinats=globals_dict['bounding_coordinates']
    soil_dict={'61a': '61a: Bodenkomplex: Vorherrschend Anmoorgley und Pseudogley, gering verbreitet Podsol aus (Kryo-)Sandschutt (Granit oder Gneis) über Sandschutt bis Sandgrus (Basislage, verfestigt)', '62c': '62c: Fast ausschließlich kalkhaltiger Anmoorgley aus Schluff bis Lehm (Flussmergel oder Alm) über tiefem Carbonatsandkies (Schotter)', '65c': '65c: Fast ausschließlich Anmoorgley, Niedermoorgley und Nassgley aus Lehmsand bis Lehm (Talsediment); im Untergrund carbonathaltig', '66b': '66b: Fast ausschließlich Anmoorgley aus Lehm bis Schluff, selten Ton (See- oder Flusssediment); im Untergrund carbonathaltig', '67': '67: Fast ausschließlich Gley über Niedermoor und Niedermoor-Gley aus Wechsellagerungen von (Carbonat-)Lehm bis Schluff und Torf über Carbonatsandkies (Schotter)', '72c': '72c: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Sand (Talsediment)', '72f': '72f: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Sand (Substrate unterschiedlicher Herkunft); außerhalb rezenter Talbereiche', '64c': '64c: Fast ausschließlich kalkhaltiger Anmoorgley aus Schluff bis Lehm (Flussmergel) über Carbonatsandkies (Schotter), gering verbreitet aus Talsediment', '73c': '73c: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Schluff bis Lehm, selten aus Ton (Talsediment)', '73f': '73f: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Schluff bis Lehm, selten aus Ton (Substrate unterschiedlicher Herkunft); außerhalb rezenter Talbereiche', '74': '74: Fast ausschließlich Gley über Niedermoor und Niedermoor-Gley aus Wechsellagerungen von Lehm und Torf über Sand bis Lehm (Talsediment)', '75': '75: Fast ausschließlich Moorgley, Anmoorgley und Oxigley aus Lehmgrus bis Sandgrus (Talsediment)', '75c': '75c: Bodenkomplex: Vorherrschend Gley und Anmoorgley, gering verbreitet Moorgley aus (Kryo-)Sandschutt (Granit oder Gneis), selten Niedermoor aus Torf', '77': '77: Fast ausschließlich Kalkniedermoor und Kalkerdniedermoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum; verbreitet mit Wiesenkalk durchsetzt', '78': '78: Vorherrschend Niedermoor und Erdniedermoor, gering verbreitet Übergangsmoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum', '78a': '78a: Fast ausschließlich Niedermoor und Übergangsmoor aus Torf über kristallinen Substraten mit weitem Bodenartenspektrum', '79': '79: Fast ausschließlich Hochmoor und Erdhochmoor aus Torf', '80a': '80a: Fast ausschließlich (flacher) Gley über Niedermoor aus (flachen) mineralischen Ablagerungen mit weitem Bodenartenspektrum über Torf, vergesellschaftet mit (Kalk)Erdniedermoor', '80b': '80b: Überwiegend (Gley-)Rendzina und kalkhaltiger Gley über Niedermoor aus Alm über Torf, engräumig vergesellschaftet mit Kalkniedermoor und Kalkerdniedermoor aus Torf', '850': '850: Bodenkomplex: Humusgleye, Moorgleye, Anmoorgleye und Niedermoore aus alpinen Substraten mit weitem Bodenartenspektrum'}
    if isinstance(single_type,dict):
        replace_list=[]
        for i in single_type:
            if i in soil_dict:
                replace_list.append(soil_dict[i])
            else:
                replace_list.append(i)
        single_type=replace_list
    single_type=str(single_type)
    if '[' in single_type:
        single_type=single_type.replace("[", "(").replace("]", ")")

    else:
        single_type=f"('{single_type}')"
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
    fclass="fclass"
    osm_id="osm_id"
    bounding_box_str=""
    building_type=""
    if bounding_box_coordinats is not None:
        min_lat, max_lat, min_lon, max_lon = bounding_box_coordinats
        polygon_wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
        bounding_box_str=f'BIND("{polygon_wkt}"^^geo:wktLiteral AS ?bbox) .'
        bounding_box_str+="\nFILTER(geof:sfIntersects(?wkt, ?bbox))"
    if "soil" in graph_name:
        fclass='uebk25_l'
        osm_id='soil_id'
    if "building" in graph_name:
        building_type="\n?entity ns1:type ?type ."
    if "all" not in single_type:
        fclass_filter=f'\nFILTER(?fclass IN {single_type})'
    else:
        fclass_filter=""
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


        """ % (graph_name, fclass,osm_id,fclass_filter,building_type,bounding_box_str)
    # print(query)
    feed_back = ask_soil(query,graph_name)
    # print(len(feed_back))
    return feed_back


def ask_soil(query,map):
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
                result_dict.update({map.split("/")[-1] + "_" + fclass +"/"+ result['type']['value']+"/_" + str(osm_id): geometry})
            else:
                result_dict.update({map.split("/")[-1]+"_"+fclass+"_"+str(osm_id):  geometry})
        return result_dict
    except:
        result_list=[]
        for result in results["results"]["bindings"]:
            result_list.append(result)
    # print(result_list)
        return result_list


def get_geo_via_id(graph_name, id):
    if "/" not in graph_name:
        graph_name="http://example.com/"+graph_name
    if "_" in id:
        id=id.split("_")[-1]
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
    feed_back = ask_soil(query,graph_name)
    return feed_back


def geo_calculate(data_list1, data_list2, mode,buffer_number=0):

    if isinstance(data_list1,str):
        data_list1=globals_dict[data_list1]
        data_list2=globals_dict[data_list2]
    print("len datalist1", len(data_list1))
    print("len datalist2", len(data_list2))

    data_list1=data_list1
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
    result_list=[]
    id_list=[]
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
        print(len(osmId1_list))


    elif mode == "buffer":
        for osmId1, geom1 in tqdm(gseries1.items(),desc="buffer"):
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
        print("distance between set1 id "+str(closest_pair[0])+" set2 id "+str(closest_pair[1])+" is closest: "+str(min_distance)+" m")

        result_list.append("distance between set1 id "+str(closest_pair[0])+" set2 id "+str(closest_pair[1])+" is closest: "+str(min_distance)+" m")
    elif mode == "single_distance":
        distance = list(data_list1[0].values())[0].distance(list(data_list2[0].values())[0])
        print(distance)
    """
        globals_dict["bounding_box_region_name"]=region_name
    globals_dict['bounding_coordinates'],globals_dict['bounding_wkb']=find_boundbox(region_name)

    """
    if "bounding_box_region_name" in globals_dict:
        geo_dict={globals_dict["bounding_box_region_name"]:wkb.loads(bytes.fromhex(globals_dict['bounding_wkb']))}
    else:
        geo_dict={}
    data_list1.update(data_list2)
    geo_dict.update(transfer_id_list_2_geo_dict(id_list,data_list1))
    draw_geo_map(geo_dict, "geo")
    with open('my_list.pkl', 'wb') as file:
        pickle.dump(osmId1_list, file)
    return result_list,id_list

#
# print(all_graph_name)
# list_type_of_graph_name('http://example.com/landuse')
def chat_single(messages,mode="json"):
    if mode=="json":

        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            response_format={"type": "json_object"},
            messages=messages
        )
    else:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages
        )
    return response.choices[0].message.content

def transfer_id_list_2_geo_dict(id_list,raw_dict=None):

    result_dict={}
    for i in tqdm(id_list,desc="generating map..."):
        result_dict[i]=raw_dict[i]
    return result_dict
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }
    if tools is None:
        json_data = {"model": model, "response_format": {"type": "json_object"}, "messages": messages}
    else:
        json_data = {"model": model, "messages": messages}
        json_data.update({"tools": tools})
    if tool_choice is not None:
        json_data.update({"tool_choice": tool_choice})
    try:
        while True:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=json_data,
            )
            if "choices" in response.json():
                print(response, "response")
                return response

            else:
                print("400 error")
                time.sleep(2)

    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


def build_agents():
    def test_arg():
        query_list=[
            {
                "description": "First need to find all IDs in the soil graph",
                "whole_plan": ["Find id list of soil map"],
                "next_step": "Call list_id_of_type function",
                "command": {
                    "command": "list_id_of_type",
                    "args": ["http://example.com/soil","all"],
                    "variable": "soil_id_list"
                },
                "finish_sign": False
            }
            ,
            {
                "description": "Now we need to find all elements in buildings graph",
                "whole_plan": ["Find id list of soil map",
                               "Get a list of IDs of buildings"],
                "next_step": "Call list_id_of_type function",
                "command": {
                    "command": "list_id_of_type",
                    "args": ["http://example.com/buildings", "building"],
                    "variable": "buildings_id_list"
                },
                "finish_sign": False
            },
            {
                "description": "Compute element intersection with geo_calculate",
                "whole_plan": ["Find id list of soil map",
                               "Get a list of IDs of buildings",
                               "Compute element intersection"],
                "next_step": "Call geo_calculate function",
                "command": {
                    "command": "geo_calculate",
                    "args": ["soil_id_list", "buildings_id_list","intersects"],
                    "variable": "intersects_result"
                },
                "finish_sign": False
            },
            {
                "description": "",
                "whole_plan": [],
                "next_step": "",
                "command": {},
                "finish_sign": True
            }

        ]
        return query_list
    def execute_function_call(message):

        args_ = list(json.loads(message["tool_calls"][0]["function"]["arguments"]).values())
        print(args_)
        function_name = message["tool_calls"][0]["function"]["name"]
        if function_name:
            results = globals()[function_name](*args_)
            print(results)
        else:
            results = f"Error: function  does not exist"
        return ("length: " + str(len(results)) + " " + str(results)[:300])
    def execute_function_call_dict(message):
        try:
            feed_dict = json.loads(message)
        except:
            feed_dict = (message)
        print(json.dumps(feed_dict, indent=4))
        # feed_dict=json.loads(message)
        finish_sign=str(feed_dict['finish_sign'])

        # print("finish_sign:",finish_sign)
        if "command" in feed_dict['command']:
            command = feed_dict['command']['command']
            variable=feed_dict['command']['variable']

            args_=feed_dict['command']['args']
            globals_dict[variable]=  globals()[command](*args_)
            results=globals_dict[variable]
            if command=="list_type_of_graph_name" and "soil" in str(args_):
                return ("length: " + str(len(results)) + " " + str(results)[:1000])
            else:
                if isinstance(results,list) or isinstance(results,dict):
                    return ("length: " + str(len(results)) + " " + str(results)[:300])
                else:
                    return str(results)[:300]
        else:
            return "break down"
    tools = [{
        "type": "function",
        "function": {
            "name": "list_id_of_type",
            "description": "get all element id of one specific type",
            "parameters": {
                "type": "object",
                "properties": {
                    "graph_name": {
                        "type": "string",
                        "enum": ['http://example.com/landuse', 'http://example.com/soil',
                                 'http://example.com/buildings'],
                        "description": f"the graph user wants to search in database, you need to select the one has most similar semantic meaning",
                    },
                    "single_type": {
                        "type": "string",
                        # "enum": type_list,
                        "description": "type of data user want to search",
                    },

                },
                "required": ["graph_name", "single_type"]
            },
        }
    },
        {
            "type": "function",
            "function": {
                "name": "list_type_of_graph_name",
                "description": "get all element types of this graph and return a type_list, example: for soil graph, its type_list gonna be different kinds of soil",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "graph_name": {
                            "type": "string",
                            "enum": ['http://example.com/landuse', 'http://example.com/soil',
                                     'http://example.com/buildings'],
                            "description": f"the graph user wants to search in database, you need to select the one has most similar semantic meaning",
                        },

                    },
                    "required": ["graph_name"],
                },
            }
        },
    ]
    messages = []
    messages.append({"role": "system",
                     "content": """
                     you are a database query assistant that can use provided functions to query database
                     """})
    messages_2 = []
    messages_2.append({"role": "system",
                       "content": """
You are an AI assistant that processes complex database queries. You need to break down the user's query into several steps to complete the final query. Below are the functions you can use:

{

    "find_bounding_box": {
        "Argument": "region_name",
        "Description": "If user wants to get query result from a specific location, you need to first run this function with argument region_name, then the other function would limit its result in this region. Example: if user wants to search result from munich germany, input of this function would be 'munich germany'."
    },
    "list_type_of_graph_name": {
        "Argument": "graph_name",
        "Description": "Enter the name of the graph you want to query and it returns all types of that graph. For example, for a soil graph, the types are different soil types."
    },
    "list_id_of_type": {
        "Arguments": ["graph_name", "type_name"],
        "Description": "Enter the graph name and type name you want to query, and it returns the corresponding element IDs.
                        If you want to get id_list from multi types at the same time, you can input arg type_name as a list."
        "Example":"
                
        If user wants to search soil that suitable for agriculture,
        first you need to figure out what kind of soil the soil graph have using list_type_of_graph_name,
            "command": {
        "command": "list_type_of_graph_name",
        "args": ["http://example.com/soil"],
        "variable": "soil_type"
    },
        then input type list you think is good for agriculture(please pick its full name but not only index of this type), and use list_id_of_type to get its id_list
                    "command": {
        "command": "list_id_of_type",
        "args": ["http://example.com/soil",[type list]],
        "variable": "soil_id"
    },
        
        "
    },

        "geo_calculate": {
        "Arguments": [id_list_1, id_list_2,"function name",buffer_number=0],
        "Description": "
        geo_calculate function has functions: contains, intersects, buffer. 
        Input should be two id_list which generated by function list_id_of_type and function name you want to use. 
        
        function contains: return which id in id_list_2 geographically contains which id in id_list_1
        function intersects: return which id in id_list_2 geographically intersects which id in id_list_1
        function buffer: return which id in id_list_2 geographically intersects the buffer of which id in id_list_1, if you want to call buffer, you need to specify the last argument "buffer_number" as a number.
        "Example":
        If user wants to search buildings in farmland, 
        first you need to figure out farmland and buildings in which graph using function list_type_of_graph_name,
        then generate id_list for buildings and farmland using function list_id_of_type, 
        "command": {
        "command": "list_id_of_type",
        "args": ["http://example.com/buildings", "building"]
        "variable":"id_list1"
        },
        "command": {
        "command": "list_id_of_type",
        "args": ["http://example.com/landuse", "farmland"]
        "variable":"id_list2"
        },
        finally call geo_calculate(id_list_1,id_list_2,"contains").
        "command": {
        "command": "geo_calculate",
        "args": ["id_list1", "id_list2","contains"]
        "variable":"contains_list"
        }

        
        "
    }
}

Environment:
The database has three graphs: ['http://example.com/landuse', 'http://example.com/soil', 'http://example.com/buildings']


Constraints:
After each step you will receive feedback from functions, which contains results length and results, but you can only receive top 500 characters due to memory limitation.


Each response should only cover one step. Your response format should be json format as follows, and set the finish_sign to True after you get the result of last step, if the task is not finished yet please set finish_sign to False. 

Please always keep all the keys in response,if nothing to write leave the value empty:
Response json format:
{
"description":"what you want to do in this step and next step",
"whole_plan": ["first:...", "second:...", "third:...", ...],
"next_step": "...",
"command": {"command": "", "args": [],"variable":"you can set a variable to store the result of this command"},
"finish_sign": False
}
                     """})


    while True:
        user_content = input("input question:")
        results=""
        messages.append({"role": "user", "content": user_content})
        messages_2.append({"role": "user", "content": user_content})
        step=0
        query_list=test_arg()
        while results!="break down":
        # for chat_response in query_list:
        #     delay = random.uniform(1, 2)

            # 暂停执行随机生成的时间
            # time.sleep(4+delay)
            step+=1
            chat_response = chat_single(messages_2)
            print(f'Agent step {step}:')

            try:
                results=execute_function_call_dict((chat_response))
            except Exception as e:
                results="provided function or args does not correct, please check it and try again, Exception: "+str(e)

            print("\n\nQuery result:")
            print(results)
            print('\n\n')
            # assistant_message = chat_response.json()["choices"][0]["message"]
            messages_2.append({"role": "assistant", "content": chat_response})
            messages_2.append({"role": "user", "content": results})
        print("Task finished.")
        user_content = input("input question:")
        time.sleep(4)
        print("Sure. ")
        # chat_response = chat_completion_request(messages,tools=tools)
        # assistant_message = chat_response.json()["choices"][0]["message"]
        # print(assistant_message)
        # messages_2.append(assistant_message)
        # # messages.append(assistant_message)
        #
        # assistant_message['content'] = str(assistant_message["tool_calls"][0]["function"])
        # messages.append(assistant_message)
        # if assistant_message.get("tool_calls"):
        #     results = str(execute_function_call(assistant_message))
        #     messages.append({"role": "tool", "tool_call_id": assistant_message["tool_calls"][0]['id'],
        #                      "name": assistant_message["tool_calls"][0]["function"]["name"], "content": results})


build_agents()

# all_graph_name=["http://example.com/landuse","http://example.com/soil","http://example.com/buildings"]
# all_soil=(list_type_of_graph_name(all_graph_name[1]))
# print(all_soil)

# region_name="munich Ismaning"
# bounding_coordinates,bounding_wkb=find_boundbox(region_name)
# # # print(list_type_of_graph_name(all_graph_name[1]))
# id_list_buildings=list_id_of_type(all_graph_name[2],"building",bounding_coordinates)
# id_list_landuse=list_id_of_type(all_graph_name[0],["park",'residential'],bounding_coordinates)
#
# id_list_soil=list_id_of_type(all_graph_name[1],"all")

# _,id_list=geo_calculate(id_list_buildings,id_list_soil,"intersects")
# geo_dict={region_name:wkb.loads(bytes.fromhex(bounding_wkb))}
# id_list_buildings.update(id_list_landuse)
# geo_dict=((id_list_soil))

# draw_geo_map(id_list_buildings,"geo")

# print(id_list_landuse)
# print(id_list_soil)

# id1=get_geo_via_id(all_graph_name[0],"153446951") #forest
# id2=get_geo_via_id(all_graph_name[1],"2984") #"78: Vorherrschend Niedermoor und Erdniedermoor, gering verbreitet Übergangsmoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum"
# print(id1)
# geo_calculate(id1,id2,"single_distance")
# query="""
# PREFIX ns1: <http://example.org/property/>
# PREFIX geo: <http://www.opengis.net/ont/geosparql#>
# PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
#     SELECT ?osmId ?wkt
#     WHERE {
#       GRAPH <http://example.com/buildings> {
#         ?entity ns1:fclass "building" .
#         ?entity ns1:osm_id ?osmId .
#         ?entity geo:asWKT ?wkt .
#       }
#         # 创建一个边界框的多边形，用指定的坐标
#         BIND("POLYGON((11.661455 48.2609734, 11.6794104 48.2609734, 11.6794104 48.2702361, 11.661455 48.2702361, 11.661455 48.2609734))"^^geo:wktLiteral AS ?bbox) .
# FILTER(geof:sfIntersects(?wkt, ?bbox))
#     }
#
# """
# start_time = time.time()
# sparql.setQuery(query)
# sparql.setReturnFormat(JSON)
#
# # 执行查询并获取结果
# results = sparql.query().convert()
# print(len(results["results"]["bindings"]))
# end_time = time.time()
#
# # 计算运行时间
# elapsed_time = end_time - start_time
# print(f"函数运行时间：{elapsed_time}秒")