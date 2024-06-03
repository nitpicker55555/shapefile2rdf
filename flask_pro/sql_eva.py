import psycopg2

conn_params = "dbname='evaluation' user='postgres' host='localhost' password='9417941'"
conn = psycopg2.connect(conn_params)
cur = conn.cursor()
def create_spatial_data_sql(data1, data2, distance):
    # 解析输入数据
    sql_remove_buildings = 'TRUNCATE TABLE buildings;'
    sql_remove_land = 'TRUNCATE TABLE land;'


    fclass1, name1 = data1
    fclass2, name2 = data2
    if 'area' in fclass1:
        table_name1='land'
    else:
        table_name1='buildings'

    if 'area' in fclass2:
        table_name2='land'
    else:
        table_name2='buildings'
    # 定义一个基础的 Polygon WKT，一个简单的正方形
    base_wkt = "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"
    distance = 100  # 距离单位为米

    # 适合的投影坐标系的 EPSG 代码，根据地理位置选择
    projection_epsg = 4326

    # 准备 SQL 语句
    sql1 = {f"""
    INSERT INTO {table_name1} (fclass, name, geom) 
    VALUES (%s, %s, ST_GeomFromText(%s, 4326));
    """:(fclass1,name1,base_wkt)}

    sql2 = {f"""
    INSERT INTO {table_name2} (fclass, name, geom) 
    VALUES (%s, %s, ST_Transform(ST_Translate(ST_Transform(ST_GeomFromText(%s, 4326), {projection_epsg}), {distance}, 0), 4326));
    """:(fclass2,name2,base_wkt)}
    print(sql1)
    print(sql2)
    sql_list=[sql_remove_buildings,sql_remove_land,sql1,sql2]
    return sql_list

def cur_action(query_list):
    for query in query_list:
        if isinstance(query,dict):
            print(next(iter(query.keys())))

            cur.execute(next(iter(query.keys())),next(iter(query.values())))
        # rows = cur.fetchall()
        # print(rows)
# 示例数据和调用
data1 = ["park area", "TUM"]
data2 = ["buildings", ""]
distance = 500  # 1000 米

sql_statements = create_spatial_data_sql(data1, data2, distance)
# check_sql=["SELECT * FROM pg_extension WHERE extname LIKE 'postgis%';"]
cur_action(sql_statements)
