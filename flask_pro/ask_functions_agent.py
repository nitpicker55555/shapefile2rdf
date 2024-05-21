import geo_functions
from chat_py import *
from levenshtein import are_strings_similar
import json, re
from rag_model import calculate_similarity
from rag_model_openai import calculate_similarity_openai
from geo_functions import *
import spacy
from bounding_box import find_boundbox

# 加载spaCy的英语模型
nlp = spacy.load('en_core_web_sm')
global_paring_dict = {}

new_dict_num = 0
file_path = 'global_paring_dict.jsonl'
# fclass_dict={}
# name_dict={}
# for key ,value in col_name_mapping_dict.items():
#     if key not in fclass_dict:
#         fclass_dict[key]=ids_of_attribute(key)
#     if key not in name_dict:
#         name_dict[key]=ids_of_attribute(key,'name')
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

    item_list = set()

    for item in lst:
        if string.lower() == item.lower():
            if not has_middle_space:
                return [item]
            else:
                item_list.add(item)
        if string.lower() in item.lower().split(' '):
            item_list.add(item)
    return item_list


def describe_label(query, given_list, table_name, messages=None):
    if messages == None:
        messages = []

    ask_prompt = """
    Based on the this list: %s, create imitations to match the query. Be sure to use the same language as the provided list, and be as concise as possible, offering only keywords. Response in json
    {
    'result':statement
    }
    
    """ % given_list
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
    processed = re.sub(r'\d+', '', s)
    if processed.startswith(':'):
        processed = processed[1:]
    return processed
def has_middle_space(s: str) -> bool:
    # 去掉字符串两端的空格
    stripped_s = s.strip()
    # 如果字符串去掉两端空格后的长度小于2，说明中间不可能有空格
    if len(stripped_s) < 2:
        return False
    # 检查字符串中间部分是否有空格
    return ' ' in stripped_s[1:-1]

def details_pick_chatgpt(query, given_list, table_name, messages=None):
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

    reversed_query = vice_versa(query)
    new_paring_dict = {query: [], reversed_query: []}

    for word in given_list:
        if word != '':
            messages = []
            messages.append(message_template('system', ask_prompt))
            messages.append(message_template('user', f'is "{string_process(word)}" "{query}"?'))
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
    if new_paring_dict[query] != []:
        if table_name not in global_paring_dict:
            global_paring_dict[table_name] = {}

        global_paring_dict[table_name].update(new_paring_dict)

        with open('global_paring_dict.jsonl', 'a', encoding='utf-8') as file:
            json.dump({table_name: new_paring_dict}, file)
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
        vice_list = set(given_list) - set(query_paring_list)
        new_paring_dict[query] = list(query_paring_list)
        new_paring_dict[reversed_query] = list(vice_list)
        if table_name not in global_paring_dict:
            global_paring_dict[table_name] = {}

        global_paring_dict[table_name].update(new_paring_dict)

        return new_paring_dict

    reversed_query = vice_versa(query)
    new_paring_dict = {query: [], reversed_query: []}
    # describe the target label to make match more precise

    query_paring_list = calculate_similarity_openai(table_name, query)
    if len(query_paring_list) != 0:
        result = after_match(query_paring_list)
        new_paring_dict.update(result)
        return result[query]
    else:
        target_label_describtion = describe_label(query, list(given_list)[:2], table_name)
        query_paring_list = calculate_similarity_openai(table_name, target_label_describtion)

        if len(query_paring_list) != 0:
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
    a = 1
    if 'small' in s:
        a = -1
    if len(numbers) != 0:
        return int(numbers[0]) * a
    else:
        return 1 * a  # 如果没有显式说明最大数值，则为最大的


