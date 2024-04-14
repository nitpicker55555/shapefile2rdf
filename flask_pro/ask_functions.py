from chat_py import *
from geo_functions import *
import json
def ask_function(query,given_list,messages=None):
    ask_prompt="""
    You are tasked that selects one or more elements from a given list that semantically match the user's request. 
    
    Input: Receive the user's request as a string.
    List: You are provided with a list of elements to compare against.
    Semantic Matching: Implement a method to determine the semantic similarity between the user's request and each item in the list.
    Selection: Select the element(s) from the list that best match the user's request semantically.
    Output: Return the selected element(s) in JSON format.
    Example:
    
    User Input: "Find a book about space exploration."
    
    List of Items:
    
    json
    Copy code
    [
        "Astronomy Textbook",
        "Space Odyssey: A Journey to the Cosmos",
        "Exploring the Universe: An Illustrated Guide",
        "Rocket Science: The Ultimate Guide to Space Exploration"
    ]
    Output (JSON):
    
    json
    Copy code
    {
        "matches": [
            "Space Odyssey: A Journey to the Cosmos",
            "Rocket Science: The Ultimate Guide to Space Exploration"
        ]
    }
    In this example, "Space Odyssey: A Journey to the Cosmos" and "Rocket Science: The Ultimate Guide to Space Exploration" are the closest semantic matches to the user's request.
    """
    if messages==None:
        messages=[]

    messages.append(message_template('system',ask_prompt))
    messages.append(message_template('user',query+":"+str(given_list)))
    result=chat_single(messages,'json')
    # print(result)
    json_result=json.loads(result)
    if 'matches' in json_result:
        return json_result['matches']
    else:
        raise Exception('no relevant item found for: ' +query + ' in given list.')
    # messages.append(message_template('assistant',result))
id1=ids_of_type('soil','all')
# print(id1)
att=id_2_attributes(id1)
query='我想知道哪个适合农业'
a=ask_function(query,att)
id2=ids_of_type('soil',a)

