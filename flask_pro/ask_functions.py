from chat_py import *

import json,re
from rag_model import calculate_similarity
from rag_model_openai import calculate_similarity_openai
global_paring_dict={}
new_dict_num=0
file_path = 'global_paring_dict.jsonl'
if os.path.exists(file_path):
    with open('global_paring_dict.jsonl', 'r', encoding='utf-8') as file:
        # 逐行读取并处理每一行
        for line in file:
            current_dict = json.loads(line)
            key = next(iter(current_dict))  # 获取当前字典的键
            # 如果键不存在于全局字典中，直接添加
            if key not in global_paring_dict:
                global_paring_dict[key] = current_dict[key]
            else:
                # 如果键已存在，更新该键对应的字典
                global_paring_dict[key].update(current_dict[key])
    for key, sub_dict in global_paring_dict.items():
        for sub_key, value in sub_dict.items():
            print(f'{key} -> {sub_key}')

def limit_total_words(lst, max_length=10000):
    total_length = 0
    result = []

    for item in lst:
        current_length = len(item)
        if total_length + current_length > max_length:
            break
        result.append(item)
        total_length += current_length

    return result
def error_test():
    print("normal output")
    raise Exception("asdasdawfdafc asdac zcx fwe")
def describe_label(query,given_list,table_name,messages=None):
    if messages == None:
        messages = []

    ask_prompt = """
    Based on the this list: %s, create imitations to match the query. Be sure to use the same language as the provided list, and be as concise as possible, offering only keywords. Response in json
    {
    'result':statement
    }
    
    """%given_list
    if messages == None:
        messages = []
    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', query))
    result = chat_single(messages, 'json')
    # print(result)
    json_result = json.loads(result)
    if 'result' in json_result:

            return json_result['result']
    else:
        raise Exception('no relevant item found for: ' + query + ' in given list.')
def vice_versa(query, messages=None):
    if messages == None:
        messages = []

    ask_prompt = """
    Rewrite the input to inverse the judgement, return json format.
    Example1:
        user:"good for agriculture"

        {
        "result": "Bad for agriculture"
        }
    Example2:
        user:"negative for planting tomatoes"
        {
        "result": "positive for planting tomatoes"
        }
    Example3:
        user:"for commercial"
        {
        "result": "not for commercial"
        }
    """
    if messages == None:
        messages = []
    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', query))
    result = chat_single(messages, 'json')
    # print(result)
    json_result = json.loads(result)
    if 'result' in json_result:
            return json_result['result']
    else:
        raise Exception('no relevant item found for: ' + query + ' in given list.')
def string_process(s):
    processed=re.sub(r'\d+', '', s)
    if processed.startswith(':'):
        processed=processed[1:]
    return  processed
def details_pick_chatgpt(query,given_list,table_name,messages=None):

    # given_list = limit_total_words(given_list)
    ask_prompt = """
    Judge statement correct or not,
    if correct, response in json:
    {
    "judgment":True
    }
    if not correct, response in json:
    {
    "judgment":False
    }
    
    Example1: 
    "is "Fast ausschließlich (flacher) Gley über Niedermoor aus (flachen) mineralischen Ablagerungen" "good for agriculture"?"
    
    Your response:
    {
    "judgment":True
    }
    
    """

    reversed_query=vice_versa(query)
    new_paring_dict={query:[],reversed_query:[]}


    for word in given_list:
        if word!='':
            messages = []
            messages.append(message_template('system', ask_prompt))
            messages.append(message_template('user',f'is "{string_process(word)}" "{query}"?'))
            print(f'is {string_process(word)} {query}?')

            result = chat_single(messages, 'json')
            # print(result)
            json_result = json.loads(result)
            if 'judgment' in json_result:
                if json_result['judgment']:
                    new_paring_dict[query].append(word)
                else:
                    new_paring_dict[reversed_query].append(word)

            else:
                raise Exception('no relevant item found for: ' + query + ' in given list.')
    if new_paring_dict[query]!=[]:
        if table_name not in global_paring_dict:
            global_paring_dict[table_name]={}



        global_paring_dict[table_name].update(new_paring_dict)

        with open('global_paring_dict.jsonl','a',encoding='utf-8') as file:
            json.dump({table_name:new_paring_dict}, file)
            file.write('\n')
        return new_paring_dict[query]
    raise Exception('no relevant item found for: ' + query)


