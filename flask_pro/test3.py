def judge_table(query, messages=None):
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

    if 'building' in query.lower().split():
        return {'database':'buildings'}

    if 'planting' in query.lower():
        return {'database': 'soil'}

    # if 'area' in query.lower():
    #     return {'database': 'land'}
    #
    # if 'building' in query.lower() and 'soil' not in query.lower():
    #     return {'database': 'buildings'}
    #
    # if 'land' in query.lower() and 'soil' not in query.lower():
    #     return {'database': 'land'}
    # if 'soil' in query.lower():
    #     return {'database': 'soil'}
    return None


print(judge_table('good for building'))