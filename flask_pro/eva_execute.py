import json,re
import warnings
from create_eva_sql import create_eva
import psycopg2
from chat_py import *
import time
warnings.filterwarnings("ignore", category=FutureWarning)
# 连接参数
def extract_sql(code_str):
    code_blocks = []
    parts = code_str.split("```sql")
    for part in parts[1:]:  # 跳过第一个部分，因为它在第一个代码块之前
        code_block = part.split("```")[0]
        code_blocks.append(code_block)
    return code_blocks[0]

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
conn_params = "dbname='evaluation' user='postgres' host='localhost' password='9417941'"

conn = psycopg2.connect(conn_params)
cursor = conn.cursor()
def sql_run(query):
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        print(rows)
        if len(rows)!=0:
            return True
        else:

            return False
    except Exception as e:
        cursor.execute("ROLLBACK;")
        return e
data_lines=[]
with open('data_eva_second.jsonl','r',encoding='utf-8') as file:
    for line in file:
        # 解析每一行JSON数据并添加到列表中
        data_lines.append(json.loads(line))

prompt="""
You need to give me a sql code to answer user's questions, please do not provide anything else.
We have two tables, buildings and land.
If entity has area in the end, it means it belongs to 'land' table, otherwise, it belongs to 'buildings' table.

Search environment is postgres+postgis.
Sometimes you need to give sql which operates spatial calculations.
Please give me sql with ```sql as start, ``` as end.
We have fclass and name two columns, if there is no name mentioned, please use fclass as its column.
Please be sure to avoid 'missing FROM-clause entry for table'
Example:
query:I hope to find out parking area which name is Technical University around 100m of supermarket area which named LMU, and car_dealership area which named LMU contains parking area
sql:
     SELECT a1.*
 FROM
     land a1,
     land a2,
     land a3
 WHERE
     a1.name = 'LMU' AND
     a1.fclass = 'parking area' AND
     a2.name = 'Technical University' AND
     a2.fclass = 'supermarket area' AND
     a3.name = 'LMU' AND
     a3.fclass = 'car_dealership area' AND
     ST_DWithin(a1.geom, a2.geom,100) AND
     ST_Contains(a3.geom, a1.geom);
Example:
query:general building in Park area
sql:
    SELECT l.*
 FROM
     land l,
     buildings b
 WHERE
     b.name = '' AND
     b.fclass = 'general building' AND
     l.name = '' AND
     l.fclass = 'Park area' AND
     ST_Contains(l.geom, b.geom);
     
query:Park area contains general building
sql:
    SELECT l.*
 FROM
     land l,
     buildings b
 WHERE
     b.name = '' AND
     b.fclass = 'general building' AND
     l.name = '' AND
     l.fclass = 'Park area' AND
     ST_Contains(l.geom, b.geom);
query:general building intersects with Park area
sql:
 SELECT l.*
 FROM
     land l,
     buildings b
 WHERE
     b.name = '' AND
     b.fclass = 'general building' AND
     l.name = '' AND
     l.fclass = 'Park area' AND
     ST_Intersects(l.geom, b.geom);
     
"""
result=[]
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

    feedback = create_eva([subject_str, subject_name], [object_str, object_name], [subject_str2, subject_name2], cursor,
                          conn, geo_relations=[geo_relation, geo_relation2, relation2_object],
                          distances=[buffer_num, buffer_num2])

    return feedback
for each_data in data_lines:
    query_str=next(iter(each_data.keys()))
    messges=[]
    feedback=insert_data(each_data)

    messges.append(message_template('system',prompt))
    messges.append(message_template('user',query_str))
    start_time=time.time()
    sql,tokens=chat_single(messges)
    print('sql',extract_sql(sql))
    total_time=time.time()-start_time
    statues=str(sql_run(extract_sql(sql)))
    result.append({'query':each_data,'total_token':tokens,'time':total_time,'sql':extract_sql(sql),'statues':statues})
    print(result[-1])
    print(statues,'statues')
    print(feedback,'feedback')
    with open('second_result.jsonl','a',encoding='utf-8') as file:
            row_dict = {'query':each_data,'total_token':tokens,'time':total_time,'sql':sql,'statues':statues,'check_query':feedback}
            file.write(json.dumps(row_dict) + '\n')
