import time

from flask import session,current_app
from pyproj import CRS, Transformer
from shapely.geometry import Polygon,MultiPolygon
import psycopg2
import numpy as np
import geopandas as gpd
# from draw_geo import draw_geo_map
from tqdm import tqdm
from shapely import wkb
from shapely import wkt
from itertools import islice
import copy
import pandas as pd
from flask import session
global_id_attribute={}
global_id_geo={}

def modify_globals_dict(new_value):
    session['globals_dict'] = new_value

    # if 'global_id_attribute' not in session:
    #     session['global_id_attribute'] = {}
    # if 'global_id_geo' not in session:
    #     session['global_id_geo'] = {}
def use_globals_dict():
    with current_app.app_context():
        return session.get('globals_dict', 'No global variable found in session.')

def map_keys_to_values(similar_col_name_dict):
    result = {}
    for key, value in similar_col_name_dict.items():
        result[key] = value
        result[value] = value
    return result
# sparql = SPARQLWrapper("http://127.0.0.1:7200/repositories/osm_search")

conn_params = "dbname='osm_database' user='postgres' host='localhost' password='9417941'"
conn = psycopg2.connect(conn_params)
cur = conn.cursor()
"""
    osm_id='osm_id'
    fclass='fclass'
    select_query=f"SELECT '{graph_name}' AS source_table, {fclass},name,{osm_id},geom"
    if graph_name=='soil':
        graph_name='soilcomplete'
        fclass='leg_text'
        osm_id='objectid'
        select_query=f'SELECT {fclass},{osm_id},geom'

"""
similar_ori_table_name_dict={'lands': "land", 'building': 'buildings', 'point': 'points', 'streets': 'lines','soil':'soil'}
similar_table_name_dict=map_keys_to_values(similar_ori_table_name_dict)
col_name_mapping_dict={
"soil":{
    "osm_id":"objectid",
    "fclass":"leg_text",
    "name":"leg_text",
    "select_query":"SELECT leg_text,objectid,geom",
    "graph_name":"soilcomplete"

}
    # "soilcomplete":{
    # "osm_id":"objectid",
    # "fclass":"leg_text",
    # "select_query":"SELECT leg_text,objectid,geom",
    # "graph_name":"soilcomplete"

   ,
"buildings":{
    "osm_id": "osm_id",
    "fclass": "fclass",
    "name": "name",
    "select_query": "SELECT buildings AS source_table, fclass,name,osm_id,geom",
    "graph_name":"buildings"
},
"land":{
    "osm_id": "osm_id",
    "fclass": "fclass",
    "name":"name",
    "select_query": "SELECT landuse AS source_table, fclass,name,osm_id,geom",
    "graph_name":"landuse"
},
"points":{
    "osm_id": "osm_id",
    "fclass": "fclass",
    "name":"name",
    "select_query": "SELECT points AS source_table, fclass,name,osm_id,geom",
    "graph_name":"points"
},
"lines":{
    "osm_id": "osm_id",
    "fclass": "fclass",
    "name":"name",
    "select_query": "SELECT lines AS source_table, fclass,name,osm_id,geom",
    "graph_name":"lines"
}

}
revers_mapping_dict={}


def format_sql_query(names):
    formatted_names = []
    # print(names)
    for name in names:
        if not isinstance(name,int):
        # Replace single quote with two single quotes for SQL escape
            formatted_name = name.replace("'", "''")
            # Wrap the name with single quotes
        else:
            formatted_name=name
        formatted_name = f"'{formatted_name}'"
        formatted_names.append(formatted_name)

    # Join all formatted names with a comma
    formatted_names_str = ", ".join(formatted_names)
    return f"({formatted_names_str})"