def details_pick(query, given_list, table_name, messages=None):
    def after_match(query_paring_list):
        vice_list=set(given_list)-set(query_paring_list)
        new_paring_dict[query]=list(query_paring_list)
        new_paring_dict[reversed_query]=list(vice_list)
        if table_name not in global_paring_dict:
            global_paring_dict[table_name] = {}

        global_paring_dict[table_name].update(new_paring_dict)

        return new_paring_dict
    reversed_query = vice_versa(query)
    new_paring_dict = {query: [], reversed_query: []}
    # describe the target label to make match more precise

    query_paring_list=calculate_similarity_openai(table_name,query)
    if len(query_paring_list)!=0:
        result=after_match(query_paring_list)
        new_paring_dict.update(result)
        return result[query]
    else:
        target_label_describtion = describe_label(query, list(given_list)[:2],table_name)
        query_paring_list = calculate_similarity_openai(table_name, target_label_describtion)

        if len(query_paring_list)!=0:
            result = after_match(query_paring_list)
            new_paring_dict.update(result)
            with open('global_paring_dict.jsonl', 'a', encoding='utf-8') as file:
                json.dump({table_name: new_paring_dict}, file)
                file.write('\n')
            return result[query]
        else:
            raise Exception('no relevant item found for: ' + query)
def pick_match(query,given_list,table_name):
    if query in given_list:
        return query
    if 'building' in query:
        return 'building'
    find_pre_matched={}
    if table_name in global_paring_dict:
        if list(global_paring_dict[table_name].keys()) != []:
            find_pre_matched = calculate_similarity(list(global_paring_dict[table_name].keys()), query)

    if find_pre_matched != {}:
        print('find_pre_matched:', find_pre_matched)
        match_list_key = list(find_pre_matched.keys())[0]
        match_list = global_paring_dict[table_name][match_list_key]
        return match_list
    else:
        match_dict=calculate_similarity(given_list,query)
    print(query+'\n')
    # print(given_list)
    print('\n\nmatch_dict:',match_dict)
    if match_dict!={}:
        return list(match_dict.keys())

    else:

        match_list=details_pick(query,given_list,table_name)
        print('\n\nmatch_list:', match_list)
        if match_list==[]:
            raise Exception('no relevant item found for: ' +query + ' in given list.')
        return match_list
    # messages.append(message_template('assistant',result))
def judge_bounding_box(query,messages=None):
    if messages==None:
        messages=[]
    if 'munich ismaning' in query.lower():
        return 'munich ismaning'

    ask_prompt="""Does query contain a specific place name? If so, please give the place name back and do not change its 
    original string. Return json format like: { "bounding_box": { "exist":true, "place_name":place_name } 

    }
    else:
        {
        "bounding_box": {
            "exist":false
        }
    }
    Here are some place name may be appear in query:
    munich, munich moosach, munich maxvorstadt
    """
    if messages==None:
        messages=[]

    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',query))
    result=chat_single(messages,'json')
    # print(result)
    json_result=json.loads(result)
    if 'bounding_box' in json_result:
        if json_result['bounding_box']['exist']:
            return json_result['bounding_box']['place_name']
        else:
            return None
    
    else:
        raise Exception('no relevant item found for: ' +query + ' in given list.')
