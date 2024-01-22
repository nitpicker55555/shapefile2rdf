import time,os

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

load_dotenv()
from SPARQLWrapper import SPARQLWrapper, JSON
GPT_MODEL = "gpt-3.5-turbo-1106"
api_key = os.getenv('OPENAI_API_KEY')

#距离适合农业的土壤最近的居民楼
"""
找到土壤数据库
找到土壤数据库中的所有type名称
找到适合农业的type
反推出这些type的位置和id

计算这些id和居民楼的距离

"""
sparql = SPARQLWrapper("http://LAPTOP-AN4QTF3N:7200/repositories/osm_search")
def list_all_graph_name():
    """

    :return:目前所有的数据库
    {'graph': {'type': 'uri', 'value': 'http://example.com/buildings'}}
    """
    query="""
    SELECT DISTINCT ?graph
WHERE {
  GRAPH ?graph { ?s ?p ?o }
}

    """
    graph_list=[]
    feed_back= ask_soil(query)
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

        query="""
    PREFIX ns1: <http://example.org/property/>
    
    SELECT DISTINCT ?fclass
    WHERE {
      GRAPH <%s> {
        ?entity ns1:uebk25_l ?fclass .
      }
    }
    
        """%graph_name
    type_list=[]
    feed_back=ask_soil(query)
    for i in feed_back:
        type_list.append(i['fclass']['value'])
    return type_list
def list_id_of_type(graph_name,single_type):
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


    if "soil" not in graph_name:
        query = """
        PREFIX ns1: <http://example.org/property/>
        PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        SELECT ?osmId ?wkt
        WHERE {
          GRAPH <%s> {
            ?entity ns1:fclass "%s" .
            ?entity ns1:osm_id ?osmId .
            ?entity geo:asWKT ?wkt .
          }
        }


            """ % (graph_name, single_type)
    else:

        query="""

PREFIX ns1: <http://example.org/property/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
SELECT ?osmId ?wkt
WHERE {
  GRAPH <%s> {
    ?entity ns1:uebk25_l "%s" .
    ?entity ns1:soil_id ?osmId .
    ?entity geo:asWKT ?wkt .
  }
}


    """%(graph_name,single_type)

    feed_back=ask_soil(query)
    return feed_back
def ask_soil(query):




    # SPARQL查询来提取所有的ns1:kategorie实体
    sparql.setQuery ( query)
    sparql.setReturnFormat(JSON)

    # 执行查询并获取结果
    results = sparql.query().convert()

    # 遍历并打印结果
    result_list=[]

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
                result_list.append({"osmId":osm_id,"wkt":geometry})
    except:
        for result in results["results"]["bindings"]:
            result_list.append(result)
    # print(result_list)
    return result_list
def get_geo_via_id(graph_name,id):
    """

    :param graph_name:
    :param id:
    :return:
    """
    if "soil" not in graph_name:

        query="""
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


    """%(graph_name,id)
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


    """%(graph_name,id)
    # print(query)
    feed_back=ask_soil(query)
    return feed_back

def geo_calculate(data_list1,data_list2,mode,buffer_number=0):
    print("len datalist1",len(data_list1))
    print("len datalist2",len(data_list2))
    gseries1 = gpd.GeoSeries([(item['wkt']) for item in data_list1])
    gseries1.index = [item['osmId'] for item in data_list1]

    gseries2 = gpd.GeoSeries([(item['wkt']) for item in data_list2])
    gseries2.index = [item['osmId'] for item in data_list2]

    # 创建空间索引
    sindex = gseries2.sindex
    if mode=="contains":
    # 检查包含关系
        for osmId1, geom1 in gseries1.items():
            possible_matches_index = list(sindex.intersection(geom1.bounds))
            possible_matches = gseries2.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.contains(geom1)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                print(f"osmId {osmId1} in: {matching_osmIds}")
    elif mode=="buffer":
        for osmId1, geom1 in gseries1.items():
            # 创建缓冲区（100米）
            buffer = geom1.buffer(buffer_number)

            possible_matches_index = list(sindex.intersection(buffer.bounds))
            possible_matches = gseries2.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.intersects(buffer)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                print(f"osmId {osmId1} in buffer of: {matching_osmIds}")
    elif mode == "intersects":
            # 检查交叉关系
            for osmId1, geom1 in gseries1.items():
                possible_matches_index = list(sindex.intersection(geom1.bounds))
                possible_matches = gseries2.iloc[possible_matches_index]
                precise_matches = possible_matches[possible_matches.intersects(geom1)]

                if not precise_matches.empty:
                    matching_osmIds = precise_matches.index.tolist()
                    print(f"osmId {osmId1} intersects with: {matching_osmIds}")
    elif mode=="shortest_distance":
        min_distance = float('inf')
        closest_pair = (None, None)

        # 计算两个列表中每对元素间的距离，并找出最小值
        for item1 in data_list1:
            geom1 = loads(item1['wkt'])
            for item2 in data_list2:
                geom2 = loads(item2['wkt'])
                distance = geom1.distance(geom2)
                if distance < min_distance:
                    min_distance = distance
                    closest_pair = (item1['osmId'], item2['osmId'])
        print(closest_pair, min_distance)
    elif mode=="single_distance":
        distance = data_list1[0]['wkt'].distance(data_list2[0]['wkt'])
        print(distance)


# all_graph_name=list_all_graph_name()
# print(all_graph_name)
# list_type_of_graph_name('http://example.com/landuse')
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }
    json_data = {"model": model, "messages": messages}
    if tools is not None:
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

        args_=list(json.loads(message["tool_calls"][0]["function"]["arguments"]).values())
        print(args_)
        function_name=message["tool_calls"][0]["function"]["name"]
        if function_name:
            results = globals()[function_name](*args_)
            print(results)
        else:
            results = f"Error: function  does not exist"
        return results[:400]


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
                "required": ["graph_name","single_type"]
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
                            "enum": ['http://example.com/landuse', 'http://example.com/soil', 'http://example.com/buildings'],
                            "description": f"the graph user wants to search in database, you need to select the one has most similar semantic meaning",
                        },

                    },
                    "required": ["graph_name"],
                },
            }
        },
    ]
    messages=[]
    messages.append({"role": "system",
                     "content": """
                     You are an AI assistant that processes complex database queries. You need to break down the user's query into several steps to complete the final query. :