def auto_add_WHERE_AND(sql_query,mode='query'):

        # 将 SQL 查询分割成多行
        lines_ori = sql_query.splitlines()
        lines = [item for item in lines_ori if item.strip()]
        # 标记是否已经添加了 WHERE 子句
        where_added = False
        # 标记是否已经处理过 FROM 关键字的行
        from_processed = False
        # 准备存储处理后的 SQL 查询
        modified_query = []

        for line in lines:
            # 删除行首和行尾的空白字符
            stripped_line = line.strip()
            # 如果行是注释或空行，直接添加到结果中
            if stripped_line.startswith('--') or not stripped_line:
                modified_query.append(line)
                continue

            # 检查是否是 FROM 行或之后的行
            if 'FROM' in stripped_line.upper():
                modified_query.append(line)
                from_processed = True
            elif from_processed:
                # 检查行是否已经以 WHERE 或 AND 开始
                if not (stripped_line.upper().startswith('WHERE') or stripped_line.upper().startswith('AND')):
                    # 如果还未添加 WHERE，则首个条件添加 WHERE，之后添加 AND
                    if not where_added:
                        line = line.replace(stripped_line, 'WHERE ' + stripped_line)
                        where_added = True
                    else:
                        line = line.replace(stripped_line, 'AND ' + stripped_line)
                modified_query.append(line)
            else:
                modified_query.append(line)
        if not modified_query[-1].strip().endswith(';'):
            if mode!='attribute':
                modified_query[-1] += '\nLIMIT 20000;'
            else:
                modified_query[-1]+=';'
        # 将处理后的行合并回一个单一的字符串
        return '\n'.join(modified_query)
def get_table_names():
    """ 获取指定数据库中所有表名 """
    # conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    # cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    table_names = cur.fetchall()
    # cur.close()
    # conn.close()
    return [name[0] for name in table_names]
def get_column_names(table_name):
    """ 获取指定表中的所有列名 """
    # conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    # cur = conn.cursor()
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{col_name_mapping_dict[table_name]['graph_name']}' AND table_schema='public';")
    column_names = cur.fetchall()
    # cur.close()
    # conn.close()
    return [name[0] for name in column_names]

# 使用示例
# columns = get_column_names('mydatabase', 'myusername', 'mypassword', 'mytable')
# print(columns)

def cur_action(query,mode='query'):
    try:
        start_time = time.time()
        query=auto_add_WHERE_AND(query,mode)

        # print(query)

        cur.execute(query)
        rows =cur.fetchall()
        end_time = time.time()

        # 计算耗时
        elapsed_time = end_time - start_time
        # print(f"代码执行耗时: {elapsed_time} 秒",len(rows))
        return rows
    except psycopg2.Error as e:
        cur.execute("ROLLBACK;")
        print(query)
        raise Exception(f"SQL error: {e}")





def ids_of_attribute(graph_name,specific_col=None, bounding_box_coordinats=None):



    attributes_set = set()

    fclass= col_name_mapping_dict[graph_name]['fclass']

    if specific_col!=None:
        fclass=col_name_mapping_dict[graph_name][specific_col]
    graph_name_modify = col_name_mapping_dict[graph_name]['graph_name']
    bounding_query = f"""
    SELECT DISTINCT {fclass}
    FROM {graph_name_modify}

    """
    #     {bounding_judge_query}
    # print(bounding_query)


    rows = cur_action(bounding_query,'attribute')


    for row in rows:
        attributes_set.add(row[0])
    return attributes_set

def judge_area(type):
    if 'large' in str(type) or 'small' in str(type) or 'big' in str(type):
        return True
    else:
        return False