def judge_geo_relation(query,messages=None):
    if messages==None:
        messages=[]
    geo_relation=['intersects','contains','buffer','area_calculate']
    ask_prompt="""You are a search query analyst tasked with analyzing user queries to determine if they include 
    geographical relationships. For each query, assess if it contains any of the following geographical operations: [
    'intersects', 'contains', 'buffer', 'area_calculate']. Provide a response indicating whether the query includes a 
    geographical calculation and, if so, which type. Response in json format. Examples of expected analyses are as follows: 

Query: "I want to know buildings 100m around the forest"
Response:
{
    "geo_calculations": {
        "exist": true,
        "type": "buffer",
        "num": 100
    }
}
Query: "I want to know buildings in forest"
Response:
{
    "geo_calculations": {
        "exist": true,
        "type": "contains",
        "num": 0
    }
}
Query: "I want to know residential closed to park"
Response:
{
    "geo_calculations": {
        "exist": true,
        "type": "buffer",
        "num": 10
    }
}
Query: "I want to know the largest 5 parks"
Response:
{
    "geo_calculations": {
        "exist": true,
        "type": "area_calculate",
        "num": 5
    }
}
For queries that do not involve any geographical relationship, your response should be:

{
    "geo_calcalculations": {
        "exist": false,
    }
}
Please ensure accuracy and precision in your responses, as these are critical for correctly interpreting the user's needs.
    """
    if messages==None:
        messages=[]

    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',query))
    result=chat_single(messages,'json')
    # print(result)
    json_result=json.loads(result)
    if 'geo_calculations' in json_result:
        if json_result['geo_calculations']['exist']:
            # object_dict=judge_object_subject(query)
            if 'num' in json_result['geo_calculations']:
                return {'type':json_result['geo_calculations']['type'],'num':json_result['geo_calculations']['num']}
            else:
                return {'type':json_result['geo_calculations']['type'],'num':0}
        else:
            return None
    else:
        raise Exception('no relevant item found for: ' +query + ' in given list.')
def judge_object_subject(query,geo_relation_dict,messages=None):
    print('query for judge_object_subject:',query)
    if messages==None:
        messages=[]
    ask_prompt_geo_relation="""
    
    Please response in json format: {'primary_subject':primary_subject, 
    'related_statement':related_geographic_element}. 
    
    For example, when I ask, 'I want to know the 
    residential area near the swamp,' you should respond with: {'primary_subject':'residential area', 
    'related_statement':'swamp'}. Similarly, for 'I want to know the buildings around 100m of forests, 
    ' the response should be:  {'primary_subject':'buildings', 'related_statement':'forests'}, 
    
    If there is no related_statement, related_statement should be set as None, example: 
    for 'the largest 5 forest', related_statement is None. """
    ask_prompt_adj="""
You are a query analysis expert. Your task is to extract the primary subject and any related statements from user queries. Here's how you should approach it:

Identify the primary subject in the query. This is often a noun or a noun phrase that forms the core focus of the query.
Extract the related statement which modifies or provides additional context about the primary subject, and response in json format.
For example:

Query: "soil type good for agriculture"
Expected Output: {'primary_subject':'soil', 'related_statement':'good for agriculture'}
Query: "buildings which is commercial"
Expected Output: {'primary_subject':'buildings', 'related_statement':'commercial'}
If a query does not explicitly mention a primary subject but provides a statement,like asking about 'where is for...' set primary_subject as None:
Query: "Where is good for planting strawberries"
Expected Output: {'primary_subject':None, 'related_statement':'good for planting strawberry'}
Query: "Where is good for planting vegetables"
Expected Output: {'primary_subject':None, 'related_statement':'good for planting vegetables'}
If there is no modifying statement, set the related_statement to None:
Query: "show greenery"
Expected Output: {'primary_subject': 'greenery', 'related_statement': None}
Your goal is to consistently apply this method to analyze and break down user queries into structured data as shown above.
    """

    if messages==None:
        messages=[]
    if geo_relation_dict!=None and 'area_calculate' not in geo_relation_dict:
            print('geo_calculate')
            ask_prompt=ask_prompt_geo_relation
    else:
        print('ask_prompt_adj')
        ask_prompt=ask_prompt_adj
    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',query))
    result=chat_single(messages,'json')
    # print(result)
    json_result=json.loads(result)
    if 'primary_subject' in json_result:


        return {'primary_subject':json_result['primary_subject'],'related_geographic_element':json_result['related_statement']}

    else:
        raise Exception('no relevant item found for: ' +query + ' in given list.')

