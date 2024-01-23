import re
import json


def extract_json_objects(text):
    # 定义一个正则表达式来匹配大括号括起来的字符串
    regex = r'\{.*?\}'

    # 使用正则表达式找到所有匹配项
    matches = re.findall(regex, text)

    # 尝试将每个匹配的字符串解析为JSON对象
    json_objects = []
    for match in matches:
        try:
            json_obj = json.loads(match)
            json_objects.append(json_obj)
        except json.JSONDecodeError:
            # 如果解析失败，忽略这个匹配项
            continue

    return json_objects


# 示例用法
text = """
您想查询的是所有森林中的元素ID。为了完成这个查询，我们需要先确定“森林”属于哪个图（landuse, soil, 或 buildings）以及它的具体类型名称。然后，我们可以使用相应的函数来获取这些元素的ID。

由于我们不确定“森林”属于哪个图，我们的第一步是检查“landuse”图中是否有“森林”类型，因为从名字上来看，这个图似乎最有可能包含“森林”。如果在“landuse”图中找到了“森林”，那么我们将使用“get_id_of_type”函数来获取所有森林的元素ID。

计划将分为以下步骤：
1. 使用“get_type_of_graph”函数查询“landuse”图中的所有类型。
2. 检查结果中是否有“森林”类型。
3. 如果有“森林”类型，使用“get_id_of_type”函数查询所有森林的元素ID。

我们将从第一步开始：

```json
{
    "whole_plan": [
        "first: Query all types in the 'landuse' graph using 'get_type_of_graph'.",
        "second: Check if 'forest' is a type in the 'landuse' graph.",
        "third: If 'forest' is found, query all element IDs of 'forest' in the 'landuse' graph using 'get_id_of_type'."
    ],
    "next_step": "Query all types in the 'landuse' graph.",
    "command": {
        "command": "get_type_of_graph",
        "args": ["landuse"]
    },
    "finish_sign": False
}
```
"""
extracted_jsons = extract_json_objects(text)
print(extracted_jsons)
