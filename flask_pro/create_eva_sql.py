import psycopg2
from shapely import wkt
# 连接参数
from smaller_polygon import half_area_polygon,double_area_polygon
import pyproj
from shapely.ops import transform
# conn_params = "dbname='evaluation' user='postgres' host='localhost' password='9417941'"
# from shapely.geometry import Polygon
#
# conn = psycopg2.connect(conn_params)
# cursor = conn.cursor()


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
def create_eva(data1,data2,data3,cursor,conn,geo_relations,distances=None):
    geo_relation=geo_relations[0]
    geo_relation2=geo_relations[1]
    geo_relation2_object=geo_relations[2]

    distance=distances[0]
    distance2=distances[1]
    print(data1,data2,geo_relation,distance)
    # name1 = "Sample Location"
    fclass1,name1 = data1

    fclass2,name2 = data2
    fclass3,name3 = data3
    relation_first_mapping={fclass1:'a1',fclass2:'a2',fclass3:'a3'}

    name1=name1.replace('which ','').replace('name ','').replace('named ','').replace('is ','')
    name2=name2.replace('which ','').replace('name ','').replace('named ','').replace('is ','')
    name3=name3.replace('which ','').replace('name ','').replace('named ','').replace('is ','')
    if 'area' in fclass1:
        table_name1='land'
    else:
        table_name1='buildings'

    if 'area' in fclass2:
        table_name2='land'
    else:
        table_name2='buildings'
    if 'area' in fclass3:
        table_name3='land'
    else:
        table_name3='buildings'
    bigger_geom = "POLYGON ((29.5 9.5, 30.5 9.5, 30.5 10.5, 29.5 10.5, 29.5 9.5))"  # WKT格式的几何数据
    smaller_geom = half_area_polygon(bigger_geom)

    wkt_geom_subject=bigger_geom
    wkt_geom_object=smaller_geom
    if distance:
        distance_meters = distance*150000*10/19  # 将距离设置为一个变量
        wkt_geom_subject=bigger_geom
        wkt_geom_object = translate_polygon_north(bigger_geom, distance_meters)
    else:
        if geo_relation:
            if geo_relation=='in':
                wkt_geom_subject,wkt_geom_object=smaller_geom,bigger_geom
            else:
                wkt_geom_subject=bigger_geom
                wkt_geom_object=smaller_geom
    wkt_geom_subject_mapping={fclass1:wkt_geom_subject,fclass2:wkt_geom_object,fclass3:'a3'}

    if distance2:
        distance_meters = distance2*150000*10/19  # 将距离设置为一个变量
        wkt_geom_subject2 = translate_polygon_north(wkt_geom_subject_mapping[geo_relation2_object], distance_meters)
    else:
        if geo_relation2:
            if geo_relation2=='in':
                wkt_geom_subject2=half_area_polygon(wkt_geom_subject_mapping[geo_relation2_object])
            else:
                wkt_geom_subject2=double_area_polygon(wkt_geom_subject_mapping[geo_relation2_object])

    # 插入到第一个表

    sql_remove_buildings = 'TRUNCATE TABLE buildings;'
    sql_remove_land = 'TRUNCATE TABLE land;'
    cursor.execute(sql_remove_land)
    cursor.execute(sql_remove_buildings)

    insert_query1 = f"""
    INSERT INTO {table_name1} (name, fclass, geom)
    VALUES (%s, %s, ST_GeomFromText(%s, 4326));
    """
    cursor.execute(insert_query1, (name1, fclass1, wkt_geom_subject))
    # 插入到第二个表
    insert_query2 = f"""
    INSERT INTO {table_name2} (name, fclass, geom)
    VALUES (%s, %s, ST_GeomFromText(%s, 4326));
    """
    cursor.execute(insert_query2, (name2, fclass2, wkt_geom_object))

    insert_query3 = f"""
    INSERT INTO {table_name3} (name, fclass, geom)
    VALUES (%s, %s, ST_GeomFromText(%s, 4326));
    """
    cursor.execute(insert_query3, (name3, fclass3, wkt_geom_subject2))



    # 提交更改
    conn.commit()
    ['intersects with', 'in', 'in 100m of', 'around 100m of', 'close', 'contains']
    relation_dict={'intersects with':'ST_Intersects(b.geom, l.geom);','in':"ST_Contains(l.geom, b.geom);","in 100m of":"ST_DWithin(b.geom, l.geom,100);","around 100m of":"ST_DWithin(b.geom, l.geom,100);","close":"ST_DWithin(b.geom, l.geom,10);","contains":"ST_Contains(b.geom, l.geom);"}
    template=f"""
     SELECT a1.*
 FROM
     {table_name1} a1,
     {table_name2} a2,
     {table_name3} a3
 WHERE
     a1.name = '{name1}' AND
     a1.fclass = '{fclass1}' AND
     a2.name = '{name2}' AND
     a2.fclass = '{fclass2}' AND
     a3.name = '{name3}' AND
     a3.fclass = '{fclass3}' AND
     {relation_dict[geo_relation].replace('b.geom','a1.geom').replace('l.geom','a2.geom').replace(';','')} AND
     {relation_dict[geo_relation2].replace('b.geom','a3.geom').replace('l.geom',f'{relation_first_mapping[geo_relation2_object]}.geom')}
    """

    print('template',template)
    cursor.execute(template)
    rows = cursor.fetchall()
    print(rows)
    if len(rows)!=0:
        return True
    else:
        return False

    # 关闭连接
    # cursor.close()
    # conn.close()
# conn_params = "dbname='evaluation' user='postgres' host='localhost' password='9417941'"
# from shapely.geometry import Polygon
#
# conn = psycopg2.connect(conn_params)
# cursor = conn.cursor()
#
# # create_eva(['general',''],['Park area',''],cursor,conn,geo_relation='contains')
# create_eva(['general',''],['Park area',''],['ass area',''],cursor,conn,geo_relations=['in 100m of','contains','general'],distances=[100,None])
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


SELECT l.*
FROM
    land l,
    buildings b
WHERE
    b.name = '' AND
    b.fclass = 'general' AND
    l.name = '' AND
    l.fclass = 'Park area' AND
    ST_Contains(b.geom,l.geom);



 SELECT
     b.fclass AS building_name,
     l.fclass AS land_name,
     ST_Distance(b.geom, l.geom) AS distance_meters
 FROM
     buildings b,
     land l
 WHERE
     b.name = '' AND
     b.fclass = 'general' AND
     l.name = '' AND
     l.fclass = 'Park area';
     
     
SELECT
    a.name AS location_a_name,
    b.name AS location_b_name,
    ST_Distance(a.geom, b.geom) AS distance_meters
FROM
    land a,
    land b
WHERE
    a.name = '' AND
    a.fclass = 'general area' AND
    b.name = '' AND
    b.fclass = 'Park area';



 SELECT l.*
 FROM
     land l,
     buildings b
 WHERE
     b.name = '' AND
     b.fclass = 'general' AND
     l.name = '' AND
     l.fclass = 'Park area' AND
     ST_DWithin(b.geom, l.geom, 100);
SELECT * FROM land;
"""