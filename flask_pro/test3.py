from rag_model import calculate_similarity
from geo_functions import *

fclass_dict_4_similarity = {}
all_fclass_set = set()
for i in col_name_mapping_dict:
    if i != 'soil' and i != 'buildings':
        each_set = ids_of_attribute(i, 'name')
        fclass_dict_4_similarity[i] = each_set
        all_fclass_set.update(each_set)


def find_similar(query):
    def find_keys_by_values(d, elements):
        result = {}
        for key, values in d.items():
            matched_elements = [element for element in elements if element in values]
            if matched_elements:
                result[key] = matched_elements
        return result

    match_list = set(calculate_similarity(all_fclass_set, query).keys())
    if len(match_list) != 0:
        table_fclass_dicts = find_keys_by_values(fclass_dict_4_similarity, match_list)
        all_id_list = []
        for table_, fclass_list in table_fclass_dicts.items():
            print(table_, fclass_list)
    print('nothing')
while True:
    find_similar(input(":"))