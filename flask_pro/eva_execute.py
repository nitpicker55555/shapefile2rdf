import json,re

from create_eva_sql import create_eva
import psycopg2
from chat_py import chat_single
import time
# 连接参数
def extract_numbers_from_string(s):
    # 定义正则表达式模式，匹配一个或多个数字
    pattern = r'\d+'

    # 查找所有匹配的数字
    numbers = re.findall(pattern, s)

    # 判断字符串中是否包含数字
    if numbers:
        # 打印找到的数字
        # print("Found numbers:", numbers)
        return numbers
    else:
        # print("No numbers found in the string.")
        return None
conn_params = "dbname='evaluation' user='postgres' host='localhost' password='9417941'"

conn = psycopg2.connect(conn_params)
cursor = conn.cursor()
def sql_run(query):
    cursor.execute(query)
    rows = cursor.fetchall()
data_lines=[]
with open('data_eva_basic.jsonl','r',encoding='utf-8') as file:
    for line in file:
        # 解析每一行JSON数据并添加到列表中
        data_lines.append(json.loads(line))
for each_data in data_lines:
    query_str=next(iter(each_data.keys()))
    true_labels=next(iter(each_data.values()))
    subject_str=true_labels[0]
    geo_relation=true_labels[1]
    object_str=true_labels[2]
    buffer_num=extract_numbers_from_string(geo_relation)
    if buffer_num:
        create_eva([subject_str,''],[object_str,''],buffer_num)
