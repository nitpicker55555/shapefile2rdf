from chat_py import *

import json,re
from rag_model import calculate_similarity
global_paring_dict={}
new_dict_num=0
file_path = 'global_paring_dict.jsonl'
if os.path.exists(file_path):
    with open('global_paring_dict.jsonl', 'r', encoding='utf-8') as file:
        # 逐行读取文件内容
        for line in file:
            # 解析 JSON 字符串为字典
            new_dict_num+=1
            current_dict = json.loads(line)

            # 合并字典
            global_paring_dict.update(current_dict)
    print('Found pre_pairing_dict: ',new_dict_num)
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
def details_pick(query,given_list,messages=None):

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
    global_paring_dict.update(new_paring_dict)
    with open('global_paring_dict.jsonl','a',encoding='utf-8') as file:
        json.dump(new_paring_dict, file)
        file.write('\n')
    return new_paring_dict[query]
def pick_match(query,given_list):
    if query in given_list:
        return query
    if 'building' in query:
        return 'building'
    match_dict=calculate_similarity(given_list,query)
    print(query+'\n')
    print(given_list)
    print('\n\nmatch_dict:',match_dict)
    if match_dict!={}:
        return list(match_dict.keys())

    else:
        find_pre_matched=calculate_similarity(list(global_paring_dict.keys()),query)
        if find_pre_matched!={}:
            print('find_pre_matched:',find_pre_matched)
            match_list_key=list(find_pre_matched.keys())[0]
            match_list=global_paring_dict[match_list_key]
        else:
            match_list=details_pick(query,given_list)
        print('\n\nmatch_list:', match_list)
        if match_list==[]:
            raise Exception('no relevant item found for: ' +query + ' in given list.')
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
    ask_prompt="""
If the query includes sections about geospatial calculations such as intersects, contains, buffer, or area calculations, please respond with the JSON format indicating whether these calculations exist, what type it is('it should be single type'), and the number mentioned. The JSON should look like this:

```json
{
    "geo_calculations": {
        "exist": true,
        "type": "type",
        "num": "num"
    }
}
```
If query is about 'near/close', geospatial calculations should be buffer with num 10.
If query is about largest n elements, geospatial calculations should be area_calculate with num n.
If query is about 'in/on', geospatial calculations should be contains.
If these calculations are not included in the query, respond with:

```json
{
    "geo_calculations": {
        "exist": false
    }
}
```

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
def judge_object_subject(query,messages=None):
    print('query for judge_object_subject:',judge_object_subject)
    if messages==None:
        messages=[]
    ask_prompt="""Please provide information in the following json format: {'primary_subject':primary_subject, 
    'related_geographic_element':related_geographic_element}. For example, when I ask, 'I want to know the 
    residential area near the swamp,' you should respond with: {'primary_subject':'residential area', 
    'related_geographic_element':'swamp'}. Similarly, for 'I want to know the buildings around 100m of forests, 
    ' the response should be:  {'primary_subject':'buildings', 'related_geographic_element':'forests'}, 
    for 'buildings for commercial in munich ismaning',the response should be:  {'primary_subject':'buildings', 
    'related_geographic_element':'commercial'}
    
    if there is adj in query which describe primary_subject, like: 'soil type good for agriculture', the response 
    should include adj in related_geographic_element:{'primary_subject':'soil', 'related_geographic_element':'good 
    for agriculture'}. 
    
    
    If there is no related_geographic_element, related_geographic_element should be set as None, example: 
    for 'the largest 5 forest', related_geographic_element is None. """
    if messages==None:
        messages=[]

    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',query))
    result=chat_single(messages,'json')
    # print(result)
    json_result=json.loads(result)
    if 'primary_subject' in json_result:

        return {'primary_subject':json_result['primary_subject'],'related_geographic_element':json_result['related_geographic_element']}

    else:
        raise Exception('no relevant item found for: ' +query + ' in given list.')

def judge_type(query,messages=None):
    if query==None:
        return None
    if messages==None:
        messages=[]
    if 'building' in query.lower():
        return {'database': 'buildings'}
    ask_prompt="""
    There are two database: [soil,landuse], 
    'soil' database stores various soil types, such as swamps, wetlands, soil compositions.
    'landuse' database stores various types of urban land use like park, forest, residential area.
    
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


def judge_query_first(query,messages=None):
    if query==None:
        return None
    if messages==None:
        messages=[]

    ask_prompt="""
    if the query is one of the three questions below:
    ['What soil types are the houses near the farm on?','Which farmlands are on soil unsuitable for agriculture?','Which buildings are on soil unsuitable for buildings?']
    response in json format like:
    {
    'judge':True
    }
    else:
        {
    'judge':False
    }
    """
    if messages==None:
        messages=[]

    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',query))
    result=chat_single(messages,'json')
    # print(result)
    json_result=json.loads(result)
    if 'judge' in json_result:



        return {'judge':json_result['judge']}

    else:
        raise Exception('no relevant item found for: ' +query + ' in given list.')

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
from geo_functions import *
iii=ids_of_attribute('landuse')
print(pick_match('parks', iii))
# set_bounding_box("munich garching")
# id_buildings=ids_of_type('buildings','building')
# id_farmland=ids_of_type('landuse','forest')
# buildings_near_farmland=geo_calculate(id_farmland,id_buildings,'contains',10)
# print(id_2_attributes(soil_under_buildings['subject']))