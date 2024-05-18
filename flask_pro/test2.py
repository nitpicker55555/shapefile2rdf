import json

from chat_py import *
def misson_planner(query,messages=None):
    ask_prompt="""
I have four tools available to answer user queries:

1.id_list_of_entity(description of entity):

Input: Description of the entity, like adj or prepositional phrase like good for commercial,good for planting potatoes.
Output: A list of IDs (id_list) corresponding to the described entity.
Usage: Use this function to obtain an id_list which will be used as input in the following functions.

2.geo_filter(id_list_subject, id_list_object, 'their geo_relation'):
Input: Two id_lists (one as subject and one as object) and their corresponding geographical relationship.
Output: A dict contains 'subject','object' two keys as filtered id_lists based on the geographical relationship.
Usage: This function is used only when the user wants to query multiple entities that are geographically related. Common geographical relationships are like: 'in/on/under/in 200m of/close'

3.area_filter(id_list, num):
Input: An id_list and a number representing either the maximum or minimum count.
Output: An id_list filtered by area.
Usage: Use this function only when the user explicitly asks for the entities with the largest or smallest areas. For example, input 3 for the largest three, and -3 for the smallest three.

4.id_list_explain(id_list, explain content):
Input: An id_list and a query condition (e.g., type/name).
Output: A dictionary containing the count of each type/name occurrence.
Usage: Use this function to provide explanations based on user queries. For instance, if the user asks, "I want to know soil types," first use id_list_of_entity to get the soil_id_list, then use id_list_explain(soil_id_list, ‘type’) to get the soil type distribution. This function is used only when the user needs an explanation.
    

    """

    # print(len(ask_prompt))
    if messages == None:
        messages = []

    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', query))
    result = chat_single(messages,'')
    return result
    # print(result)
print(misson_planner('I want to know buildings name technische in forest'))