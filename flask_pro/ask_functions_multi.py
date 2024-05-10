import spacy

from chat_py import *
from levenshtein import are_strings_similar
import json,re
from rag_model import calculate_similarity
from rag_model_openai import calculate_similarity_openai
from geo_functions import *
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
def is_string_in_list_partial(string, lst):
    # print(string,lst)

    item_list=set()
    for item in lst:
        if string==item.lower():
            return [item]
        if string.lower() in item.lower().split(' '):
            item_list.add(item)
    return item_list
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

def judge_col_name(statement_split):

    if 'name' in statement_split:
        return 'name'
    elif judge_area(statement_split):
        return None
    else:
        return 'fclass'

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
def judge_area(type):
    if 'large' in str(type) or 'small' in str(type) or 'big' in str(type):
        return True
    else:
        return False
def extract_numbers(s):
    # print(s)
    # 使用正则表达式找出字符串中的所有数字
    numbers = re.findall(r'\d+', s)
    # print(numbers)
    # 将找到的数字字符串转换为整数
    a=1
    if 'small' in s:
       a=-1
    if len(numbers)!=0:
        return int(numbers[0])*a
    else:return 1*a #如果没有显式说明最大数值，则为最大的
def pick_match(query_feature_ori,table_name):
    #for query_feature_ori['entity_text']==table_name,
    #for query_feature_ori['entity_text']!=table_name, add query_feature_ori['entity_text'] to query_feature_ori['non_spatial_modify_statement']

    if query_feature_ori['non_spatial_modify_statement']:#如果有non_spatial_modify_statement，使用non_spatial_modify_statement。
        if 'type' in query_feature_ori['non_spatial_modify_statement']:
            query_feature_ori['non_spatial_modify_statement']=query_feature_ori['non_spatial_modify_statement'].replace('types','').replace('type','')


        query_feature = query_feature_ori['non_spatial_modify_statement']
        if query_feature_ori['entity_text'] != table_name: #如果entity_text和table名不一致，那么将entity_text也加入作为判断
            query_feature+=f' {query_feature_ori["entity_text"]}'

    else:
        query_feature = query_feature_ori['entity_text']#如果没有non_spatial_modify_statement，那么把entity当作pick的判断语


    if ',' in query_feature:#复合特征
        query_list=query_feature.split(",")
    else:
            query_list=[query_feature]
    match_list={'non_area_col':{},'area_num':None}
    for query in query_list:

        if query!='':
            col_name=judge_col_name(query)
            if col_name!=None:                                                  #fclass和name的粗选
                if are_strings_similar(query,table_name):
                    match_list['non_area_col'][col_name] ='all'
                    # print('match')
                    continue
                if col_name not in match_list['non_area_col']:
                    match_list['non_area_col'][col_name] =set()
                given_list=ids_of_attribute(table_name,col_name)
                query = query.replace('named', '').replace("name ", '').replace("is ", '')
                partial_similar=is_string_in_list_partial(query,given_list)

                if len(partial_similar)>=1:
                    match_list['non_area_col'][col_name].update(set(partial_similar))
                    # print('   as')
                    continue
                elif len(given_list)==1:
                    match_list['non_area_col'][col_name].update(set(given_list))
                    continue
                else:                                                           #fclass和name的精选



                        find_pre_matched = {}
                        if table_name in global_paring_dict:
                            if list(global_paring_dict[table_name].keys()) != []:
                                find_pre_matched = calculate_similarity(list(global_paring_dict[table_name].keys()), query)

                        if find_pre_matched != {}:
                            print(f'find_pre_matched for {query}:', find_pre_matched)
                            match_list_key = list(find_pre_matched.keys())[0]
                            match_list['non_area_col'][col_name].update(set(global_paring_dict[table_name][match_list_key]))
                            # return match_list
                        else:
                            match_dict = calculate_similarity(given_list, query)
                            print(query + '\n')
                            # print(given_list)
                            print('\n\nmatch_dict:', match_dict)
                            if match_dict != {}:
                                 match_list['non_area_col'][col_name].update(set(match_dict.keys()))

                            else:
                                if col_name == 'fclass':
                                    try:
                                        match_list['non_area_col'][col_name].update(set(details_pick(query, given_list, table_name)))
                                    except Exception as e:
                                        raise Exception(e,query,table_name,given_list)
                                    print(f'\n\nmatch_list for {query}:', match_list)
                                else:
                                    query_modify=general_gpt('what is name of '+query)
                                    print(query_modify + '\n')
                                    match_dict = calculate_similarity(given_list, query_modify)
                                    print('\n\nmatch_dict:', match_dict)
                                    if match_dict != {}:
                                        match_list['non_area_col'][col_name].update(set(match_dict.keys()))

            else:#area relate query
                match_list['area_num'] = extract_numbers(query)
                continue


    if match_list==[]:
        raise Exception('no relevant item found for: ' +query_feature + ' in given list.')

    return match_list
    # messages.append(message_template('assistant',result))

