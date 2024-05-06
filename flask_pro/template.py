import json

from chat_py import *

single_geo_buffer = """
{
  "query": "I want to know commercial kinds of buildings in around 100m of landuse which is forest",
  "entities": [
    {
      "text": "buildings",
      "non_spatial_modify_statement": "commercial kinds"
    },
    {
      "text": "landuse",
      "non_spatial_modify_statement": "forest"
    },
  ],
  "spatial_relations": [
    {"type": "in around 100m of", "head": 0, "tail": 1},
  ]
}
"""
double_template={
  "query": "show parking slots of landuse in around 200 m of the largest river in the commercial park area?",
  "entities": [
    {
      "text": "landuse",
      "non_spatial_modify_statement": "parking slots"
    },
    {
      "text": "river",
      "non_spatial_modify_statement": "largest"
    },
    {
      "text": "park area",
      "non_spatial_modify_statement": "commercial"
    }
  ],
  "spatial_relations": [
    {"type": "in around 200 m of", "head": 0, "tail": 1},
    {"type": "in", "head": 1, "tail": 2}
  ]
}
single_geo_in = """
{
  "query": "I want to know commercial buildings in landuse which is forest",
  "entities": [
    {
      "text": "buildings",
      "non_spatial_modify_statement": "commercial"
    },
    {
      "text": "landuse",
      "non_spatial_modify_statement": "forest"
    },
  ],
  "spatial_relations": [
    {"type": "in", "head": 0, "tail": 1},
  ]
}
"""

modify_prompt = [{
    "type": "Adjective Modifying a Noun",
    "structure": "Adjective + Noun",
    "example": "commercial buildings",
    "explanation": "The adjective 'commercial' directly modifies the noun 'buildings', describing its purpose or type."
},
    {
        "type": "Noun as Modifier",
        "structure": "Modifier Noun + Main Noun",
        "example": "strawberry soil",
        "explanation": "The noun 'strawberry' acts as a modifier to the noun 'soil', indicating the type or purpose of the soil."
    },
    {
        "type": "Prepositional Phrase Modifying a Noun",
        "structure": "Noun + Prepositional Phrase",
        "example": "soil for planting strawberry",
        "explanation": "The prepositional phrase 'for planting strawberry' modifies the noun 'soil', providing additional information about its intended use."
    },
    {
        "type": "Adjectival Clause Modifying a Noun",
        "structure": "Noun + Relative Clause",
        "example": "buildings that are used for commercial purposes",
        "explanation": "The relative clause 'that are used for commercial purposes' provides detailed information about the noun 'buildings'."
    }, {
        "set non_spatial_modify_statement as None"
    }
]
import random


def generate_feature_pair():
    features = [
        'A containment or location-based relationship, like "in" or "within," which positions one entity within another.',
        '"Under" is a spatial relationship indicating that one entity is directly beneath another, exemplified by phrases such as "soil under buildings," where the soil is positioned directly below the structure of the buildings.',
        '"Intersects" refers to a relationship where two entities cross or meet each other in space, as in a road that intersects a railway, meaning the road and railway cross at some point.',
        'A buffer relationship indicating proximity, such as "within 100 meters of" or "around 200 meters of," or close / near. Which specifies a zone of interest around one of the entities.']
    probabilities = [0.2, 0.2, 0.2, 0.4]  # 初始概率分布

    # 首先选择第一个特征
    first_feature = random.choices(features, probabilities, k=1)[0]

    # 移除已选择的特征并更新概率分布
    index = features.index(first_feature)
    del features[index]
    del_prob = probabilities.pop(index)

    # 更新剩余特征的概率分布
    probabilities = [p / (1 - del_prob) for p in probabilities]

    # 选择第二个特征
    second_feature = random.choices(features, probabilities, k=1)[0]

    return [first_feature, second_feature]


def num_of_geo():
    features = ['single', 'double']
    probabilities = [0.5, 0.5]  # 概率分布，a,b,c各占1/5, d占2/5

    # 使用random.choices从features中按照概率probabilities选择两个特征
    return random.choices(features, probabilities, k=1)[0]


def modify_of_entity(elements):
    """从给定列表中随机返回一个元素"""
    random_elements = random.sample(elements, 2)
    return str(random_elements)

num_entities=2

for i in range(50):
    print(i)
    ask_prompt = f"""Create a structured query involving {str(num_entities)} entities relevant to geographic analysis. These entities must be related to landuse or buildings or soil. Each entity needs 
to have these modifying phrases in turn:{modify_of_entity(modify_prompt)}. The query should involve the spatial relationship: 
{generate_feature_pair()[0]}
please response in json format like:
{str(single_geo_buffer)}
"""
    messages = []
    messages.append(message_template('system', "You are a data generator, I will give you introductions and example for generating data, please only follow the introdcutions but do not copy the entities and relation in example, and do not learn the query in example. You need to write query which has different entities from example."))
    messages.append(message_template('user', ask_prompt))
    print(ask_prompt)
    result = chat_single(messages, 'json','gpt-4-turbo')
    # print(result)
    json_result = json.loads(result)
    print(result)
    with open('template_gpt.jsonl','a',encoding='utf-8') as file:
        file.write(json.dumps(json_result)+'\n')

