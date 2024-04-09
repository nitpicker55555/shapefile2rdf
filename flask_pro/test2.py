import time

import psycopg2

conn_params = "dbname='osm_database' user='postgres' host='localhost' password='9417941'"
conn = psycopg2.connect(conn_params)
cur = conn.cursor()
a=time.time()
# cur = conn.cursor()

# 执行SQL查询
cur.execute("SELECT * FROM soilnoraml WHERE uebk25_k = '66b';")

# 获取并打印列名称（标签）
column_names = [desc[0] for desc in cur.description]
print("Column names:", column_names)

# 遍历查询结果
for row in cur.fetchall():
    for col_name, value in zip(column_names, row):
        print(f"{col_name}: {value}")

# 关闭游标和连接
cur.close()
conn.close()