def pick_match(query_feature_ori, table_name,verbose=False):
    # for query_feature_ori['entity_text']==table_name,
    # for query_feature_ori['entity_text']!=table_name, add query_feature_ori['entity_text'] to query_feature_ori['non_spatial_modify_statement']
    try:
        query_feature=query_feature_ori.strip()
    except Exception as e:
        print(query_feature_ori)
        raise Exception(e)
    # query_feature = query_feature_ori.replace(table_name, '')

    # print(query_feature)
    if ' and ' in query_feature:  # 复合特征
        query_list = query_feature.split(" and ")
    else:
        query_list = [query_feature]
    # print(query_list)
    match_list = {'non_area_col': {'fclass':set(),'name':set()}, 'area_num': None}
    for query in query_list:
        # print(query)
        col_name_list = ['name', 'fclass']
        if query != '':
            col_name = judge_col_name(query)
            if col_name != None:  # fclass和name的粗选
                if are_strings_similar(query, table_name):
                    match_list['non_area_col'][col_name].add('all')
                    # print(match_list)
                    continue

                given_list = ids_of_attribute(table_name, col_name)
                query = query.replace(table_name, '').replace('named', '').replace("name", '').replace("is ", '').replace('which','').replace('where','').strip()#去除两边空格
                # print(query,table_name)
                partial_similar = is_string_in_list_partial(query, given_list)
                # print(partial_similar)

                if len(partial_similar) >= 1:
                    match_list['non_area_col'][col_name].update(set(partial_similar))
                    # print('   as')
                    continue
                elif len(given_list) == 1:
                    match_list['non_area_col'][col_name].update(set(given_list))
                    continue
                else:  # 在另一个col中再次查找, 为了防止没有明确写出named
                    # col_name_list.remove(col_name)
                    # another_col=str(col_name_list[0])
                    # given_list = ids_of_attribute(table_name, another_col)
                    # partial_similar = is_string_in_list_partial(query, given_list)
                    # # print(partial_similar)
                    #
                    # if len(partial_similar) >= 1:
                    #     match_list['non_area_col'][another_col].update(set(partial_similar))
                    #     # print('   as')
                    #     continue
                    # elif len(given_list) == 1:
                    #     match_list['non_area_col'][another_col].update(set(given_list))
                    #     continue
                    # else:# fclass和name的精选

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
                                        match_list['non_area_col'][col_name].update(
                                            set(details_pick(query, given_list, table_name)))
                                    except Exception as e:
                                        raise Exception(e, query, table_name, given_list)
                                    print(f'\n\nmatch_list for {query}:', match_list)
                                else:
                                    query_modify = general_gpt('what is name of ' + query)
                                    print(query_modify + '\n')
                                    match_dict = calculate_similarity(given_list, query_modify)
                                    print('\n\nmatch_dict:', match_dict)
                                    if match_dict != {}:
                                        match_list['non_area_col'][col_name].update(set(match_dict.keys()))

            else:  # area relate query
                match_list['area_num'] = extract_numbers(query)
                continue

    if match_list == []:
        raise Exception('no relevant item found for: ' + query_feature + ' in given list.')
    # print(match_list, query_feature, table_name)
    return match_list
    # messages.append(message_template('assistant',result))


def judge_geo_relation(query, messages=None):
    sample_list=['in','contains']
    if 'under' in query:
        return {'type':'contains','num':0}
    if 'on' in query:
        return {'type':'in','num':0}

    if query in sample_list:
        return {'type':query,'num':0}
    if messages == None:
        messages = []
    ask_prompt = """You are a search query analyst tasked with analyzing user queries to determine if they include 
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
    if messages == None:
        messages = []

    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', query))
    result = chat_single(messages, 'json')
    # print(result)
    json_result = json.loads(result)
    if 'geo_calculations' in json_result:
        if json_result['geo_calculations']['exist']:
            # object_dict=judge_object_subject(query)
            if 'num' in json_result['geo_calculations']:
                return {'type': json_result['geo_calculations']['type'], 'num': json_result['geo_calculations']['num']}
            else:
                return {'type': json_result['geo_calculations']['type'], 'num': 0}
        else:
            return None
    else:
        raise Exception('no relevant item found for: ' + query + ' in given list.')


def judge_object_subject_multi(query, messages=None):
    multi_prompt = """