def ids_of_type(graph_name, type_dict, bounding_box=None):
    print(type_dict)

    """
    session['globals_dict']["bounding_box_region_name"]=region_name
    session['globals_dict']['bounding_coordinates'],session['globals_dict']['bounding_wkb']=find_boundbox(region_name)
set_bounding_box("munich")
a={'non_area_col':{'fclass':'all'},'area_num':0}
ids_of_type('landuse',a)
    type_dict={'non_area_col':{'fclass':fclass_list...,'name':name_list...},'area_num':area_num}
    """
    area_num=None

    select_query=col_name_mapping_dict[graph_name]['select_query']
    graph_name_modify=col_name_mapping_dict[graph_name]['graph_name']
    fclass=col_name_mapping_dict[graph_name]['fclass']
    osm_id=col_name_mapping_dict[graph_name]['osm_id']

    bounding_judge_query = ""
    bounding_box_value=bounding_box

    if bounding_box_value!=None:
        bounding_box_coordinats = bounding_box_value['bounding_coordinates']
        min_lat, max_lat, min_lon, max_lon = bounding_box_coordinats
        bounding_judge_query=f"ST_Intersects(geom, ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat}, {4326}))"

    fclass_row = ''

    for col_name,single_type_list in type_dict['non_area_col'].items():
        # print(col_name,single_type_list)
        # print(col_name,single_type_list)
        if single_type_list=={'all'}:
            fclass_row += ''
        elif len(single_type_list)>1:
            fclass_row+=f"\n{col_name_mapping_dict[graph_name][col_name]} in {format_sql_query(list(single_type_list))}"
        elif len(single_type_list)==1:
            fclass_row += f"\n{col_name_mapping_dict[graph_name][col_name]} = '{list(single_type_list)[0]}'"




    bounding_query = f"""
    {select_query}
    FROM {graph_name_modify}
    {bounding_judge_query}
    {fclass_row}
    """
    # queries.append(bounding_query)

    # print(bounding_query)
    # final_query = "UNION ALL".join(queries)
    # print(bounding_query)
    rows = cur_action(bounding_query)

    result_dict = {}
    # print(graph_names)
    for row in rows:


        # result_dict[row[2] + "_" + row[3]+"_"+row[4]] = mapping(wkb.loads(bytes.fromhex(row[6])))
        if graph_name=='soil':
            # soil 没有name

            result_dict['soil' + "_" + str(row[0]) + "_" + str(row[1])] = (wkb.loads(bytes.fromhex(row[-1]))) #result_dict _分割的前两位是展示在地图上的
            global_id_attribute['soil' + "_" + str(row[0]) + "_" + str(row[1])]=  str(row[0])

        else:
            #     select_query=f'SELECT {fclass},name,{osm_id},geom'
            result_dict[graph_name+ "_" + str(row[1])+"_"+str(row[2])+"_"+str(row[3])] = (wkb.loads(bytes.fromhex(row[-1])))
            global_id_attribute[graph_name+ "_" + str(row[1])+"_"+str(row[2])+"_"+str(row[3])] =  str(row[1]+str(row[2]))


        global_id_geo.update(result_dict)

    feed_back=result_dict
    # print(len(feed_back))
    if type_dict['area_num']!=None:
        feed_back=area_filter(feed_back, type_dict['area_num'])['id_list'] #计算面积约束
        print(len(feed_back),'area_num',type_dict['area_num'])

    if "bounding_box_region_name" in bounding_box_value:
        geo_dict = {bounding_box_value["bounding_box_region_name"]:  (wkb.loads(bytes.fromhex((bounding_box_value['bounding_wkb']))))}
    else:
        geo_dict = {}

    geo_dict.update(feed_back)
    if len(feed_back)==0:
        print(f"Table {graph_name} have elements {type_dict}, but not in the current region.")
    #     raise Exception(f'Nothing found for {type_dict} in {graph_name}! Please change an area and search again.')

    return {'id_list':feed_back,'geo_map':geo_dict}


def area_filter(data_list1_original, top_num=None):
    print(top_num)
    top_num=int(top_num)

    data_list1 = copy.deepcopy(data_list1_original)
    if isinstance(data_list1, dict) and 'id_list' in data_list1: #ids_of_type return的id_list是可以直接计算的字典
        data_list1 = data_list1['id_list']

    list_2_geo1 = {i:[(global_id_geo[i]).area,global_id_geo[i]] for i in data_list1}
    data_list1=list_2_geo1
    sorted_dict=dict(sorted(data_list1.items(), key=lambda item: item[1][0], reverse=True))
    if top_num!=None and top_num!=0:
        if top_num>0:
            top_dict=dict(islice(sorted_dict.items(), top_num))
        else:
            items_list = list(sorted_dict.items())

            # 获取最后三个键值对
            last_three_items = items_list[top_num:]

            # 转换这三个键值对回字典
            top_dict = dict(last_three_items)
    else:
        top_dict=sorted_dict
    area_list = {key: value[0] for key, value in top_dict.items()}
    geo_dict = {key: value[1] for key, value in top_dict.items()}

    return {'area_list':area_list,'geo_map':geo_dict,'id_list':geo_dict}

