def merge_dicts(dict_list):
    result = {}
    for d in dict_list:
        for key, subdict in d.items():
            if key not in result:
                result[key] = subdict.copy()  # 初始化键对应的字典
            else:
                result[key].update(subdict)  # 使用 update 方法更新字典
    return result

# 示例使用
dict_list = [
    {'A': {'x': 1, 'y': 2}, 'B': {'z': 3}},
    {'A': {'x': 4, 'y': 5}, 'B': {'z': 6, 'w': 7}},
    {'A': {'x': 10,'c':1}, 'B': {'z': 1, 'w': 2}}
]
print(next(iter(dict_list[0].values())))
merged_result = merge_dicts(dict_list)
print(merged_result)
