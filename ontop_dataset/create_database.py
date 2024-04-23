from sqlalchemy import create_engine, Column, Integer, String,REAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
import rdflib

Base = declarative_base()
from tqdm import tqdm

class Building(Base):
    __tablename__ = 'soilcomplete'
    # id = Column(Integer, primary_key=True)
    # code = Column(Integer)
    # fclass = Column(String)
    # name = Column(String)
    # osm_id = Column(String)
    # type = Column(String)
    # # geom = Column(Geometry('POLYGON', srid=4326))
    # geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326))
    id= Column(Integer, primary_key=True)
    leg_einh = Column(String)
    leg_nr = Column(Integer)
    leg_text = Column(String)
    objectid = Column(Integer)
    shape_area = Column(REAL)
    shape_leng = Column(REAL)
    # geom = Column(Geometry('POLYGON', srid=4326))
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326))
"""
    ns1:leg_einh "101" ;
    ns1:leg_nr 10100 ;
    ns1:leg_text "101: Vorherrschend (Para-)Rendzina und Braunerde, gering verbreitet Terra fusca und Pseudogley aus Bunten Trümmermassen mit weitem Bodenartenspektrum, verbreitet mit flacher Deckschicht aus Schluff bis Lehm" ;
    ns1:objectid 1 ;
    ns1:shape_area 1.569228e+06 ;
    ns1:shape_leng 7.182522e+03 ;
    geo:asWKT 
"""

ns1 = rdflib.Namespace("http://example.org/property/")
geo = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")


engine = create_engine('postgresql://postgres:9417941@localhost:5432/osm_database')
Base.metadata.create_all(engine)  # 创建表结构（如果表不存在）
Session = sessionmaker(bind=engine)
session = Session()


g = rdflib.Graph()
g.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\soil_4326_repaired.ttl", format="turtle")
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

    if p == ns1.leg_einh:
        properties[s]['leg_einh'] = str(o)
    elif p == ns1.leg_nr:
        properties[s]['leg_nr'] = int(o)
    elif p == ns1.leg_text:
        properties[s]['leg_text'] = str(o)
        # print(float(o))
    elif p == ns1.objectid:
        properties[s]['objectid'] = int(o)
    elif p == ns1.shape_area:
        properties[s]['shape_area'] = float(o)
    elif p == ns1.shape_leng:
        properties[s]['shape_leng'] = float(o)
    elif p == geo.asWKT:
        properties[s]['geom'] = o
"""
    ns1:leg_einh "101" ;
    ns1:leg_nr 10100 ;
    ns1:leg_text "101: Vorherrschend (Para-)Rendzina und Braunerde, gering verbreitet Terra fusca und Pseudogley aus Bunten Trümmermassen mit weitem Bodenartenspektrum, verbreitet mit flacher Deckschicht aus Schluff bis Lehm" ;
    ns1:objectid 1 ;
    ns1:shape_area 1.569228e+06 ;
    ns1:shape_leng 7.182522e+03 ;
    geo:asWKT 
"""
# 遍历每个主题s的属性字典
num_index=0
for s, attrs in tqdm(properties.items()):

    if all(key in attrs for key in ['leg_einh', 'leg_nr', 'leg_text','objectid', 'shape_area', 'shape_leng','geom']):
        num_index+=1
        # 创建Building对象
        building = Building(
            id=num_index,
            leg_einh=attrs['leg_einh'],
            leg_nr=attrs['leg_nr'],
            leg_text=attrs['leg_text'],
            objectid=attrs['objectid'],
            shape_area=attrs['shape_area'],
            shape_leng=attrs['shape_leng'],
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
