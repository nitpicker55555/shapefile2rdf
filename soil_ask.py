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
    if bounding_box_coordinats is not None:
        min_lat, max_lat, min_lon, max_lon = bounding_box_coordinats
        polygon_wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
        bounding_box_str=f'BIND("{polygon_wkt}"^^geo:wktLiteral AS ?bbox) .'
        bounding_box_str+="\nFILTER(geof:sfIntersects(?wkt, ?bbox))"
    if "soil" in graph_name:
        fclass='uebk25_l'
        osm_id='soil_id'

    query = """
PREFIX ns1: <http://example.org/property/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
    SELECT ?osmId ?wkt
    WHERE {
      GRAPH <%s> {
        ?entity ns1:%s "%s" .
        ?entity ns1:%s ?osmId .
        ?entity geo:asWKT ?wkt .
      }
        # 创建一个边界框的多边形，用指定的坐标
        %s
    }


        """ % (graph_name, fclass,single_type,osm_id,bounding_box_str)
    print(query)
    feed_back = ask_soil(query,graph_name+"_"+single_type)
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

            # 将WKT字符串转换为几何对象
            geometry = loads(wkt)

            # 添加到列表
            result_dict.update({map.split("/")[-1]+"_"+str(osm_id):  geometry})
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


def geo_calculate(data_list1, data_list2, mode, buffer_number=0):
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
    if mode == "contains":
        # 检查包含关系

        for osmId1, geom1 in gseries1.items():
            possible_matches_index = list(sindex.intersection(geom1.bounds))
            possible_matches = gseries2.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.contains(geom1)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                id_list.append(osmId1)
                id_list.extend(matching_osmIds)
                result_list.append(f"set1 id {osmId1} in set2 id {matching_osmIds}")
                print(f"set1 id {osmId1} in set2 id {matching_osmIds}")


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
def merge_id_list(list1,list2):
    merged_list = list1.copy()

    existing_osm_ids = set(item['osmId'] for item in list1)

    for item in list2:
        if item['osmId'] not in existing_osm_ids:
            merged_list.append(item)
            existing_osm_ids.add(item['osmId'])

    return merged_list
def transfer_id_list_2_geo_dict(id_list,raw_dict):
    result_dict={}
    for i in tqdm(id_list,desc="transferring..."):
        # id=i.split("_")[-1]
        # map=i.split("_")[0]
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
        feed_dict=json.loads(message)
        finish_sign=str(feed_dict['finish_sign'])

        print("finish_sign:",finish_sign)
        command = feed_dict['command']['command']
        variable=feed_dict['command']['variable']

        args_=feed_dict['command']['args']
        globals_dict[variable]=  globals()[command](*args_)
        results=globals_dict[variable]
        if command=="list_type_of_graph_name" and "soil" in str(args_):
            return ("length: " + str(len(results)) + " " + str(results)[:1000])
        else:
            return ("length: " + str(len(results)) + " " + str(results)[:300])
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
    "list_type_of_graph_name": {
        "Argument": "graph_name",
        "Description": "Enter the name of the graph you want to query and it returns all types of that graph. For example, for a soil graph, the types are different soil types."
    },
    "list_id_of_type": {
        "Arguments": ["graph_name", "type_name"],
        "Description": "Enter the graph name and type name you want to query, and it returns the corresponding element IDs."
    },

        "geo_calculate": {
        "Arguments": [id_list_1, id_list_2,"function name",buffer_number=0],
        "Description": "
        geo_calculate function has functions: contains, intersects, buffer. 
        Input should be two id_list which generated by function list_id_of_type and function name you want to use. 
        
        function contains: return which id in id_list_2 geographically contains which id in id_list_1
        function intersects: return which id in id_list_2 geographically intersects which id in id_list_1
        function buffer: return which id in id_list_2 geographically intersects the buffer of which id in id_list_1, if you want to call buffer, you need to specify the last argument "buffer_number" as a number.
        Example:
{        If user wants to search buildings in farmland, 
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
        },},{
        If user wants to search soil that suitable for agriculture,
        first you need to figure out what kind of soil the soil graph have using list_type_of_graph_name,
            "command": {
        "command": "list_type_of_graph_name",
        "args": ["http://example.com/soil"],
        "variable": "soil_type"
    },
        then pick one you think is good for agriculture(please pick its full name but not only index of this type), and use list_id_of_type to get its id_list
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
        user_content = input("input")
        results=""
        messages.append({"role": "user", "content": user_content})
        messages_2.append({"role": "user", "content": user_content})
        while results!="break down":
            chat_response = chat_single(messages_2)
            print(chat_response)
            try:
                results=execute_function_call_dict(chat_response)
            except Exception as e:
                results="provided function or args does not correct, please check it and try again, Exception: "+str(e)
            print(results)
            # assistant_message = chat_response.json()["choices"][0]["message"]
            messages_2.append({"role": "assistant", "content": chat_response})
            messages_2.append({"role": "user", "content": results})
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


# build_agents()

all_graph_name=list_all_graph_name()
region_name="munich Ismaning"
bounding_coordinates,bounding_wkb=find_boundbox(region_name)
# # print(list_type_of_graph_name(all_graph_name[1]))
id_list_buildings=list_id_of_type(all_graph_name[2],"building",bounding_coordinates)
id_list_landuse=list_id_of_type(all_graph_name[0],"forest",bounding_coordinates)

# # id_list_soil=list_id_of_type(all_graph_name[1],"78: Vorherrschend Niedermoor und Erdniedermoor, gering verbreitet Übergangsmoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum")
# # print(id_list_landuse)
# # print(id_list_soil)
#

_,id_list=geo_calculate(id_list_buildings,id_list_landuse,"buffer",100)
geo_dict={region_name:wkb.loads(bytes.fromhex(bounding_wkb))}
id_list_buildings.update(id_list_landuse)
geo_dict.update(transfer_id_list_2_geo_dict(id_list,id_list_buildings))

draw_geo_map(geo_dict,"geo")

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