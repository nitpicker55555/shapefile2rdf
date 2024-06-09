import json
import random

from geo_functions import *
type_list=[f"{id} area" for id in list(ids_of_attribute('land'))]


def unique_elements(lst, n):
    # 使用集合去除重复元素
    unique_set = set(lst)

    # 将集合转换回列表
    unique_list = list(unique_set)

    # 如果n小于或等于唯一元素的数量，则返回前n个元素，否则返回整个列表
    return unique_list[:min(n, len(unique_list))]
# type_list.extend(['buildings']*int(len(type_list)))
for i in type_list:
    if '_' in i:
        type_list.remove(i)
expressions = [
    "I'm curious about",
    "I'd like to find out",
    "Can you tell me",
    "I wonder",
    "Could you give me information about",
    "I'm eager to discover",
    "Please inform me about",
    "I'm seeking information on",
    "I wish to ascertain",
    "I'm looking for details on",
    "I'm inquiring about",
    "I'd appreciate knowing",
    "I'm trying to figure out",
    "I hope to find out",
    "Tell me about",
    "I'm all ears for information on",
    "I'd be interested in hearing",
    "Could you detail",
    "I'm probing for details about",
    "I'm investigating"
]

name_list=['name is Peter Khal','named TUM','named LMU','name is John Smith','name is Technical University']
modify_list=['is good for study','is good for living','is good for visiting','have beautiful view','have good reputation']
geo_relation_list=['intersects with','in','in 100m of','around 100m of','close','contains']
entity_subject=''
entity_object=''
geo_relation=''
eva_list_first=[]


def pick_two_distinct(lst):
    if len(lst) < 2:
        raise ValueError("列表必须至少有两个元素")

    # 获取所有唯一值的组合
    unique_pairs = []
    seen = set()
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if lst[i] != lst[j] and (lst[i], lst[j]) not in seen and (lst[j], lst[i]) not in seen:
                unique_pairs.append((lst[i], lst[j]))
                seen.add((lst[i], lst[j]))

    if not unique_pairs:
        raise ValueError("没有找到两个不同的元素")

    # 从所有唯一的元素对中随机选择一个
    return random.choice(unique_pairs)
def basic_eva():

    for i in range(50):
        entity_list=pick_two_distinct(type_list)
        name_mo_list=random.sample(name_list,1)[0]
        fclass_mo_list=random.sample(modify_list,1)[0]
        modify_random=[name_mo_list,fclass_mo_list]
        random_index=random.randint(0, 1)
        entity_subject=entity_list[0]
        entity_object=entity_list[1]
        random_relation=random.sample(geo_relation_list,1)[0]
        random_expression=random.sample(expressions,1)[0]
        template_first= {f'{random_expression} {entity_subject} {random_relation} {entity_object}':[entity_subject,random_relation,entity_object]}
        eva_list_first.append(template_first)
    with open('data_eva_basic.jsonl', 'w') as file:
        for item in eva_list_first:
            json_line = json.dumps(item)
            file.write(json_line + '\n')
def first_eva():
    for i in range(50):
        entity_list=random.sample(type_list,2)
        name_mo_list=random.sample(name_list,2)
        fclass_mo_list=random.sample(modify_list,1)[0]
        modify_random=name_mo_list
        random_index=random.randint(0, 1)
        entity_subject=entity_list[0]+' which '+modify_random[random_index]
        entity_object=entity_list[1]+' which '+modify_random[1-random_index]
        random_relation=random.sample(geo_relation_list,1)[0]
        random_expression=random.sample(expressions,1)[0]
        template_first= {f'{random_expression} {entity_subject} {random_relation} {entity_object}':[{entity_list[0]:modify_random[random_index]},random_relation,{entity_list[1]:modify_random[1-random_index]}]}

        eva_list_first.append(template_first)
    with open('data_eva_first.jsonl', 'w') as file:
        for item in eva_list_first:
            json_line = json.dumps(item)
            file.write(json_line + '\n')
def second_eva():
    for i in range(100):
        entity_list=unique_elements(type_list,3)

        name_mo_list=random.sample(name_list,2)
        fclass_mo_list=random.sample(modify_list,1)[0]
        modify_random=name_mo_list
        random_index=random.randint(0, 1)
        entity_subject=entity_list[0]+' which '+modify_random[random_index]
        entity_object=entity_list[1]+' which '+modify_random[1-random_index]
        random_relation=random.sample(geo_relation_list,1)[0]

        name_mo_list=random.sample(name_list,2)
        fclass_mo_list=random.sample(modify_list,1)[0]
        modify_random2=name_mo_list
        ob_sub=[entity_list[0],entity_list[1]]
        random_index3=random.randint(0, 1)
        random_index2=random.randint(0, 1)
        entity_third = entity_list[2] + ' which ' + modify_random2[random_index2]
        random_relation2=random.sample(geo_relation_list,1)[0]


        random_expression=random.sample(expressions,1)[0]
        template_first= {
            f'{random_expression} {entity_subject} {random_relation} {entity_object}, and {entity_third} {random_relation2} {ob_sub[random_index3]}':
                [{entity_list[0]:modify_random[random_index]},{entity_list[1]:modify_random[1-random_index]},{entity_list[2]:modify_random2[random_index2]},random_relation,random_relation2,ob_sub[random_index3]]}
        eva_list_first.append(template_first)
    with open('data_eva_second.jsonl', 'w') as file:
        for item in eva_list_first:
            json_line = json.dumps(item)
            file.write(json_line + '\n')
def third_eva():
    for i in range(100):
        entity_list=random.sample(type_list,4)
        name_mo_list=random.sample(name_list,2)
        modify_random=name_mo_list
        random_index=random.randint(0, 1)
        entity_subject=entity_list[0]+' which '+modify_random[random_index]
        entity_object=entity_list[1]+' which '+modify_random[1-random_index]
        random_relation=random.sample(geo_relation_list,1)[0]

        name_mo_list=random.sample(name_list,2)
        modify_random2=name_mo_list
        ob_sub2=[entity_list[0],entity_list[1]]
        random_index_ob_2=random.sample(ob_sub2,1)[0]
        random_index2=random.randint(0, 1)
        entity_third = entity_list[2] + ' which ' + modify_random2[random_index2]
        random_relation2=random.sample(geo_relation_list,1)[0]

        name_mo_list=random.sample(name_list,2)
        modify_random3=name_mo_list
        ob_sub3=[entity_list[0],entity_list[1],entity_list[2]]
        random_index_ob_3=entity_list[2]
        random_index3=random.randint(0, 1)
        entity_forth = entity_list[3] + ' which ' + modify_random3[random_index3]
        random_relation3=random.sample(geo_relation_list,1)[0]


        random_expression=random.sample(expressions,1)[0]
        template_first= {
            f'{random_expression} {entity_subject} {random_relation} {entity_object}, and {entity_third} {random_relation2} {random_index_ob_2}, and {entity_forth} {random_relation3} {random_index_ob_3}':
                [{entity_list[0]: modify_random[random_index]}, {entity_list[1]: modify_random[1 - random_index]},
                 {entity_list[2]: modify_random2[random_index2]},{entity_list[3]: modify_random3[random_index3]}, random_relation, random_relation2,random_relation,random_index_ob_2,
                 random_index_ob_3]}
        eva_list_first.append(template_first)
    with open('data_eva_third.jsonl', 'w') as file:
        for item in eva_list_first:
            json_line = json.dumps(item)
            file.write(json_line + '\n')
third_eva()
# print(random.sample(type_list,2))