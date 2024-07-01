from ask_functions_agent import *
# aa=name_cosin('water')
def data_intersection(query):
    match_list = name_cosin_list(query)
    table_name_dicts={}
    table_fclass_dicts={}
    all_id_list=[]
    if len(match_list) != 0:
        print('name match')
        table_name_dicts = find_keys_by_values(name_dict_4_similarity, match_list)
        print(table_name_dicts)

    match_list = fclass_cosin_list(query)
    if len(match_list) != 0:
        print('fclass match')
        table_fclass_dicts = find_keys_by_values(fclass_dict_4_similarity, match_list)
        print(table_fclass_dicts)
    if table_name_dicts!={} and table_fclass_dicts!={}:
        table_fclass_dicts.update({'buildings':'building'})
    for table_ ,fclass_list in table_fclass_dicts.items():
        if table_ in table_name_dicts:
            each_id_list = ids_of_type(table_, {'non_area_col': {'fclass': set(fclass_list), 'name': set(table_name_dicts[table_])},'area_num': None})
            all_id_list.append(each_id_list)
    return merge_dicts(all_id_list)
calculation_query('isar river')
    # for table_, fclass_list in table_fclass_dicts.items():
    #     each_id_list = ids_of_type(table_, {'non_area_col': {'fclass': set(fclass_list), 'name': set()},
    #                                         'area_num': None})


# {'buildings': ['isarCenter', 'Isarburg'], 'land': ['isarCenter', 'Isar', 'Isarauenpark', 'Isarstraße', 'Isarburg', 'Isarstausee'], 'points': ['Isar Quelle', 'Isar', 'Isarweg', 'Die Isarauen', 'Isarhotel', 'Isar Durscht', 'Isarstraße', 'Isar Renaturierung'], 'lines': ['Isarleitenweg', 'Isartrail', 'Isarwanderweg', 'Isar', 'Isarlandstraße', 'Isarweg', 'Isarbrücke', 'Isarauenweg', 'Kleine Isar', 'Isarwerkkanal', 'Isarauen', 'Isarauenstraße', 'Isarleiten', 'Isarstraße']}

# {'land': ['riverbank', 'water', 'reservoir'], 'lines': ['river', 'canal', 'stream']}