You are an excellent linguist，Help me identify all entities from this statement and spatial_relations. Please format your response in JSON. 
Example:
query: "I want to know which soil types the commercial buildings near farm on"
response:
{
"entities":
[
  {
    'entity_text': 'soil',
  },
  {
    'entity_text': 'commercial buildings',
  },
    {
    'entity_text': 'farm',
  }
],
 "spatial_relations": [
    {"type": "on", "head": 1, "tail": 0},
    {"type": "near", "head": 1, "tail": 2}
  ]
}

query: "I want to know residential area in around 100m of land which is forest"
response:
{
  "entities": [
    {
      "entity_text": "residential area",
    },
    {
      "entity_text": "land which is forest",
    },
  ],
  "spatial_relations": [
    {"type": "in around 100m of", "head": 0, "tail": 1},
  ]
}
query: "show land which is university and has name TUM"
response:
{
  "entities": [
    {
      "entity_text": "land which is university and has name TUM",
    },
  ],
  "spatial_relations": []
}
query: "show land which is university or bus stop"
response:
{
  "entities": [
    {
      "entity_text": "land which is university or bus stop",
    },
  ],
  "spatial_relations": []
}
Notice, have/has should be considered as spatial_relations:
like: residential area which has buildings.
    """
    if messages == None:
        messages = []
    ask_prompt = multi_prompt
    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', query))
    result = chat_single(messages, 'json', 'gpt-4o-2024-05-13')
    # print(result)
    json_result = json.loads(result)
    return json_result

def remove_non_spatial_modify_statements(data):
    for entity in data.get("entities", []):
        if "non_spatial_modify_statement" in entity:
            del entity["non_spatial_modify_statement"]
    return data
def id_list_of_entity(query):
    """
    graph{num} = judge_type(multi_result['entities'][{num}])["database"]
    type{num} = pick_match(multi_result['entities'][{num}], graph{num})
    :param query:
    :return:
    """
    graph_str = judge_type(query)['database']
    type_str = pick_match(query, graph_str)
    ids_list = ids_of_type(graph_str, type_str)
    return ids_list


def find_negation(text):
    # 使用spaCy处理文本
    doc = nlp(text)

    # 检查是否有依存关系为'neg'的词
    for token in doc:
        if token.dep_ == 'neg':
            return True, token.text
    return False, None


def judge_bounding_box(query,filter=False, messages=None):
    if messages == None:
        messages = []
    new_query=None
    # if 'munich ismaning' in query.lower():
    #     return 'munich ismaning'
    locations=['Munich', 'Augsburg', 'Munich Moosach', 'Munich Maxvorstadt', 'Munich Ismaning', 'Freising',
         'Oberschleissheim']
    final_address=[]
    for address in locations:
        if address.lower() in query.lower():
            final_address.append(address)
    if filter:
        new_query=process_query(str({'location name':final_address,'query':query}))
    return final_address, new_query

    # return final_address


def geo_filter(query,id_list_subject, id_list_object):
    """
    geo_relation{num}=judge_geo_relation(multi_result['spatial_relations'][{num}]['type'])
    geo_result{num}=geo_calculate(id_list{relations['head']},id_list{relations['tail']},geo_relation{num}['type'],geo_relation{num}['num'])

    :param query:
    :return:
    """
    if isinstance(id_list_subject,str):
        id_list_subject=id_list_of_entity(id_list_subject)
    if isinstance(id_list_object, str):
        id_list_object = id_list_of_entity(id_list_object)

    versa_sign, negation_word = find_negation(query)
    if versa_sign:
        query = query.replace(negation_word, '')
    geo_relation = judge_geo_relation(query)
    geo_result = geo_calculate(id_list_subject, id_list_object, geo_relation['type'], geo_relation['num'], versa_sign=versa_sign)
    return geo_result


def judge_object_subject(query, geo_relation_dict, messages=None):
    print('query for judge_object_subject:', query)

    if messages == None:
        messages = []
    ask_prompt_geo_relation = """
    
    Please response in json format: {'entity_text':entity_text, 
    'non_spatial_modify_statement':non_spatial_modify_statement}. 
    
    For example, when I ask, 'I want to know the 
    residential area near the swamp,' you should respond with: {'entity_text':'residential area', 
    'non_spatial_modify_statement':'swamp'}. Similarly, for 'I want to know the buildings around 100m of forests, 
    ' the response should be:  {'entity_text':'buildings', 'non_spatial_modify_statement':'forests'}, 
    
    If there is no non_spatial_modify_statement, non_spatial_modify_statement should be set as None, example: 
    for 'the largest 5 forest', non_spatial_modify_statement is None. """
    ask_prompt_adj = """
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

    if messages == None:
        messages = []
    if geo_relation_dict != None and 'area_calculate' not in geo_relation_dict:
        print('geo_calculate')
        ask_prompt = ask_prompt_geo_relation
    else:
        print('ask_prompt_adj')
        ask_prompt = ask_prompt_adj
    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', query))
    result = chat_single(messages, 'json')
    # print(result)
    json_result = json.loads(result)
    if 'entity_text' in json_result:

        return {'entity_text': json_result['entity_text'],
                'non_spatial_modify_statement': json_result['non_spatial_modify_statement']}

    else:
        raise Exception('no relevant item found for: ' + query + ' in given list.')


