import json
import sys

from ask_functions_agent import *
from create_eva_sql import create_eva
import psycopg2
from chat_py import *
import time,warnings
warnings.filterwarnings("ignore", category=FutureWarning)
data_lines=[]
from io import StringIO

output = StringIO()
original_stdout = sys.stdout
with open('data_eva_second.jsonl','r',encoding='utf-8') as file:
    for line in file:
        # 解析每一行JSON数据并添加到列表中
        data_lines.append(json.loads(line))

def extract_numbers_from_string(s):
    # 定义正则表达式模式，匹配一个或多个数字
    pattern = r'\d+'

    # 查找所有匹配的数字
    numbers = re.findall(pattern, s)

    # 判断字符串中是否包含数字
    if numbers:
        # 打印找到的数字
        # print("Found numbers:", numbers)
        return int(numbers[0])
    else:
        # print("No numbers found in the string.")
        return None
def extract_sql(code_str):
    code_blocks = []
    if 'python' in code_str:
        parts = code_str.split("```python")
        for part in parts[1:]:  # 跳过第一个部分，因为它在第一个代码块之前
            code_block = part.split("```")[0]
            code_blocks.append(code_block)
        return code_blocks[0]
    else:
        return code_str
def insert_data(each_data):

    true_labels=next(iter(each_data.values()))
    subject_str=next(iter(true_labels[0].keys()))
    subject_name=next(iter(true_labels[0].values()))
    object_str=next(iter(true_labels[1].keys()))
    object_name=next(iter(true_labels[1].values()))
    subject_str2=next(iter(true_labels[2].keys()))
    subject_name2=next(iter(true_labels[2].values()))

    geo_relation=true_labels[3]
    geo_relation2=true_labels[4]

    relation2_object=true_labels[5]

    buffer_num=extract_numbers_from_string(geo_relation)
    buffer_num2=extract_numbers_from_string(geo_relation2)
    if geo_relation=='close':
        buffer_num=10
    if geo_relation2=='close':
        buffer_num2=10

    feedback = create_eva([subject_str, subject_name], [object_str, object_name], [subject_str2, subject_name2], cur,
                          conn, geo_relations=[geo_relation, geo_relation2, relation2_object],
                          distances=[buffer_num, buffer_num2])

    return feedback
for each_data in data_lines:
    query_str=next(iter(each_data.keys()))
    feedback=insert_data(each_data)
    plan_str=mission_gpt(query_str)[0]
    print(extract_sql(plan_str))
    sys.stdout = output
    exec(extract_sql(plan_str))
    code_result = str(output)
    # output.truncate(0)
    sys.stdout = original_stdout
    print(code_result,'code_result')
    # break