import time
import asyncio
import psycopg2,re
from draw_geo import draw_geo_map
# 数据库连接信息
host = "localhost"
dbname = "mydatabase"
user = "postgres"
password = "9417941"
port = "5432"
api_key = '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'
# from gpt_api import change_statement
def change_statement(prompt,user_content,mode='run'):
    import openai

    openai.api_key = api_key

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": user_content
            }
        ],
        temperature=0,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    # print(response["choices"][0]["message"]["content"])
    final_query=response["choices"][0]["message"]["content"]


    # if mode=="run":

        # print("final_query:")
        # print(final_query)
        # print('----------')
    return (final_query)
def extract_num(text):
    try:
        numbers = re.findall(r"\d+\.\d+|\d+", text)[0]
        return numbers
    except:
        return False
land_query="""
SELECT 
    'land_use' AS table_name_land_use, 
    l.osm_id AS land_use_osm_id, 
    l.fclass AS land_use_fclass, 
    l.geom AS land_use_geom,
    'buildings' AS table_name_buildings, 
    b.osm_id AS building_osm_id, 
    b.fclass AS building_fclass,
    b.geom AS building_geom
FROM 
    land_use l, 
    buildings b
WHERE 
    l.fclass = 'farmland' AND ST_Intersects(b.geom, l.geom);
"""
number_query="""
SELECT 
    'land_use' AS table_name_land_use, 
    l.osm_id AS land_use_osm_id, 
    l.fclass AS land_use_fclass, 
    l.geom AS land_use_geom,
    'buildings' AS table_name_buildings, 
    b.osm_id AS building_osm_id, 
    b.fclass AS building_fclass,
    b.geom AS building_geom
FROM 
    land_use l, 
    buildings b
WHERE 
    b.osm_id = '383499448' AND ST_Intersects(b.geom, l.geom);
"""

all_query="""
SELECT
    'land_use' AS table_name_land_use, 
    l.osm_id AS land_use_osm_id, 
    l.fclass AS land_use_fclass, 
    l.geom AS land_use_geom,
    'buildings' AS table_name_buildings, 
    b.osm_id AS building_osm_id, 
    b.fclass AS building_fclass,
    b.geom AS building_geom
FROM buildings b, land_use l
WHERE ST_Intersects(b.geom, l.geom);
"""

def get_multiline_input():
    print("input:")
    lines = []
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)
    return "\n".join(lines)


# 连接数据库
try:
    conn = psycopg2.connect(
        host=host,
        dbname=dbname,
        user=user,
        password=password,
        port=port
    )
    print("Connected to the database successfully")
except Exception as e:
    print("Unable to connect to the database")
    print(e)

# 写一个 SQL 搜索示例
while True:
    cur = conn.cursor()
    try:
        # 创建一个 cursor 对象


        # 定义 SQL 查询
        nquery = input("input:") # 请替换 your_table 为您的表名
        if extract_num(nquery)!=False:
            query=number_query.replace("383499448",extract_num(nquery))
            indication="Intersection problem: show specific intersected element (Building id:%s)"%extract_num(nquery)
        elif "farmland" in nquery:
            query=land_query
            indication = "Intersection problem: show specific intersected land (Farmland)"
        else:
            indication="Intersection problem: show all intersected elements"
            query=all_query
        print("-------------------")
        print("Generating query...")
        print("-------------------")
        time.sleep(4)

        print(indication)
        print("-------------------")
        print("Grammer correct!")
        print("-------------------")
        system_content="I will give you a sql query, please translate it to natural language and do not mention sql"
        translation= (change_statement(query,system_content))
        print("Do you want to search: "+translation+"?")
        print("please input yes/no \n\n(If you think this query is not what you need, please input no, then we can reproduce the query.)")
        input("input:")
        print("-------------------")
        # 执行查询
        # query = get_multiline_input()
        cur.execute(query)

        # 获取查询结果
        rows = cur.fetchall()
        map_dict={}
        for row in rows:
            print(row[0]+"_"+row[1]+"_"+row[2],row[4]+"_"+row[5]+"_"+row[6])

            map_dict.update({row[0]+"_"+row[1]+"_"+row[2]:row[3],row[4]+"_"+row[5]+"_"+row[6]:row[7]})
        print("-------------------")
        print("Total results: ",len(rows))
        print("-------------------")
        print("Generating the map...")
        print("-------------------")
        draw_geo_map(map_dict)

        print("Map finished, please check it in browser.")
        # 关闭 cursor 和连接
        # cur.close()
        # conn.close()
    except Exception as e:
        print("Error in executing query")
        print(e)