def judge_type(query, messages=None):
    if isinstance(query, dict):
        query = str(query)
    #     if query['entity_text']!=None: #没有地理关系,有non_spatial_modify_statement，是subject的形容词,object subject 被全部送入judge_type防止没有主语
    #         query= query['entity_text']
    #     else:
    #         query=query['non_spatial_modify_statement']
    if query == None:
        return None
    if messages == None:
        messages = []
    if 'building' in query.lower() and 'soil' not in query.lower():
        return {'database': 'buildings'}

    if 'land' in query.lower() and 'soil' not in query.lower():
        return {'database': 'land'}
    if 'soil' in query.lower():
        return {'database': 'soil'}

    ask_prompt = """
    There are two database: [soil,land], 
    'soil' database stores various soil types, such as swamps, wetlands, for agriculture or planting or construction.
    'land' database stores various types of urban land use like park, forest, residential area, school, university, water, river.
    response the correct database name given the provided data name in json format like:
    {
    'database':database
    }
    """
    if messages == None:
        messages = []

    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', str(query)))
    result = chat_single(messages, 'json')
    # print(result)
    json_result = json.loads(result)
    if 'database' in json_result:

        return {'database': json_result['database']}

    else:
        raise Exception('no relevant item found for: ' + str(query) + ' in given list.')


def general_gpt(query, messages=None):
    print(query)
    if isinstance(query, dict):
        query = str(query)
    if query == None:
        return None
    if messages == None:
        messages = []

    ask_prompt = """

You have following tools available to answer user queries, please only write code, do not say anything else except user ask you to describe:
I have three kinds of data:buildings, land (different kinds of area), soil.
1.set_bounding_box(address):
Input:An address which you want search limited in.
Output:None, it establishes a global setting that restricts future searches to the defined region.
Usage:By providing an address, you can limit the scope of subsequent searches to a specific area. This function does not produce any output, but it establishes a global setting that restricts future searches to the defined region. For example, if you want to find buildings in Munich, you should first set the bounding box to Munich by using set_bounding_box("Munich").
Notice:Please include the directional words like east/south/east/north of query in the address sent to set_bounding_box

2.id_list_of_entity(description of entity):
Input: Description of the entity, like adj or prepositional phrase like good for commercial,good for planting potatoes.
Output: A list of IDs (id_list) corresponding to the described entity.
Usage: Use this function to obtain an id_list which will be used as input in the following functions.
Notice: Some times the description may have complex description like:"I want to know land which named see and is water", input the whole description into function.
Notice: Do not input geographical relation like 'in/on/under/in 200m of/close' into this function, it is not description of entity.

3.geo_filter('their geo_relation',id_list_subject, id_list_object):
Input: Two id_lists (one as subject and one as object) and their corresponding geographical relationship.
Output: A dict contains 'subject','object' two keys as filtered id_lists based on the geographical relationship.
Usage: This function is used only when the user wants to query multiple entities that are geographically related. Common geographical relationships are like: 'in/on/under/in 200m of/close/contains...'
Notice: id_list_subject should be the subject of the geo_relation, in example: soil under the buildings, soil is subject.

4.area_filter(id_list, num):
Notice: only use it when user wants to filter result by area.
Input: An id_list and a number representing either the maximum or minimum count.
Output: An id_list filtered by area.
Usage: Use this function only when the user explicitly asks for the entities with the largest or smallest areas. For example, input 3 for the largest three, and -3 for the smallest three.

5.id_list_explain(variable name, category to explain(name or type)):
Input: id_list generated by function 'id_list_of_entity' or 'geo_filter' or 'area_filter'
Output: A dictionary containing the count of each type/name occurrence.
Usage: Use this function to provide explanations based on user queries.

Please always set an output variable for each function you called. Variable in history is available to call.
If user ask you to draw a diagram, please always use the true variable in previous code to draw but not assume fake value.
    """
    if messages == None:
        messages = []

    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', str(query)))
    result = chat_single(messages, '','gpt-4o-2024-05-13')
    return result


