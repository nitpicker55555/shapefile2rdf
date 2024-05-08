import json


def transform_to_conversation_format(input_data):
    # Extract information from the input data
    query = input_data['query']
    entities = input_data['entities']
    spatial_relations = input_data['spatial_relations']

    # Format the response as specified
    conversation = {
        "messages": [
            {
                "role": "system",
                "content": "You are an excellent linguist, Help me identify all entities from this statement also their non_spatial_modify_statement and spatial_relations. Please format your response in JSON."
            },
            {
                "role": "user",
                "content": query
            },
            {
                "role": "assistant",
                "content": json.dumps({"entities": entities, "spatial_relations": spatial_relations}, indent=4)
            }
        ]
    }

    return conversation
with open('template_gpt.jsonl','r',encoding='utf-8') as file:
    for line in file:
        current_dict = json.loads(line)
        transfered=transform_to_conversation_format(current_dict)
        with open('transfered.jsonl','a',encoding='utf-8') as ff:
            ff.write(json.dumps(transfered)+'\n')