from sqlalchemy import create_engine, Column, Integer, String,REAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
import rdflib

Base = declarative_base()
from tqdm import tqdm

class Building(Base):
    __tablename__ = 'landuse'
    # id = Column(Integer, primary_key=True)
    # code = Column(Integer)
    # fclass = Column(String)
    # name = Column(String)
    # osm_id = Column(String)
    # type = Column(String)
    # # geom = Column(Geometry('POLYGON', srid=4326))
    # geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326))
    id= Column(Integer, primary_key=True)
    fclass = Column(String)
    name = Column(String)
    osm_id = Column(String)
    # geom = Column(Geometry('POLYGON', srid=4326))
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326))
"""
<http://example.org/data/0> ns1:code 7208 ;
    ns1:fclass "meadow" ;
    ns1:name "Adelberger" ;
    ns1:osm_id "3401793" ;
    geo:asWKT "POLYGON [[(11.8986921 48.195019) (11.9010643 48.1957291) (11.901297 48.1950387) (11.9001733 48.1947152) (11.8996997 48.1945784) (11.8992682 48.1944537) (11.8991531 48.1944205) (11.8986921 48.195019)]]" .

"""

ns1 = rdflib.Namespace("http://example.org/property/")
geo = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")


engine = create_engine('postgresql://postgres:9417941@localhost:5432/osm_database')
Base.metadata.create_all(engine)  # 创建表结构（如果表不存在）
Session = sessionmaker(bind=engine)
session = Session()


g = rdflib.Graph()
g.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\landuse_repaired.ttl", format="turtle")
# g.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\modified_osm_buildings.ttl", format="turtle")
print("finds")

code = None
fclass = None
name = None
osm_id = None
type_ = None
geom = None
from collections import defaultdict

# 创建一个默认字典来存储每个主题s的属性
properties = defaultdict(dict)

for s, p, o in tqdm(g):

    if p == ns1.fclass:
        properties[s]['fclass'] = str(o)
    elif p == ns1.name:
        properties[s]['name'] = str(o)
    elif p == ns1.osm_id:
        properties[s]['osm_id'] = str(o)
    #     # print(float(o))
    # elif p == ns1.objectid:
    #     properties[s]['objectid'] = int(o)
    # elif p == ns1.shape_area:
    #     properties[s]['shape_area'] = float(o)
    # elif p == ns1.shape_leng:
    #     properties[s]['shape_leng'] = float(o)
    elif p == geo.asWKT:
        properties[s]['geom'] = o
"""
    ns1:fclass "meadow" ;
    ns1:name "Adelberger" ;
    ns1:osm_id "3401793" ;
    geo:asWKT "POLYGON [[(11.8986921 48.195019) (11.9010643 48.1957291) (11.901297 48.1950387) (11.9001733 48.1947152) (11.8996997 48.1945784) (11.8992682 48.1944537) (11.8991531 48.1944205) (11.8986921 48.195019)]]" .

"""
# 遍历每个主题s的属性字典
num_index=0
for s, attrs in tqdm(properties.items()):

    if all(key in attrs for key in ['osm_id', 'name', 'fclass','geom']):
        num_index+=1
        # 创建Building对象
        building = Building(
            id=num_index,
            osm_id=attrs['osm_id'],
            name=attrs['name'],
            fclass=attrs['fclass'],
            # objectid=attrs['objectid'],
            # shape_area=attrs['shape_area'],
            # shape_leng=attrs['shape_leng'],
            geom=attrs['geom']
        )
        # 添加到会话
        session.add(building)
try:
    session.commit()
except Exception as e:
    print("An error occurred:", e)
    session.rollback()
finally:
    session.close()
