import ast
import re

import psycopg2
import time
from shapely.geometry import shape
import geopandas as gpd
from shapely.wkt import loads
from shapely.geometry import mapping
# from draw_geo import draw_geo_map
from SPARQLWrapper import SPARQLWrapper, JSON
from tqdm import tqdm
from bounding_box import find_boundbox
from shapely import wkb
from shapely import wkt
from itertools import islice
import copy
from shapely.geometry import base
globals_dict = {}
global_id_attribute={}
global_id_geo={}

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
col_name_mapping_dict={
"soil":{
    "osm_id":"objectid",
    "fclass":"leg_text",
    "select_query":"SELECT leg_text,objectid,geom",
    "graph_name":"soilcomplete"

}   ,
    "soilcomplete":{
    "osm_id":"objectid",
    "fclass":"leg_text",
    "select_query":"SELECT leg_text,objectid,geom",
    "graph_name":"soilcomplete"

}   ,
"buildings":{
    "osm_id": "osm_id",
    "fclass": "fclass",
    "name": "name",
    "select_query": "SELECT buildings AS source_table, fclass,name,osm_id,geom",
    "graph_name":"buildings"
},
"landuse":{
    "osm_id": "osm_id",
    "fclass": "fclass",
    "name":"name",
    "select_query": "SELECT landuse AS source_table, fclass,name,osm_id,geom",
    "graph_name":"landuse"
}

}
def auto_add_WHERE_AND(sql_query):

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
            modified_query[-1] += '\nLIMIT 20000;'
        # 将处理后的行合并回一个单一的字符串
        return '\n'.join(modified_query)

def cur_action(query):
    try:
        query=auto_add_WHERE_AND(query)

        # print(query)

        cur.execute(query)
        rows =cur.fetchall()
        return rows
    except psycopg2.Error as e:
        cur.execute("ROLLBACK;")
        print(query)
        raise Exception(f"SQL error: {e}")



def set_bounding_box(region_name):
    if region_name!=None:
        globals_dict["bounding_box_region_name"] = region_name
        globals_dict['bounding_coordinates'], globals_dict['bounding_wkb'], response_str = find_boundbox(region_name)

        # print(wkb.loads(bytes.fromhex(globals_dict['bounding_wkb'])))

        geo_dict = {
                globals_dict["bounding_box_region_name"]: (wkb.loads(bytes.fromhex((globals_dict['bounding_wkb']))))}



        return {'geo_map':geo_dict}
    else:
        return None

def ids_of_attribute(graph_name,specific_col=None, bounding_box_coordinats=None):
    bounding_judge_query=''
    if 'bounding_coordinates' in globals_dict:
        bounding_box_coordinats = globals_dict['bounding_coordinates']
        min_lat, max_lat, min_lon, max_lon = bounding_box_coordinats
        bounding_judge_query=f"ST_Intersects(geom, ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat}, {4326}))"
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


    rows = cur_action(bounding_query)


    for row in rows:
        attributes_set.add(row[0])
    return attributes_set

def judge_area(type):
    if 'large' in str(type) or 'small' in str(type) or 'big' in str(type):
        return True
    else:
        return False

def ids_of_type(graph_name, type_dict, bounding_box_coordinats=None):


    """
    globals_dict["bounding_box_region_name"]=region_name
    globals_dict['bounding_coordinates'],globals_dict['bounding_wkb']=find_boundbox(region_name)

    type_dict={'non_area_col':{'fclass':fclass_list...,'name':name_list...},'area_num':area_num}
    """
    area_num=None

    select_query=col_name_mapping_dict[graph_name]['select_query']
    graph_name_modify=col_name_mapping_dict[graph_name]['graph_name']
    fclass=col_name_mapping_dict[graph_name]['fclass']
    osm_id=col_name_mapping_dict[graph_name]['osm_id']

    bounding_judge_query = ""
    if 'bounding_coordinates' in globals_dict:
        bounding_box_coordinats = globals_dict['bounding_coordinates']
        min_lat, max_lat, min_lon, max_lon = bounding_box_coordinats
        bounding_judge_query=f"ST_Intersects(geom, ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat}, {4326}))"

    fclass_row = ''

    for col_name,single_type_list in type_dict['non_area_col'].items():
        # print(col_name,single_type_list)
        if single_type_list=='all':
            fclass_row += ''
        elif len(single_type_list)>1:
            fclass_row+=f"\n{col_name_mapping_dict[graph_name][col_name]} in {tuple(single_type_list)}"
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
    # print(final_query)
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
    print(len(feed_back))
    if type_dict['area_num']!=None:
        feed_back=area_filter(feed_back, type_dict['area_num'])['id_list'] #计算面积约束
        print(len(feed_back),'area_num',type_dict['area_num'])
    if "bounding_box_region_name" in globals_dict:
        geo_dict = {globals_dict["bounding_box_region_name"]:  (wkb.loads(bytes.fromhex((globals_dict['bounding_wkb']))))}
    else:
        geo_dict = {}

    geo_dict.update(feed_back)
    if len(feed_back)==0:
        raise Exception(f'Nothing found for {type_dict}! Please change an area and search again.')

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