def geo_calculate(data_list1_original, data_list2_original, mode, buffer_number=0,versa_sign=False,bounding_box=None):
    if mode=='area_filter':
        return area_filter(data_list1_original, buffer_number)
    reverse_sign=False

    #data_list1.keys() <class 'shapely.geometry.polygon.Polygon'>
    """
    buildings in forest

    :param data_list1_original:  smaller element as subject buildings 主语
    :param data_list2_original:  bigger element as object forest 宾语
    :param mode:
    :param buffer_number:
    :return:
    """
    bounding_box_value=session['globals_dict']
    data_list1=copy.deepcopy(data_list1_original)
    data_list2=copy.deepcopy(data_list2_original)
    if mode=='contains':
        reverse_sign=True
        mode='in'
        data_list1 = copy.deepcopy(data_list2_original)
        data_list2 = copy.deepcopy(data_list1_original)
    if isinstance(data_list1, str):
        data_list1 = bounding_box_value[data_list1]
        data_list2 = bounding_box_value[data_list2]

    elif isinstance(data_list1,list): #list是geo_calculate return的subject或Object的键值
        list_2_geo1 = {i:global_id_geo[i] for i in data_list1}
        data_list1=list_2_geo1
    if isinstance(data_list1, dict) and 'id_list' in data_list1: #ids_of_type return的id_list是可以直接计算的字典
        data_list1 = data_list1['id_list']

    if isinstance(data_list2,dict) and 'id_list' in data_list2:
        data_list2=data_list2['id_list']
    if  isinstance(data_list2,list):
        list_2_geo2 = {i:global_id_geo[i] for i in data_list2}
        data_list2=list_2_geo2

    # print("len datalist1", len(data_list1))
    # print("len datalist2", len(data_list2))
    # gseries1 = gpd.GeoSeries([shape(geojson) for geojson in data_list1.values()])
    # gseries2= gpd.GeoSeries([shape(geojson) for geojson in data_list2.values()])

    # data_list1=data_list1[:300]
    # for i in data_list1:
    #     print(type(data_list1[i]))
    #     break
    # for i in data_list2:
    #     print(data_list2[i])
    #     break
    gseries1 = gpd.GeoSeries(list(data_list1.values()))
    gseries1.index = list(data_list1.keys())
    # print(gseries1.index)
    gseries2 = gpd.GeoSeries(list(data_list2.values()))
    gseries2.index = list(data_list2.keys())


    gseries1 = gseries1.set_crs("EPSG:4326", allow_override=True)
    gseries1 = gseries1.to_crs("EPSG:32632")
    gseries2 = gseries2.set_crs("EPSG:4326", allow_override=True)
    gseries2 = gseries2.to_crs("EPSG:32632")
    # gseries2 = gpd.GeoSeries([(item['wkt']) for item in data_list2])
    # gseries2.index = [item['osmId'] for item in data_list2]

    # 创建空间索引
    sindex2 = gseries2.sindex
    sindex1 = gseries1.sindex
    osmId1_dict = {}
    parent_set=set()
    child_set=set()
    if mode == "in":
        # 检查包含关系

        for osmId1, geom1 in gseries1.items():
            possible_matches_index = list(sindex2.intersection(geom1.bounds))
            possible_matches = gseries2.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.contains(geom1)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                # all_id_list.append(osmId1)
                osmId1_dict[osmId1]=geom1
                # all_id_list.extend(matching_osmIds)
                parent_set.update(set(matching_osmIds))
                child_set.add(osmId1)
                # result_list.append(f"set1 id {osmId1} in set2 id {matching_osmIds}")
                # print(f"set1 id {osmId1} in set2 id {matching_osmIds}")
        # print(len(osmId1_dict))

    elif mode == "buffer":
        for osmId2, geom2 in tqdm(gseries2.items(), desc="buffer"):
            # osmId1 is smaller element : subject
            # matching_osmIds is bigger element : object
            # 创建缓冲区（100米）
            buffer = geom2.buffer(buffer_number)

            possible_matches_index = list(sindex1.intersection(buffer.bounds))
            possible_matches = gseries1.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.intersects(buffer)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                # all_id_list.append(osmId2)
                osmId1_dict[osmId2]=geom2
                # all_id_list.extend(matching_osmIds)
                child_set.update(set(matching_osmIds))
                parent_set.add(osmId2)
                # result_list.append(f"set1 id {osmId1} in buffer of set2 id {matching_osmIds} ")
                # print(f"set1 id {osmId1} in buffer of set2 id {matching_osmIds} ")

    elif mode == "intersects":
        # 检查交叉关系
        for osmId1, geom1 in gseries1.items():
            possible_matches_index = list(sindex2.intersection(geom1.bounds))
            possible_matches = gseries2.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.intersects(geom1)]

            if not precise_matches.empty:
                matching_osmIds = precise_matches.index.tolist()
                # result_list.append(f"set1 id {osmId1} intersects with set2 id {matching_osmIds}")
                # all_id_list.append(osmId1)
                osmId1_dict[osmId1]=geom1
                # all_id_list.extend(matching_osmIds)
                parent_set.update(set(matching_osmIds))
                child_set.add(osmId1)
                # print(f"set1 id {osmId1} intersects with set2 id {matching_osmIds}")

    elif mode == "shortest_distance":
        min_distance = float('inf')
        closest_pair = (None, None)

        # 计算两个列表中每对元素间的距离，并找出最小值
        for item1 in data_list1:
            geom1 = (data_list1[item1])
            for item2 in data_list2:
                geom2 = (data_list1[item2])
                distance = geom1.distance(geom2)
                if distance < min_distance:
                    min_distance = distance
                    closest_pair = (item1, item2)
        # print("distance between set1 id " + str(closest_pair[0]) + " set2 id " + str(
        #     closest_pair[1]) + " is closest: " + str(min_distance) + " m")

        # result_list.append("distance between set1 id " + str(closest_pair[0]) + " set2 id " + str(
        #     closest_pair[1]) + " is closest: " + str(min_distance) + " m")
    elif mode == "single_distance":
        distance = list(data_list1[0].values())[0].distance(list(data_list2[0].values())[0])
        # print(distance)
    """
        session['globals_dict']["bounding_box_region_name"]=region_name
    session['globals_dict']['bounding_coordinates'],session['globals_dict']['bounding_wkb']=find_boundbox(region_name)

    """

    if "bounding_box_region_name" in bounding_box_value:
        # geo_dict = {bounding_box_value["bounding_box_region_name"]: wkb.loads(bytes.fromhex(bounding_box_value['bounding_wkb']))}
        geo_dict = {bounding_box_value["bounding_box_region_name"]: (wkb.loads(bytes.fromhex((bounding_box_value['bounding_wkb']))))}
    else:
        geo_dict = {}
    # data_list1.update(data_list2)
    parent_geo_dict=transfer_id_list_2_geo_dict(list(parent_set), data_list2)
    if versa_sign:

        child_geo_dict=transfer_id_list_2_geo_dict(list(set(data_list1)-child_set), data_list1)
    else:
        child_geo_dict=transfer_id_list_2_geo_dict(list(child_set), data_list1)

    geo_dict.update(parent_geo_dict)
    geo_dict.update(child_geo_dict)

    # print(len(geo_dict))

    # html=draw_geo_map(geo_dict, "geo")
    # with open('my_list.pkl', 'wb') as file:
    #     pickle.dump(osmId1_list, file)
    if reverse_sign==True:
        parent_geo_dict,child_geo_dict=child_geo_dict,parent_geo_dict

    return {'object':{'id_list':parent_geo_dict},'subject':{'id_list':child_geo_dict},'geo_map':geo_dict}
    # return {'subject_id_list':parent_set,'object_id_list':child_set,'geo_map':geo_dict}
    # return child_set,parent_set,geo_dict
    # return geo_dict

    # return {'subject_id_list':parent_set,'object_id_list':child_set,'geo_map':geo_dict}
    # return child_set,parent_set,geo_dict
    # return geo_dict