def judge_type(query,messages=None):
    if isinstance(query,dict):
        if query['primary_subject']!=None: #没有地理关系,有related_geographic_element，是subject的形容词,object subject 被全部送入judge_type防止没有主语
            query= query['primary_subject']
        else:
            query=query['related_geographic_element']
    if query==None:
        return None
    if messages==None:
        messages=[]
    if 'building' in query.lower():
        return {'database': 'buildings'}
    ask_prompt="""
    There are two database: [soil,landuse], 
    'soil' database stores various soil types, such as swamps, wetlands, soil compositions.
    'landuse' database stores various types of urban land use like park, forest, residential area, school.
    response the correct database name given the provided data name in json format like:
    {
    'database':database
    }
    """
    if messages==None:
        messages=[]

    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',query))
    result=chat_single(messages,'json')
    # print(result)
    json_result=json.loads(result)
    if 'database' in json_result:



        return {'database':json_result['database']}

    else:
        raise Exception('no relevant item found for: ' +query + ' in given list.')


def judge_result(query,messages=None):

    if query==None:
        return None
    if messages==None:
        messages=[]

    ask_prompt="""User will give you a dict, key is a item name, value is the number of its occurrences in map, 
    describe it for user, Emphasize which items appear most often, and What types of objects are most of them? 
    Please mention you get the result from search but not from dict.
    """
    if messages==None:
        messages=[]

    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',str(query)[:3000]))
    result=chat_single(messages)
    return result

def judge_query(query,messages=None):
    if query==None:
        return None
    if messages==None:
        messages=[]
    if 'building' in query:
        return {'database': 'buildings'}
    ask_prompt="""
    
    If this query is about What soil types are the houses near the farm on?
    
    response in json format like:
    {
    'code':"
set_bounding_box("munich ismaning")
id_buildings=ids_of_type('buildings','building')
id_farmland=ids_of_type('landuse','farmland')
id_soil=ids_of_type('soil','all')
buildings_near_farmland=geo_calculate(id_farmland,id_buildings,'buffer',10)
soil_under_buildings=geo_calculate(id_soil,buildings_near_farmland['subject'],'intersects')
print(id_2_attributes(soil_under_buildings['subject']))
    "
    }
  If this query is about Which farmlands are on soil unsuitable for agriculture?
    
    response in json format like:
    {
    'code':"
set_bounding_box("munich ismaning")
id_farmland=ids_of_type('landuse','farmland')
soil_type_list = ids_of_attribute('soil') # Get soil types
soil_type_list_not_good_for_agriculture = pick_match('not good for agriculture', soil_type_list) # Get soil types which not good for agriculture
id_soil=ids_of_type('soil',soil_type_list_not_good_for_agriculture)
farmlands_on_soil=geo_calculate(id_soil,id_farmland,'contains')
print(id_2_attributes(farmlands_on_soil['subject']))
    "
    }
  If this query is about Which buildings are on soil unsuitable for buildings?
    
    response in json format like:
    {
    'code':"
set_bounding_box("munich ismaning")
id_buildings=ids_of_type('buildings','building')
soil_type_list = ids_of_attribute('soil') # Get soil types
soil_type_list_not_good_for_buildings = pick_match('not good for buildings', soil_type_list) # Get soil types which not good for buildings
id_soil=ids_of_type('soil',soil_type_list_not_good_for_buildings)
buildings_on_soil=geo_calculate(id_soil,id_buildings,'contains')
print(id_2_attributes(buildings_on_soil['subject']))
    "
    }
    """
    if messages==None:
        messages=[]

    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',query))
    result=chat_single(messages,'json')
    # print(result)
    json_result=json.loads(result)
    if 'code' in json_result:



        return {'code':json_result['code']}

    else:
        raise Exception('no relevant item found for: ' +query + ' in given list.')