def geo_calculate(data_list1_original, data_list2_original, mode, buffer_number=0):
    if mode=='area_calculate':
        return area_filter(data_list1_original, buffer_number)


    #data_list1.keys() <class 'shapely.geometry.polygon.Polygon'>
    """
    buildings in forest

    :param data_list1_original:  smaller element as subject buildings 主语
    :param data_list2_original:  bigger element as object forest 宾语
    :param mode:
    :param buffer_number:
    :return:
    """
    data_list1=copy.deepcopy(data_list1_original)
    data_list2=copy.deepcopy(data_list2_original)
    if mode=='contains':
        mode='in'
        data_list1 = copy.deepcopy(data_list2_original)
        data_list2 = copy.deepcopy(data_list1_original)
    if isinstance(data_list1, str):
        data_list1 = globals_dict[data_list1]
        data_list2 = globals_dict[data_list2]

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
    result_list = []
    all_id_list = []
    osmId1_dict = {}
    parent_list=[]
    child_list=[]
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
                parent_list.extend(matching_osmIds)
                child_list.append(osmId1)
                # result_list.append(f"set1 id {osmId1} in set2 id {matching_osmIds}")
                # print(f"set1 id {osmId1} in set2 id {matching_osmIds}")
        print(len(osmId1_dict))

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
                child_list.extend(matching_osmIds)
                parent_list.append(osmId2)
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
                parent_list.extend(matching_osmIds)
                child_list.append(osmId1)
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

        result_list.append("distance between set1 id " + str(closest_pair[0]) + " set2 id " + str(
            closest_pair[1]) + " is closest: " + str(min_distance) + " m")
    elif mode == "single_distance":
        distance = list(data_list1[0].values())[0].distance(list(data_list2[0].values())[0])
        # print(distance)
    """
        globals_dict["bounding_box_region_name"]=region_name
    globals_dict['bounding_coordinates'],globals_dict['bounding_wkb']=find_boundbox(region_name)

    """

    if "bounding_box_region_name" in globals_dict:
        # geo_dict = {globals_dict["bounding_box_region_name"]: wkb.loads(bytes.fromhex(globals_dict['bounding_wkb']))}
        geo_dict = {globals_dict["bounding_box_region_name"]: (wkb.loads(bytes.fromhex((globals_dict['bounding_wkb']))))}
    else:
        geo_dict = {}
    # data_list1.update(data_list2)
    parent_geo_dict=transfer_id_list_2_geo_dict(parent_list, data_list2)
    child_geo_dict=transfer_id_list_2_geo_dict(child_list, data_list1)
    geo_dict.update(parent_geo_dict)
    geo_dict.update(child_geo_dict)

    print(len(geo_dict))

    # html=draw_geo_map(geo_dict, "geo")
    # with open('my_list.pkl', 'wb') as file:
    #     pickle.dump(osmId1_list, file)


    return {'object':{'id_list':parent_geo_dict},'subject':{'id_list':child_geo_dict},'geo_map':geo_dict}
    # return {'subject_id_list':parent_list,'object_id_list':child_list,'geo_map':geo_dict}
    # return child_list,parent_list,geo_dict
    # return geo_dict

    # return {'subject_id_list':parent_list,'object_id_list':child_list,'geo_map':geo_dict}
    # return child_list,parent_list,geo_dict
    # return geo_dict