def calculate_areas(input_dict):
    """
    输入一个键值为WKT字符串的字典，返回一个键值为对应几何图形面积的字典。

    参数：
        input_dict (dict): 键值为WKT字符串的字典。

    返回：
        dict: 键值为对应几何图形面积的字典。
    """
    if isinstance(input_dict,dict):
        if 'id_list' in input_dict:
            input_dict=input_dict['id_list']
    crs_wgs84 = CRS("EPSG:4326")
    # 定义UTM投影坐标系，这里使用UTM 33区
    crs_utm = CRS("EPSG:32633")

    # 创建坐标转换器
    transformer = Transformer.from_crs(crs_wgs84, crs_utm, always_xy=True)
    total_area = 0
    output_dict = {}
    for key, value in input_dict.items():

        if isinstance(value, Polygon):
            coords = np.array(value.exterior.coords)
            utm_coords = np.array(transformer.transform(coords[:, 0], coords[:, 1])).T
            utm_polygon = Polygon(utm_coords)
            total_area= utm_polygon.area
        elif isinstance(value, MultiPolygon):

            for poly in value.geoms:
                coords = np.array(poly.exterior.coords)
                utm_coords = np.array(transformer.transform(coords[:, 0], coords[:, 1])).T
                utm_polygon = Polygon(utm_coords)
                total_area += utm_polygon.area
        # 将结果存入输出字典
        output_dict[key] = round(total_area,2)
    return output_dict