def chart_agent(query, messages=None):
    if query == None:
        return None
    if messages == None:
        messages = []

    ask_prompt = """
    You need to give me the code for drawing a diagram according to the query.
    You will be given a code block and you need to pick one appropriate variable in them and draw it.
    If the variable has string 'explain'， it means this variable is a occur frequency dict, its key name is string name,
    key value is number.
    otherwise, the variable is a dict with geo wkt as its key value, still string in its key name.
    
    Please notice, always use the variable itself to draw diagram but not assume fake values.
    """
    if messages == None:
        messages = []

    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', str(query)))
    result = chat_single(messages,'','gpt-4o-2024-05-13')
    return result

def routing_agent(query, messages=None):
    if query == None:
        return None
    if messages == None:
        messages = []

    ask_prompt = """
You are a task planner. Based on the user's query, select the next function to execute and inform them of the task to be performed. There are three functions available:

explain_agent: Explain information to the user.
chart_agent: Create charts for the user.
query_agent: Query information for the user.
Choose the most appropriate function and provide clear instructions on what work needs to be done.
output as json format like:

    """
    if messages == None:
        messages = []

    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', str(query)))
    result = chat_single(messages,'json')

    return json.loads(result)['function']


def set_bounding_box(region_name, query=None):
    if region_name=='':
        geo_functions.globals_dict={}
        return
    if region_name != None:
        locations = ['Munich', 'Augsburg', 'Munich Moosach', 'Munich Maxvorstadt', 'Munich Ismaning', 'Freising',
                     'Oberschleissheim']

        location_name=''
        for i in locations:
            if i.lower() in region_name.lower():

                location_name=i

        if len(region_name.lower().replace(location_name.lower(),'').strip())!=0: #除了地名外还有额外修饰
                print(' s')
                query=region_name
                region_name=location_name

        geo_functions.globals_dict["bounding_box_region_name"] = region_name
        geo_functions.globals_dict['bounding_coordinates'], geo_functions.globals_dict['bounding_wkb'], response_str = find_boundbox(region_name)

        if query!=None:

            modify_query={
                'Original_bounding_box_of_'+region_name:str(geo_functions.globals_dict['bounding_coordinates']),
                          "query":query
                          }
            print(modify_query)
            modified_box=process_boundingbox(str(modify_query))
            print(modified_box)
            geo_functions.globals_dict['bounding_coordinates'], geo_functions.globals_dict['bounding_wkb'], response_str = find_boundbox(modified_box,'changed')
            # print(wkb.loads(bytes.fromhex(geo_functions.globals_dict['bounding_wkb'])))

        geo_dict = {
            geo_functions.globals_dict["bounding_box_region_name"]: (wkb.loads(bytes.fromhex((geo_functions.globals_dict['bounding_wkb']))))}
   
        return {'geo_map': geo_dict}
    else:
        return None