Each response should only cover one step. Your response format should be as follows, and set the finish_sign to True if you think the task is completed:
{
"whole_plan": ["first:...", "second:...", "third:...", ...],
"next_step": "...",
"command": {"command": "", "args": []},
"finish_sign": False
}
                     """})
    messages_2=[]
    messages_2.append({"role": "system",
                     "content": """
You are an AI assistant that processes complex database queries. You need to break down the user's query into several steps to complete the final query. Below are the functions you can use:

{
    "get_all_graph_name": {
        "Description": "Returns the names of all graphs in the current database."
    },
    "get_type_of_graph": {
        "Argument": "graph_name",
        "Description": "Enter the name of the graph you want to query and it returns all types of that graph. For example, for a soil graph, the types are different soil types."
    },
    "get_id_of_type": {
        "Arguments": ["graph_name", "type_name"],
        "Description": "Enter the graph name and type name you want to query, and it returns the corresponding element IDs."
    }
}

Each response should only cover one step. Your response format should be as follows, and set the finish_sign to True if you think the task is completed:
{
"whole_plan": ["first:...", "second:...", "third:...", ...],
"next_step": "...",
"command": {"command": "", "args": []},
"finish_sign": False
}
                     """})

    while True:
        user_content=input("input")
        messages.append({"role": "user", "content": user_content})
        messages_2.append({"role": "user", "content": user_content})

        chat_response = chat_completion_request(messages,tools=tools)
        assistant_message = chat_response.json()["choices"][0]["message"]
        print(assistant_message)
        messages_2.append(assistant_message)
        # messages.append(assistant_message)

        assistant_message['content'] = str(assistant_message["tool_calls"][0]["function"])
        messages.append(assistant_message)
        if assistant_message.get("tool_calls"):
            results = str(execute_function_call(assistant_message))
            messages.append({"role": "tool", "tool_call_id": assistant_message["tool_calls"][0]['id'],
                             "name": assistant_message["tool_calls"][0]["function"]["name"], "content": results})




build_agents()


# print(list_type_of_graph_name(all_graph_name[1]))
# id_list_buildings=list_id_of_type(all_graph_name[2],"building")
# id_list_landuse=list_id_of_type(all_graph_name[0],"forest")
# id_list_soil=list_id_of_type(all_graph_name[1],"78: Vorherrschend Niedermoor und Erdniedermoor, gering verbreitet Übergangsmoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum")
# geo_calculate(id_list_landuse,id_list_soil,"contains")

# print(id_list_landuse)
# print(id_list_soil)

# id1=get_geo_via_id(all_graph_name[0],"153446951") #forest
# id2=get_geo_via_id(all_graph_name[1],"2984") #"78: Vorherrschend Niedermoor und Erdniedermoor, gering verbreitet Übergangsmoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum"
# print(id1)
# geo_calculate(id1,id2,"single_distance")