def equal_interval_stats(data_dict, num_intervals=5):
    # 将字典值转换为DataFrame

        data = pd.DataFrame(list(data_dict.items()), columns=['Key', 'Value'])

        # 获取数据的最小值和最大值
        min_value = data['Value'].min()
        max_value = data['Value'].max()



        # 创建等间距区间
        intervals = np.linspace(min_value, max_value, num_intervals + 1)
        interval_labels = [f"{intervals[i]:.2f} - {intervals[i + 1]:.2f}" for i in range(len(intervals) - 1)]

        # 创建一个新的字典存储结果
        result = {label: 0 for label in interval_labels}

        # 计算每个区间内的数量
        for i in range(len(intervals) - 1):
            lower_bound = intervals[i]
            upper_bound = intervals[i + 1]
            count = data[(data['Value'] > lower_bound) & (data['Value'] <= upper_bound)].shape[0]
            result[interval_labels[i]] = count

        return result

def id_list_explain(id_list,col='fclass'):
    if isinstance(id_list,dict):
        if 'subject' in id_list:
            id_list=id_list['subject']

        if 'id_list' in id_list:
            id_list=id_list['id_list']
    if 'attribute' in col:
        table_name=str(next(iter(id_list))).split('_')[0]
        return get_column_names(table_name)
    fclass_list=['fclass','type','class','name']
    result = {}
    if col  in fclass_list:
        if col=='name':
            extract_index=2
        else:
            extract_index=1

        # 遍历输入列表中的每个元素
        for item in id_list:
            # 使用split方法按'_'分割字符串，并提取所需的部分
            parts = item.split('_')
            if len(parts) > 2:
                key = parts[extract_index]
                # 更新字典中的计数
                if key in result:
                    result[key] += 1
                else:
                    result[key] = 1
    if col=='area':
        result=calculate_areas(id_list)


    print(dict(sorted(result.items(), key=lambda item: item[1], reverse=True)))
    return dict(sorted(result.items(), key=lambda item: item[1], reverse=True))


def transfer_id_list_2_geo_dict(id_list, raw_dict=None):
    result_dict = {}
    for i in tqdm(id_list, desc="generating map..."):
        result_dict[i] = raw_dict[i]
    return result_dict
def ttl_read(path):
    from rdflib import Graph
    result_dict= {}
    predicate_dict={}
    g = Graph()

    # 解析TTL文件
    g.parse(path, format="ttl")

    # 遍历图形中的所有三元组并打印它们
    u=0
    for subj, pred, obj in g:
        if str(pred) not in predicate_dict:
            predicate_dict[str(pred)]=set()
        predicate_dict[str(pred)].add(obj)
        if str(subj) not in result_dict:
            result_dict[str(subj)]={}
        result_dict[str(subj)][str(pred)]=str(obj)


    return result_dict,predicate_dict
def search_attribute(dict_,key,value):
    if isinstance(value,list):
        pass
    else:
        value=[value]
    result_dict= {}
    geo_asWKT_key=''

    for subject in dict_:
        if geo_asWKT_key=='':
            for keys in dict_[subject]:
                if "asWKT" in str(keys):
                    geo_asWKT_key=keys
                    break
        else:
            break
    # print(geo_asWKT_key)
    for subject in dict_:
        if key in dict_[subject]:
            for v in value:
                if v in dict_[subject][key]:
                # print(" as")
                # print(dict_[subject][geo_asWKT_key],type((wkt.loads(dict_[subject][geo_asWKT_key]))))

                    result_dict[f"{key}_{v}_{subject}"]=((wkt.loads(dict_[subject][geo_asWKT_key])))
                # break
    # print(len(result_dict))
    # html=draw_geo_map(result_dict,"geo")
    print(len(result_dict))
    return result_dict


for i in col_name_mapping_dict:
    revers_mapping_dict[col_name_mapping_dict[i]['graph_name']]=i
    for col_ in get_column_names(i):
        if col_ not in col_name_mapping_dict[i]:
            col_name_mapping_dict[i][col_]=col_