def judge_bounding_box(query,messages=None):
    if messages==None:
        messages=[]
    if 'munich ismaning' in query.lower():
        return 'munich ismaning'


    # 加载 spaCy 的英语模型
    nlp = spacy.load("en_core_web_sm")

    # 处理文本
    doc = nlp(query)

    # 存储地名的起始和结束索引
    start_index = None
    end_index = None

    # 找到地名的起始和结束索引
    for i, token in enumerate(doc):
        if token.ent_type_ == "GPE":
            if start_index is None:
                start_index = i
            end_index = i

    # 如果找到了地名，则删除地名及其前面的介词
    if start_index is not None and end_index is not None:
        # 提取地名
        location = doc[start_index:end_index + 1].text
        # 删除地名及其前面的介词
        while start_index > 0 and doc[start_index - 1].pos_ == "ADP":
            start_index -= 1
        updated_text = doc[:start_index].text + doc[end_index + 1:].text
        return location, updated_text.strip()
    else:
        return None, query.strip()

def judge_geo_relation(query,messages=None):
    if messages==None:
        messages=[]
    ask_prompt="""You are a search query analyst tasked with analyzing user queries to determine if they include 
    geographical relationships. For each query, assess if it contains any of the following geographical operations: [
    'intersects', 'contains','in', 'buffer', 'area_calculate']. Provide a response indicating whether the query includes a 
    geographical calculation and, if so, which type. Response in json format. Examples of expected analyses are as follows: 

Query: "100m around of"
Response:
{
    "geo_calculations": {
        "exist": true,
        "type": "buffer",
        "num": 100
    }
}
Query: "have/contains/under"
Reasoning: if query is about have/contains/under, type of geo_calculations is contains.
Response:
{
    "geo_calculations": {
        "exist": true,
        "type": "contains",
        "num": 0
    }
}
Query: "in/within/on"
Reasoning: if query is about in/within, type of geo_calculations is in.
Response:
{
    "geo_calculations": {
        "exist": true,
        "type": "in",
        "num": 0
    }
}
Query: "near/close/neighbour"
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
def judge_object_subject_multi(query,messages=None):
    multi_prompt="""
You are an excellent linguist，Help me identify all entities from this statement and their non_spatial_modify_statement and spatial_relations. Please format your response in JSON. 
Example:
query: "I want to know which soil types the commercial buildings near farm on"
response:
{
"entities":
[
  {
    'entity_text': 'soil',
    'non_spatial_modify_statement': ""
  },
  {
    'entity_text': 'buildings',
    'non_spatial_modify_statement': "commercial"
  },
    {
    'entity_text': 'farm',
    'non_spatial_modify_statement': null
  }
],
 "spatial_relations": [
    {"type": "on", "head": 1, "tail": 0},
    {"type": "near", "head": 1, "tail": 2}
  ]
}

query: "I want to know commercial kinds of buildings in around 100m of landuse which is forest"
response:
{
  "entities": [
    {
      "entity_text": "buildings",
      "non_spatial_modify_statement": "commercial"
    },
    {
      "entity_text": "landuse",
      "non_spatial_modify_statement": "forest"
    },
  ],
  "spatial_relations": [
    {"type": "in around 100m of", "head": 0, "tail": 1},
  ]
}
query: "show landuse which is university and has name TUM"
response:
{
  "entities": [
    {
      "entity_text": "landuse",
      "non_spatial_modify_statement": "university,name TUM"
    },
  ],
  "spatial_relations": []
}
query: "show landuse which is university or bus stop"
response:
{
  "entities": [
    {
      "entity_text": "landuse",
      "non_spatial_modify_statement": "university,bus stop"
    },
  ],
  "spatial_relations": []
}
Notice, have/has should be considered as spatial_relations:
like: residential area which has buildings.
    """
    if messages==None:
        messages=[]
    ask_prompt=multi_prompt
    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',query))
    result=chat_single(messages,'json','gpt-4-turbo')
    # print(result)
    json_result=json.loads(result)
    return json_result
# def judge_graph_type(query):

def judge_object_subject(query,geo_relation_dict,messages=None):
    print('query for judge_object_subject:',query)

    if messages==None:
        messages=[]
    ask_prompt_geo_relation="""
    
    Please response in json format: {'entity_text':entity_text, 
    'non_spatial_modify_statement':non_spatial_modify_statement}. 
    
    For example, when I ask, 'I want to know the 
    residential area near the swamp,' you should respond with: {'entity_text':'residential area', 
    'non_spatial_modify_statement':'swamp'}. Similarly, for 'I want to know the buildings around 100m of forests, 
    ' the response should be:  {'entity_text':'buildings', 'non_spatial_modify_statement':'forests'}, 
    
    If there is no non_spatial_modify_statement, non_spatial_modify_statement should be set as None, example: 
    for 'the largest 5 forest', non_spatial_modify_statement is None. """
    ask_prompt_adj="""
You are a query analysis expert. Your task is to extract the primary subject and any related statements from user queries. Here's how you should approach it:

