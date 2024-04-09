import time
import asyncio
import psycopg2,re
from draw_geo import draw_geo_map
from bounding_box import find_boundbox
# 数据库连接信息
host = "localhost"
dbname = "osm_database"
user = "postgres"
password = "9417941"
port = "5432"
api_key = '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'
# from gpt_api import change_statement

"""
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
PREFIX uom: <http://www.opengis.net/def/uom/OGC/1.0/>
PREFIX ns1: <http://example.org/property/>
PREFIX ex: <http://example.org/data/>

SELECT ?otherBuilding ?otherBuildingName ?otherBuildingType ?otherBuildingFclass ?otherOsmStr ?otherGeoStr
WHERE {
  # 查询指定的建筑物，并创建一个 100m 的缓冲区
  ?building a ns1:Building;
            ns1:osm_id "190282830";
            geo:asWKT ?targetGeoStr.
  BIND(geof:buffer(?targetGeoStr, 100, uom:metre) AS ?buffer)

  # 查询与缓冲区相交的其他建筑物
  ?otherBuilding a ns1:Building;
                 ns1:name ?otherBuildingName;
                 ns1:type ?otherBuildingType;
                 ns1:fclass ?otherBuildingFclass;
                 ns1:osm_id ?otherOsmStr;
                 geo:asWKT ?otherGeoStr.
  FILTER(geof:sfIntersects(?otherGeoStr, ?buffer))
}
LIMIT 5




PREFIX ns1: <http://example.org/property/>
PREFIX ex: <http://example.org/data/>

SELECT ?building ?buildingName ?buildingType ?buildingFclass
WHERE {
  ?building a ns1:Building;
            ns1:name ?buildingName;
            ns1:type ?buildingType;
            ns1:fclass ?buildingFclass.
}
LIMIT 5



PREFIX : <http://example.org/>
PREFIX ns1: <http://example.org/property/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>

SELECT ?idBuilding ?idLandUse (geof:distance(?wktBuilding, ?wktLandUse, <http://www.opengis.net/def/uom/OGC/1.0/metre>) as ?distance)
WHERE {
    {
        SELECT ?idBuilding ?wktBuilding WHERE {
            ?idBuilding a ns1:Building .
            ?idBuilding ns1:osm_id "1181064336" .
            ?idBuilding geo:asWKT ?wktBuilding .
        }
        LIMIT 1
    }
    {
        SELECT ?idLandUse ?wktLandUse WHERE {
            ?idLandUse a ns1:SoilMap .
            ?idLandUse ns1:id "1" .
            ?idLandUse geo:asWKT ?wktLandUse .
        }
        LIMIT 1
    }
}

PREFIX ns1: <http://example.org/property/>

SELECT ?soilMap ?kategorie ?redJahr ?shapeArea ?shapeLeng ?uebk25K ?uebk25L ?geom ?id
WHERE {
    ?soilMap a ns1:SoilMap ;
                          ns1:id ?id ;
             ns1:kategorie ?kategorie ;
             ns1:red_jahr ?redJahr ;
             ns1:shape_area ?shapeArea ;
             ns1:shape_leng ?shapeLeng ;
             ns1:uebk25_k ?uebk25K ;
             ns1:uebk25_l ?uebk25L ;
             ns1:geom ?geom .
}
ORDER BY RAND()
LIMIT 1


PREFIX : <http://example.org/>
PREFIX ns1: <http://example.org/property/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>

SELECT ?id ?wkt
WHERE {
    {
        SELECT ?id ?wkt WHERE {
            ?id a ns1:Building .
            ?id ns1:osm_id "1181064336" .
            ?id ns1:fclass ?fclass .
            ?id geo:asWKT ?wkt .
        }
        LIMIT 10
    }
    UNION
    {
        SELECT ?id ?wkt WHERE {
            ?id a ns1:land_use_ .
            ?id ns1:osm_id "68048452" .
            ?id ns1:fclass ?fclass .
            ?id geo:asWKT ?wkt .
        }
        LIMIT 10
    }
}

"""
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
    l.type AS land_use_type,
    l.name AS land_use_name, 
    l.geom AS land_use_geom,
    'buildings' AS table_name_buildings, 
    b.osm_id AS building_osm_id, 
    b.fclass AS building_fclass,
    b.type AS building_type,
    b.name AS building_name,
    b.geom AS building_geom
