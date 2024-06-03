import psycopg2
from shapely import wkt
# 连接参数
import pyproj
from shapely.ops import transform
conn_params = "dbname='evaluation' user='postgres' host='localhost' password='9417941'"
from shapely.geometry import Polygon

conn = psycopg2.connect(conn_params)
cursor = conn.cursor()


def translate_polygon_north(polygon_wkt, distance_meters):
    # 解析WKT为Shapely的Polygon对象
    polygon = wkt.loads(polygon_wkt)

    # 定义投影函数，以便处理地理坐标和米之间的转换
    project = pyproj.Transformer.from_proj(
        pyproj.Proj(init='epsg:4326'),  # 源坐标系 (WGS84)
        pyproj.Proj(proj='aeqd', lat_0=polygon.centroid.y, lon_0=polygon.centroid.x)  # 方位投影，以多边形的中心点为中心
    ).transform

    # 将原始Polygon投影到方位投影平面
    projected_polygon = transform(project, polygon)

    # 平移投影平面上的Polygon
    translated_projected_polygon = transform(lambda x, y: (x, y + distance_meters), projected_polygon)

    # 将平移后的Polygon投影回WGS84
    inverse_project = pyproj.Transformer.from_proj(
        pyproj.Proj(proj='aeqd', lat_0=polygon.centroid.y, lon_0=polygon.centroid.x),
        pyproj.Proj(init='epsg:4326')
    ).transform
    translated_polygon = transform(inverse_project, translated_projected_polygon)

    return translated_polygon.wkt
def create_eva(data1,data2,geo_relation=None,distance=None):

    # name1 = "Sample Location"
    fclass1,name1 = data1

    fclass2,name2 = data2
    if 'area' in fclass1:
        table_name1='land'
    else:
        table_name1='buildings'

    if 'area' in fclass2:
        table_name2='land'
    else:
        table_name2='buildings'
    wkt_geom = "POLYGON ((29.5 9.5, 30.5 9.5, 30.5 10.5, 29.5 10.5, 29.5 9.5))"  # WKT格式的几何数据
    smaller_geom = "POLYGON ((29.75 9.75, 30.25 9.75, 30.25 10.25, 29.75 10.25, 29.75 9.75))"  # WKT格式的几何数据
    if distance:
        distance_meters = distance*100000*10/9  # 将距离设置为一个变量
        new_wkt_geom = translate_polygon_north(wkt_geom, distance_meters)
    if geo_relation:
        if geo_relation=='in':
            wkt_geom,smaller_geom=smaller_geom,wkt_geom
            new_wkt_geom=smaller_geom
        else:
            new_wkt_geom=smaller_geom
    # 插入到第一个表
    insert_query1 = f"""
    INSERT INTO {table_name1} (name, fclass, geom)
    VALUES (%s, %s, ST_GeomFromText(%s, 4326));
    """
    sql_remove_buildings = 'TRUNCATE TABLE buildings;'
    sql_remove_land = 'TRUNCATE TABLE land;'
    cursor.execute(sql_remove_land)
    cursor.execute(sql_remove_buildings)
    cursor.execute(insert_query1, (name1, fclass1, wkt_geom))
    # 插入到第二个表
    insert_query2 = f"""
    INSERT INTO {table_name2} (name, fclass, geom)
    VALUES (%s, %s, ST_GeomFromText(%s, 4326));
    """


    cursor.execute(insert_query2, (name2, fclass2, new_wkt_geom))

    # 提交更改
    conn.commit()

    # 关闭连接
    cursor.close()
    conn.close()

create_eva(['Park','Sample Location'],['Park area','Sample Location'],geo_relation='in')
"""
SELECT l.*
FROM
    land l,
    buildings b
WHERE
    b.name = 'Sample Location' AND
    b.fclass = 'Park' AND
    l.name = 'Sample Location' AND
    l.fclass = 'Park area' AND
    ST_Contains(b.geom,l.geom);

 SELECT
     b.name AS building_name,
     l.name AS land_name,
     ST_Distance(b.geom, l.geom) AS distance_meters
 FROM
     buildings b,
     land l
 WHERE
     b.name = 'Sample Location' AND
     b.fclass = 'Park' AND
     l.name = 'Sample Location' AND
     l.fclass = 'Park area';
"""