Identify the primary subject in the query. This is often a noun or a noun phrase that forms the core focus of the query.
Extract the related statement which modifies or provides additional context about the primary subject, and response in json format.
For example:
Query: "show commercial buildings"
Expected Output: {'entity_text':'buildings', 'non_spatial_modify_statement':'commercial'}
Query: "soil type good for agriculture"
Expected Output: {'entity_text':'soil', 'non_spatial_modify_statement':'good for agriculture'}
Query: "buildings which is commercial"
Expected Output: {'entity_text':'buildings', 'non_spatial_modify_statement':'commercial'}
If a query does not explicitly mention a primary subject but provides a statement,like asking about 'where is for...' set entity_text as None:
Query: "Where is good for planting strawberries"
Expected Output: {'entity_text':None, 'non_spatial_modify_statement':'good for planting strawberry'}
Query: "Where is good for planting vegetables"
Expected Output: {'entity_text':None, 'non_spatial_modify_statement':'good for planting vegetables'}
If there is no modifying statement, set the non_spatial_modify_statement to None:
Query: "show greenery"
Expected Output: {'entity_text': 'greenery', 'non_spatial_modify_statement': None}
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
    if 'entity_text' in json_result:


        return {'entity_text':json_result['entity_text'],'non_spatial_modify_statement':json_result['non_spatial_modify_statement']}

    else:
        raise Exception('no relevant item found for: ' +query + ' in given list.')

def judge_type(query,messages=None):
    if isinstance(query,dict):
        query=str(query)
    #     if query['entity_text']!=None: #没有地理关系,有non_spatial_modify_statement，是subject的形容词,object subject 被全部送入judge_type防止没有主语
    #         query= query['entity_text']
    #     else:
    #         query=query['non_spatial_modify_statement']
    if query==None:
        return None
    if messages==None:
        messages=[]
    if 'building' in query.lower() and 'soil' not in query.lower():
        return {'database': 'buildings'}


    ask_prompt="""
    There are two database: [soil,landuse], 
    'soil' database stores various soil types, such as swamps, wetlands, soil compositions.
    'landuse' database stores various types of urban land use like park, forest, residential area, school, university.
    response the correct database name given the provided data name in json format like:
    {
    'database':database
    }
    """
    if messages==None:
        messages=[]

    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',str(query)))
    result=chat_single(messages,'json')
    # print(result)
    json_result=json.loads(result)
    if 'database' in json_result:



        return {'database':json_result['database']}

    else:
        raise Exception('no relevant item found for: ' +str(query) + ' in given list.')
def general_gpt(query,messages=None):
    if isinstance(query,dict):
        query=str(query)
    if query==None:
        return None
    if messages==None:
        messages=[]

    ask_prompt="""
    Please answer the question in few words, directly answer, no other words.
    response in json format like:
    {
    'result':answer
    }
    """
    if messages==None:
        messages=[]

    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',str(query)))
    result=chat_single(messages,'json')
    # print(result)
    json_result=json.loads(result)
    if 'result' in json_result:



        return json_result['result']

    else:
        raise Exception('no relevant item found for: ' +str(query) + ' in given list.')



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


# judge_object_subject_multi('I want to know buildings close to largest 5 park ')
# a={'clothes', 'pitch', 'playground', 'scrub', 'newsagent', 'mobile_phone_shop', 'biergarten', 'kindergarten', 'track', 'bank', 'shelter', 'university', 'bicycle_rental', 'meadow', 'public_building', 'allotments', 'castle', 'toilet', 'parking_multistorey', 'parking', 'tourist_info', 'hostel', 'forest', 'bus_stop', 'butcher', 'memorial', 'museum', 'jeweller', 'restaurant', 'bus_station', 'embassy', 'graveyard', 'parking_underground', 'fast_food', 'water_works', 'furniture_shop', 'retail', 'hospital', 'riverbank', 'kiosk', 'commercial', 'courthouse', 'park', 'theatre', 'attraction', 'tower', 'grass', 'helipad', 'bicycle_shop', 'school', 'cemetery', 'water', 'cafe', 'fountain', 'fire_station', 'recreation_ground', 'bar', 'taxi', 'arts_centre', 'industrial', 'college', 'bookshop', 'library', 'monument', 'comms_tower', 'bakery', 'supermarket', 'chemist', 'hairdresser', 'police', 'artwork', 'convenience', 'parking_bicycle', 'hotel', 'residential'}
# b={'entity_text': 'landuse', 'non_spatial_modify_statement': 'name technische universität münchen,largest 3,education'}
# b={'entity_text': 'buildings', 'non_spatial_modify_statement': 'name Hauptbahnhof'}
# print(pick_match(b,'buildings'))
# print(general_gpt('user wants to search name of tum, what is its full name'))
# a={'entity_text': 'soil', 'non_spatial_modify_statement': ''}
# a={'entity_text': 'landuse', 'non_spatial_modify_statement': 'name technische'}
# print(pick_match(a,'landuse'))
# print(is_string_in_list_partial('technische', ids_of_attribute('landuse', 'name')))
# print(judge_object_subject_multi('residential area close to park'))
# a=ids_of_attribute('buildings','name')
# print(is_string_in_list_partial('Studentenwohnheim', a))
# print(a)