def process_boundingbox(query,messages=None):
    if query == None:
        return None
    if messages == None:
        messages = []

    ask_prompt = """You will receive an original bounding box coordinate list and an address. Based on the 
    directional modifier (e.g., south, west, east, north, center) mentioned in the query for this address, you need to adjust 
    the bounding box accordingly.
    
     The output should be in JSON format as follows: 

json
{
  "boundingbox": []
}
        """
    if messages == None:
        messages = []

    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', str(query)))
    result = chat_single(messages, 'json', 'gpt-4o-2024-05-13')

    return json.loads(result)['boundingbox']

def process_query(query,messages=None):
    if query == None:
        return None
    if messages == None:
        messages = []

    ask_prompt = """You need to rewrite the user's query to remove directional words like south/north/west/east/center...etc and location name.
    Response in json:
    json
{
  "query_filtered": ''
}

    Example:
    Query:I want to know land which named see in south of Munich 
    Response:
    json
{
  "query_filtered": 'I want to know land which named see'
}


        """
    if messages == None:
        messages = []

    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', str(query)))
    result = chat_single(messages, 'json', 'gpt-4o-2024-05-13')

    return json.loads(result)['query_filtered']
#ge_object_subject_multi('I want to know buildings close to largest 5 park ')
# a={'clothes', 'pitch', 'playground', 'scrub', 'newsagent', 'mobile_phone_shop', 'biergarten', 'kindergarten', 'track', 'bank', 'shelter', 'university', 'bicycle_rental', 'meadow', 'public_building', 'allotments', 'castle', 'toilet', 'parking_multistorey', 'parking', 'tourist_info', 'hostel', 'forest', 'bus_stop', 'butcher', 'memorial', 'museum', 'jeweller', 'restaurant', 'bus_station', 'embassy', 'graveyard', 'parking_underground', 'fast_food', 'water_works', 'furniture_shop', 'retail', 'hospital', 'riverbank', 'kiosk', 'commercial', 'courthouse', 'park', 'theatre', 'attraction', 'tower', 'grass', 'helipad', 'bicycle_shop', 'school', 'cemetery', 'water', 'cafe', 'fountain', 'fire_station', 'recreation_ground', 'bar', 'taxi', 'arts_centre', 'industrial', 'college', 'bookshop', 'library', 'monument', 'comms_tower', 'bakery', 'supermarket', 'chemist', 'hairdresser', 'police', 'artwork', 'convenience', 'parking_bicycle', 'hotel', 'residential'}
# b={'entity_text': 'land', 'non_spatial_modify_statement': 'name technische universität münchen,largest 3,education'}
# b={'entity_text': 'buildings', 'non_spatial_modify_statement': 'name Hauptbahnhof'}
# print(pick_match(b,'buildings'))
# print(general_gpt('I want to know forest in residential area'))
# query='I want to know commercial buildings in residential area which around 10m of hospital in north of Munich'
# address_list,query_without_address=judge_bounding_box(query)
# entity_suggest=judge_object_subject_multi(query_without_address)
# suggest_info=f"#address_list:{address_list},entity_suggest:{(entity_suggest)}"
# set_bounding_box('Oberschleissheim')
# id1=id_list_of_entity('land which named See')
# print(id_list_explain(id1, 'area'))
# print(general_gpt(query+suggest_info))
# a={'entity_text': 'soil', 'non_spatial_modify_statement': ''}
# a={'entity_text': 'land', 'non_spatial_modify_statement': 'name technische'}
# print(pick_match(a,'land'))
# print(is_string_in_list_partial('technische', ids_of_attribute('land', 'name')))
# print(judge_object_subject_multi('residential area close to park'))
# a=ids_of_attribute('buildings','name')
# print(is_string_in_list_partial('Studentenwohnheim', a))
# print(a)
# pick_match('named see','land')
# query="""
# Previous code:*9+-
# residential_area_ids = id_list_of_entity("residential area")
# buildings_ids = id_list_of_entity("buildings")
# result = geo_filter(buildings_ids, residential_area_ids, 'in')
# User-query:
# Can you explain me the residential area you filtered by geo?
# """
# # print(explain_agent(query))
#
# print(process_boundingbox('Munich:[48.178202, 48.248098, 11.625186, 11.804967],I want to know buildings in north Munich'))
# a={ 'Waginger See', 'Tierarztpraxis Eberhard', 'Holnstainer Grundschule', 'Hölbinger Weiher', 'Triebenbach', 'Instanbul Kebap', 'Bayersoier Hof', 'Wertstoffhof Weichering', 'Kinderhaus "kleine Hände - große Taten"', 'Haus Thier', 'Lechstaustufe 8 - Sperber', 'Schlatt', 'SV Wangen', 'Realschule', 'Langbürgner See', 'Wallner Alm', 'Campus West Garching Forschungszentrum', 'Hub', 'Eichendorffplatz', 'Tennisclub am Brandl e.V.', 'Genrlinden (S)', 'Streetball-Platz', 'Reutbergstüberl', 'Café Konditorei Schwarz', 'Schlagenhofen', 'Hundeplatz', 'Am Saum', 'Der Haartreff', 'Sultan Imbiss', 'P Arztpraxis', 'Städtisches Adolf-Weber-Gymnasium', 'NAT Arena', 'SV Alzgern', 'Gasthof Steininger', 'Comfort Hotel', 'Wassertretanlage', 'EKC Rottach-Egern', 'Scherer', 'Hanneslabauer', 'Cobra', 'Beim Jäger', 'Bogenschießanlage', 'Hans Kurfer Möbelhaus', 'Wasserrad', 'Gewerbegebiet Feldlerchenstraße', 'Bräuhaus', 'Brummi-Bistro', 'Marka', 'Opel', 'Sudetendeutsches Museum', 'Tipbet', 'Alpenhäusl', 'Gasthaus Huber', 'Höhe', 'Kindertagesstätte Christkönig', 'Betzwiese', 'Mariahilfplatz', 'Karakuş Automobile', 'Kemmler Baustoffe & Fliesen', 'Amtsgericht Landsberg am Lech', 'Hotel Seehof'}
# pick_match('land named see','land')
# print(is_string_in_list_partial('see', a))
# set_bounding_box("Munich")
# print(id_list_of_entity('buildings'))
# judge_bounding_box()
# print(pick_match('land', 'land'))
# print(judge_bounding_box('show all land in center of Oberschleissheim'))
# set_bounding_box('Oberschleissheim')
# id1=id_list_of_entity('land forest')
# id2=id_list_of_entity('buildings')
# aa=geo_filter('in',id2,id1)
# print(aa.keys())
# print(aa['subject'])
# print(id_list_explain(aa['subject'],'name'))
# id_list_see_water = id_list_of_entity("land which named see and is water")
# print(id_list_see_water)
# set_bounding_box('Oberschleissheim','show me land in North of Oberschleissheim')
# forest_ids = id_list_of_entity("forest")
# building_ids = id_list_of_entity("buildings")
# geo_result = geo_filter('in', building_ids, forest_ids)
# soil_ids = id_list_of_entity("soil")
# geo_result_soil = geo_filter('under', soil_ids,geo_result['subject'])
# print(geo_result_soil)
# print(list(geo_result['subject']['id_list'])[:1000])
# print(list(soil_ids['id_list'])[:1000])
# set_bounding_box('Oberschleissheim','show me forest under buildings in north of Oberschleissheim')
# id_list_forest = id_list_of_entity("forest")
# id_list_buildings = id_list_of_entity("buildings")
# geo_relation_result = geo_filter('under', id_list_forest, id_list_buildings)
# id_list_soil = id_list_of_entity("soil")
# geo_relation_soil_result = geo_filter('under', geo_relation_result['object'], id_list_soil)
# id_list_explain_soil = id_list_explain(geo_relation_soil_result['object'], 'type')
# print(geo_relation_soil_result)
# type_list=ids_of_attribute('land')

# id_list_lake_landuse = id_list_of_entity("land is lake")
# print(set_bounding_box('Munich Moosach'))

# set_bounding_box('center 3km*3kn of munich')