# print(judge_query_first('Which farmlands are on soil unsuitable for agriculture?'))
# query="I want to know buildings around 100m of forest in munich ismaning."
# judge_bounding_box(query)
# object_subject=judge_geo_relation('What soil types are the houses on the farm on?') #primary_subject,related_geographic_element
# print(object_subject)
# graph_dict={}
# graph_type_list={}
# type_dict={}
# element_list={}
# for item_ in object_subject:
#     if object_subject[item_]!=None:
#         graph_dict[item_]=judge_type(object_subject[item_])['database']
#         graph_type_list[item_]=ids_of_attribute(graph_dict[item_])
#         type_dict[item_]=pick_match(object_subject[item_],graph_type_list[item_])
#         element_list[item_]=ids_of_type(graph_dict[item_],type_dict[item_])
#
# geo_relation_dict=judge_geo_relation(query)
# geo_calculate(element_list['related_geographic_element'],element_list['primary_subject'],geo_relation_dict['type'],geo_relation_dict['num'])
# print(judge_type('swamp'))
# id1=ids_of_attribute('soil')
# print(id1)
# att=id_2_attributes(id1)
# print(att.keys())
# query='我想知道哪个适合农业'
# a=pick_match(query,att)
# id2=ids_of_type('soil',a)
# from geo_functions import *
# # set_bounding_box("munich ismaning")
# # id_buildings=ids_of_type('buildings','building')
# set_bounding_box("munich")
# soil_type_list = ids_of_attribute('soil') # Get soil types
# soil_type_list_not_good_for_buildings = pick_match('not good for building construction', soil_type_list) # Get soil types which not good for buildings
# print(soil_type_list_not_good_for_buildings,'soil_type_list_not_good_for_buildings')
#
# id_soil=ids_of_type('soil',soil_type_list_not_good_for_buildings)
# buildings_on_soil=geo_calculate(id_soil,id_buildings,'contains')
# print(id_2_attributes(buildings_on_soil['subject']))
# graph_type_list=ids_of_attribute('soil')
# aa=pick_match('swamp',graph_type_list)
# print(aa)
#
# iii=ids_of_attribute('landuse')
# print(pick_match('parks', iii))

# id_buildings=ids_of_type('buildings','building')
# id_farmland=ids_of_type('landuse','forest')
# buildings_near_farmland=geo_calculate(id_farmland,id_buildings,'contains',10)
# print(id_2_attributes(soil_under_buildings['subject']))
# from geo_functions import *
# #
# print(pick_match('good for planting strawberry', ids_of_attribute('soil'), 'soil'))
# from rag_model_openai import build_vector_store
# soil=list((ids_of_attribute('buildings')))[:1000]
# # print(soil)
# build_vector_store(soil,'buildings')
# set_bounding_box("munich ismaning")
# a2=ids_of_type('buildings','building')
# a1=ids_of_type('landuse','forest')
# aa=geo_calculate(a1,a2,'buffer',100)
# explain=id_explain(aa)
# print(explain)
# print(judge_result(explain))
# a1=ids_of_attribute('landuse')
# a2=ids_of_attribute('buildings')
# (ids_of_type(['landuse','buildings'],a3))
# print(pick_match('school', a))
#
# print(pick_match('good fot agriculture', ids_of_attribute('soil')))

# print(judge_geo_relation("I want to know where is good for planting strawberry",None))
# print(judge_geo_relation("buildings in forest",None))
