import psycopg2
import time
from draw_geo import draw_geo_map
globals_dict={}
from bounding_box import find_boundbox
def set_bounding_box(region_name):
    if region_name!=None:
        globals_dict["bounding_box_region_name"] = region_name
        globals_dict['bounding_coordinates'], globals_dict['bounding_wkb'], response_str = find_boundbox(region_name)
        return response_str
    else:
        return None


def sql_get_tabel():
    query="""
    SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
    """




# 数据库连接参数
# engine = create_engine('postgresql://postgres:9417941@localhost:5432/osm_database')
conn_params = "dbname='osm_database' user='postgres' host='localhost' password='9417941'"
set_bounding_box('munich ismaning')
# 创建连接
conn = psycopg2.connect(conn_params)
cur = conn.cursor()
minLon, minLat, maxLon, maxLat = globals_dict['bounding_coordinates']
print(globals_dict['bounding_coordinates'])
# 定义边界框

srid = 4326  # 假设使用WGS 84

# 执行查询
bounding_query = f"""
SELECT ST_AsText(geom) AS geom_wkt, *
FROM buildings
WHERE ST_Within(geom, ST_MakeEnvelope({minLon}, {minLat}, {maxLon}, {maxLat}, {srid}));
"""
attribute_query = f"""
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'buildings';
"""

query="""
SELECT * FROM buildings;

"""
start_time= time.time()
cur.execute(bounding_query)

# 获取查询结果
rows = cur.fetchall()
end_time=time.time()
print(end_time-start_time)
# 打印结果
print(len(rows))
result_dict={}
start_time= time.time()
for row in rows:
    print(row)
    result_dict[str(row[2])+"_"+str(row[4])]=row[6]
    print(row[6])
    break

end_time=time.time()
print(end_time-start_time)
draw_geo_map(result_dict,'str')
# 关闭连接
cur.close()
conn.close()