FROM 
    buildings l, 
    land_use b
WHERE 
    b.fclass = 'farmland' AND ST_Intersects(b.geom, l.geom)
    
    
        kategorie = Column(String, primary_key=True)
    red_jahr = Column(Integer)
    shape_area = Column(REAL)
    shape_leng = Column(REAL)
    uebk25_k = Column(String)
    uebk25_l = Column(String)
    
    SELECT 
    'buildings' AS table_name_land_use, 
    l.osm_id AS land_use_osm_id, 
    l.fclass AS land_use_fclass, 
    l.type AS land_use_type,
    l.name AS land_use_name, 
    l.geom AS land_use_geom,
    'bayern_soil_map' AS table_name_buildings, 
    b.kategorie AS building_osm_id, 
    b.red_jahr AS building_fclass,
    b.shape_area AS building_type,
    b.shape_leng AS building_name,
    b.geom AS building_geom
FROM 
    buildings l, 
    bayern_soil_map b
WHERE 
    ST_Intersects(b.geom, l.geom)
    
    
    
SELECT
    ST_Distance(a.geom, b.geom) AS distance
FROM
    bayern_soil_map a, buildings b
WHERE
    a.id = '5000' AND b.osm_id = '241236137';


SELECT
    a.id AS soil_map_id,
    b.osm_id AS building_osm_id,
    ST_AsText(a.geom) AS soil_map_geom,
    ST_AsText(b.geom) AS building_geom
FROM
    bayern_soil_map a,
    land_use b
WHERE
    ST_Intersects(a.geom, b.geom);



SELECT
    a.id AS soil_map_id,
    b.osm_id AS building_osm_id,
    ST_AsText(ST_Transform(a.geom, 4326)) AS soil_map_geom_transformed,
    ST_AsText(b.geom) AS building_geom
FROM
    bayern_soil_map_25832 a,
    buildings b
WHERE
    ST_Intersects(ST_Transform(a.geom, 4326), b.geom);

