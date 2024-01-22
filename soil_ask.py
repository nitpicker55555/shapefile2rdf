import time,os

from rdflib import Graph
import json
import openai
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored

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


    query="""
PREFIX ns1: <http://example.org/property/>

SELECT DISTINCT ?fclass
WHERE {
  GRAPH <%s> {
    ?entity ns1:fclass ?fclass .
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


    id_geo_dict={}

    query="""
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
    for result in results["results"]["bindings"]:
        print(result)
        result_list.append(result)
    return result_list

all_graph_name=list_all_graph_name()
print(all_graph_name)
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
    tools=["list_type_of_graph_name()","list_id_of_type()",list_all_graph_name()]
    type_list=[]
    tools_list = [{
        "type": "function",
        "function": {
            "name": "list_id_of_type",
            "description": "get all elements information with specific type in the graph of database",
            "parameters": {
                "type": "object",
                "properties": {
                    "single_type": {
                        "type": "string",
                        "enum": type_list,
                        "description": "select the semantically similar type in the list",
                    },
                },
                "required": ["single_type"]
            },
        }
    },
        {
            "type": "function",
            "function": {
                "name": "list_type_of_graph_name",
                "description": "get all element types of this graph in database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "graph_name": {
                            "type": "string",
                            "enum": all_graph_name,
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
                     Response Format: 
                    {
                        "thoughts": {
                            "text": "thought",
                            "reasoning": "reasoning",
                            "plan": "- short bulleted\n- list that conveys\n- long-term plan",
                            "criticism": "constructive self-criticism",
                            "speak": "thoughts summary to say to user",
                        },
                        "command": {"name": "command name", "args": {"arg name": "value"}},
                    }
                     """})
    messages_2 = []
    messages_2.append({"role": "system",
                     "content": "为输入文本中的特定区域类型选择最合适的type"})



def ask_gpt():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_type_of_graph_name",
                "description": "get all element types of this graph in database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "graph_name": {
                            "type": "string",
                            "enum": all_graph_name,
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
                     "content": "为输入的文本中所有的区域选择最合适的graph name"})
    messages_2 = []
    messages_2.append({"role": "system",
                     "content": "为输入文本中的特定区域类型选择最合适的type"})

    while True:
        user_input=input("")
        messages.append({"role": "user", "content":user_input})
        messages_2.append({"role": "user", "content":user_input})

        chat_response = chat_completion_request(
            messages, tools=tools
        )
        assistant_message = chat_response.json()["choices"][0]["message"]
        messages.append(assistant_message)
        print(assistant_message)
        type_list=list_type_of_graph_name(json.loads(assistant_message["tool_calls"][0]["function"]["arguments"])["graph_name"])
        tools_2 = {
            "type": "function",
            "function": {
                "name": "list_id_of_type",
                "description": "get all elements information with specific type in the graph of database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "single_type": {
                            "type": "string",
                            "enum": type_list,
                            "description": "select the semantically similar type in the list",
                        },
                    },
                    "required": ["single_type"]
                },
            }
        }

        chat_response_2 = chat_completion_request(
            messages_2, tools=tools_2
        )
        print(chat_response_2)
        assistant_message_2 = chat_response_2.json()["choices"][0]["message"]
        messages_2.append(assistant_message_2)
        print(assistant_message_2)
        id_list=list_id_of_type(json.loads(assistant_message["tool_calls"][0]["function"]["arguments"])["graph_name"],json.loads(assistant_message_2["tool_calls"][0]["function"]["arguments"])["single_type"])
ask_gpt()