import json

from chat_py import *
def judge_table_gpt(query, messages=None):
    if isinstance(query, dict):
        query = str(query)
    if query == None:
        return None
    if messages == None:
        messages = []
    ask_prompt = """
    User will give you a sentence or a word, to search elements in dataset, which may related to type of data or name of data,
    "Type of data" means a more general category name, such as "river" or "restaurant", name of data means 
    you need to extract these infomation into a dict:
    {
    'type':...,
    'name':...,
    }
    example:
    User:isar river
    You:
    {
    'type':'river',
    'name':'isar',
    }
    notice: each part of sentence can only be classified to type or name once, if the label do not have words, set it to None.

    notice: Each key value should not include meaningless words such as "location" or "substance".
    only return json.
    """
    if messages == None:
        messages = []

    messages.append(message_template('system', ask_prompt))
    messages.append(message_template('user', str(query)))
    result = chat_single(messages, 'json')
    print(result)
    json_result = json.loads(result)
    return json_result


print(judge_table_gpt('drinking water'))