#
# print(all_graph_name)
# list_type_of_graph_name('http://example.com/landuse')
def id_explain(id_list):

    if isinstance(id_list, dict): #ids_of_type return的id_list是可以直接计算的字典
        if 'id_list' in id_list:
            id_list = id_list['id_list']
        elif 'subject' in id_list:
            id_list = id_list['object']['id_list']
    # print(id_list)

    element_count = {}

    # Iterate over each element in the input list
    for element in id_list:
        # If the element is already in the dictionary, increment its count
        attribute=global_id_attribute[element]
        if attribute in element_count:
            element_count[attribute] += 1
        # If the element is not in the dictionary, add it with a count of 1
        else:
            element_count[attribute] = 1

    return dict(sorted(element_count.items(), key=lambda item: item[1], reverse=True))

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
def get_table_for_sql():
    query = """
            SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
            """

def sql_debug():
    def sql_get_tabel():
        query = """
        SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
        """

    # 数据库连接参数
    # engine = create_engine('postgresql://postgres:9417941@localhost:5432/osm_database')

    set_bounding_box('munich maxvorstadt')
    # 创建连接
    bounding_box_coordinats = globals_dict['bounding_coordinates']
    min_lat, max_lat, min_lon, max_lon = bounding_box_coordinats
    # 定义边界框

    srid = 4326  # 假设使用WGS 84

    # 执行查询
    bounding_query = f"""
    SELECT *
    FROM buildings
    WHERE ST_Intersects(geom, ST_MakeEnvelope({min_lon}, {min_lat}, {max_lon}, {max_lat}, {srid}));
    """
    print(bounding_query)

    attribute_query = f"""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'buildings';
    """

    query = """
    SELECT * FROM buildings;

    """
    start_time = time.time()
    # from shapely.wkb import loads
    rows = cur_action(bounding_query)

    end_time = time.time()
    print(end_time - start_time)
    # 打印结果
    print(len(rows))
    result_dict = {}
    start_time = time.time()
    for row in rows:
        result_dict[row[2] + "_" + row[3]+"_" + row[4]] = (wkb.loads(bytes.fromhex(row[6])))
        # print(row)
        # crs = CRS.from_user_input(loads((row[6]), hex=True).srid)
        # print(crs.to_epsg())

        break
    print(result_dict)
    end_time = time.time()
    print(end_time - start_time)
    geo_dict = {
        globals_dict["bounding_box_region_name"]: mapping(wkb.loads(bytes.fromhex((globals_dict['bounding_wkb']))))}
    geo_dict.update(result_dict)
    # draw_geo_map(geo_dict, 'geo')
    # 关闭连接
    cur.close()
    conn.close()
#{'name': ['Berufs- und Technikerschule', 'Universität', 'TEH-Akademie', 'Berufsfachschule', 'Fakultät für Informatik der LMU', 'Technische Hochschule Ingolstadt', 'Bildungshaus', 'Berufsschule', 'Staatliche Fachoberschule und Berufsoberschule Altötting', 'Simmernschule', 'Berufsbildung- und Technologiezentrum | Kaminkehrer-Innung Oberbayern', 'Isardammschule', 'Knosporus CampusGarten', 'Sonderberufsschule', 'Wichtel Akademie'], 'fclass': ['school', 'college', 'university']

# set_bounding_box("Munich ismaning")
# type_dict={'non_area_col':{'name': {'Hauptbahnhof'}, 'fclass':'all'},'area_num':None}
# (ids_of_type('buildings', type_dict))
# print(ids_of_attribute('landuse', 'name'))
# a=(ids_of_type('soil', '82: Fast ausschließlich Kalkpaternia aus Carbonatfeinsand bis -schluff über Carbonatsand bis -kies (Auensediment, hellgrau)'))
# print(ids_of_attribute('soil'))
# print(ids_of_attribute('soil'))
# print(ids_of_attribute('buildings'))
# print(ids_of_attribute('soil'))
# aa=['21: Fast ausschließlich humusreiche Pararendzina aus Carbonatsandkies bis -schluffkies (Schotter), gering verbreitet mit flacher Flussmergeldecke', '57: Fast ausschließlich Rendzina aus Kalktuff oder Alm', '4a: Überwiegend Parabraunerde und verbreitet Braunerde aus Schluff bis Schluffton (Lösslehm) über Carbonatschluff (Löss)']
# ids_of_type('landuse',['smallest 3','park'])
# print(ids_of_attribute('landuse','name'))
# print(ids_of_attribute('landuse'))
# print(ids_of_attribute('soil')
# a=ids_of_type('landuse','park')
# geo_calculate(geo_result['subject']['id_list'])
# set_bounding_box('munich')
# print(len(ids_of_attribute('landuse')))