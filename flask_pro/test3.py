import json

# 使用一个字典来存储全部合并后的数据
global_paring_dict = {}

# 读取文件
with open('global_paring_dict.jsonl', 'r', encoding='utf-8') as file:
    # 逐行读取并处理每一行
    for line in file:
        current_dict = json.loads(line)
        key = next(iter(current_dict))  # 获取当前字典的键
        # 如果键不存在于全局字典中，直接添加
        if key not in global_paring_dict:
            global_paring_dict[key] = current_dict[key]
        else:
            # 如果键已存在，更新该键对应的字典
            global_paring_dict[key].update(current_dict[key])