"""
def location_query(list_,forest=True):
    print(list_)
    if forest:
        location_query="""
            SELECT
                'land_use' AS table_name_land_use,
                l.osm_id AS land_use_osm_id,
                l.fclass AS land_use_fclass,
                l.type AS land_use_type,
                l.name AS land_use_name,
                l.geom AS land_use_geom
            
            FROM
        land_use l
    
            
            
            WHERE
                l.fclass = 'forest' AND
                ST_Intersects(l.geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326)) 
    
        
        """%(list_[3],list_[0],list_[2],list_[1])
        print(location_query)
        return location_query
    else:
        location_query = """
        SELECT
            'land_use' AS table_name_land_use,
            l.osm_id AS land_use_osm_id,
            l.fclass AS land_use_fclass,
            l.type AS land_use_type,
            l.name AS land_use_name,
            l.geom AS land_use_geom,
                'buildings' AS table_name_buildings, 
    b.osm_id AS building_osm_id, 
    b.fclass AS building_fclass,
    b.type AS building_type,
    b.name AS building_name,
    b.geom AS building_geom
        
        FROM
    land_use l, 
    buildings b
        
        
        WHERE
            l.fclass = 'forest' AND
            ST_Intersects(l.geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326)) AND
            

                ST_DWithin(
        ST_Transform(b.geom, 3857), 
        ST_Transform(l.geom, 3857),
       100
    ) 
    AND
    ST_Intersects(b.geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326)) 
    
    
    
    


        """ % (list_[3], list_[0], list_[2], list_[1],list_[3], list_[0], list_[2], list_[1])
        # print(location_query)
        return location_query
number_query="""
SELECT 
    'land_use' AS table_name_land_use, 
    l.osm_id AS land_use_osm_id, 
    l.fclass AS land_use_fclass, 
    l.type AS land_use_type,
    l.name AS land_use_name, 
    l.geom AS land_use_geom,
    'buildings' AS table_name_buildings, 
    b.osm_id AS building_osm_id, 
    b.fclass AS building_fclass,
    b.type AS building_type,
    b.name AS building_name,
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
    l.type AS land_use_type,
    l.name AS land_use_name, 
    l.geom AS land_use_geom,
    'buildings' AS table_name_buildings, 
    b.osm_id AS building_osm_id, 
    b.fclass AS building_fclass,
    b.type AS building_type,
    b.name AS building_name,
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

        map_dict={}

        nquery = input("input:")
        # if extract_num(nquery)!=False and "ismaning" not in nquery:
        #     query=number_query.replace("383499448",extract_num(nquery))
        #     indication="Intersection problem: show specific intersected element (Building id:%s)"%extract_num(nquery)
        # elif "farmland" in nquery:
        #     query=land_query
        #     indication = "Intersection problem: show specific intersected land (Farmland)"
        # elif "ismaning" in nquery:
        #
        #     indication = "Region limited: (munich ismaning) \nBuffer problem: show buffer zone (100m) of (forest) for (buildings) in (munich ismaning)"
        #
        # else:
        #     indication="Intersection problem: show all intersected elements"
        #     query=all_query
        # print("-------------------")
        # print("Generating query...")
        # print("-------------------")
        # # time.sleep(4)
        #
        # print(indication)
        # coordinates_list, wkb_str = find_boundbox("munich ismaning")
        # print(coordinates_list)
        #
        # query = location_query(corrdinates_list, False)
        # map_dict.update({"munich ismaning": wkb_str})
        # print("-------------------")
        # print("Grammar correct!")
        # print("-------------------")
        # system_content="I will give you a sql query, please translate it to natural language in a simple way, and do not mention sql"
        # translation= (change_statement(query,system_content))
        # print("Do you want to search: "+translation+"?")
        # print("please input yes/no \n\n(If you think this query is not what you need, please input no, then we can reproduce the query.)")
        # input("input:")
        # print("-------------------")
        # # 执行查询

        #
        result={}
        # # nquery=input(":")
        no_buffer=False
        # if "ffff" in nquery:
        #     no_buffer=True
        #     nquery=nquery.replace("ffff","")


        query = get_multiline_input()
        print("searching...")
        cur.execute(query)
        print("search finished.")
        # 获取查询结果
        rows = cur.fetchall()

        for row in rows:
            # print(row)
            for i in range(len(row)):
                if row[i]==None:
                    result[i]=""
                else:
                    result[i]=row[i]
            print(result)
            # if no_buffer:
            #     map_dict.update(
            #        {result[0] + " / " + result[1] + " / " + result[2] + " / " + result[3] + " / " + result[4]: result[5]})
            # else:
            #
            #
            #     print(" / " +result[0] + " / " + result[1] + " / " + result[2]," / / " + result[6] + " / " + result[7] + " / " + result[8])

                # map_dict.update({result[0] + " / " + result[1] + " / " + result[2] + " / " + result[3]+ " / " + result[4]:result[5], result[6] + " / " + result[7] + " / " + result[8] + " / " + result[9]+ " / " + result[10]:result[11]})
        print("-------------------")
        print("Total results: ",len(rows))
        print("-------------------")
        print("Generating the map...")
        print("-------------------")
        # draw_geo_map(map_dict)

        print("Map finished, please check it in browser.")
        # 关闭 cursor 和连接
        # cur.close()
        # conn.close()
    except Exception as e:
        print("Error in executing query")
        print(e)

