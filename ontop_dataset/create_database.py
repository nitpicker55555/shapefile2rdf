from sqlalchemy import create_engine, Column, Integer, String,REAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
import rdflib

Base = declarative_base()


class Building(Base):
    __tablename__ = 'soilnoraml'
    # id = Column(Integer, primary_key=True)
    # code = Column(Integer)
    # fclass = Column(String)
    # name = Column(String)
    # osm_id = Column(String)
    # type = Column(String)
    # # geom = Column(Geometry('POLYGON', srid=4326))
    # geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326))
    id= Column(Integer, primary_key=True)
    kategorie = Column(String)
    red_jahr = Column(Integer)
    shape_area = Column(REAL)
    shape_leng = Column(REAL)
    uebk25_k = Column(String)
    uebk25_l = Column(String)
    # geom = Column(Geometry('POLYGON', srid=4326))
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=25832))
"""
    ns1:kategorie "Vorherrschend Anmoorgley und Moorgley, gering verbreitet Gley über Niedermoor, humusreicher Gley und Nassgley, teilweise degradiert" ;
    ns1:red_jahr "2023" ;
    ns1:shape_area 8.786226e+04 ;
    ns1:shape_leng 1.737214e+03 ;
    ns1:uebk25_k "65c" ;
    ns1:uebk25_l "65c: Fast ausschließlich Anmoorgley, Niedermoorgley und Nassgley aus Lehmsand bis Lehm (Talsediment); im Untergrund carbonathaltig" ;
    geo:asWKT "POLYGON [
"""

ns1 = rdflib.Namespace("http://example.org/property/")
geo = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")


engine = create_engine('postgresql://postgres:9417941@localhost:5432/osm_database')
Base.metadata.create_all(engine)  # 创建表结构（如果表不存在）
Session = sessionmaker(bind=engine)
session = Session()


g = rdflib.Graph()
g.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\modified_Moore_Bayern_4326_index.ttl", format="turtle")
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

for s, p, o in g:
    # 根据谓词p设置属性
    print(".")
    if p == ns1.kategorie:
        properties[s]['kategorie'] = str(o)
    elif p == ns1.red_jahr:
        properties[s]['red_jahr'] = int(o)
    elif p == ns1.shape_area:
        properties[s]['shape_area'] = float(o)
        # print(float(o))
    elif p == ns1.shape_leng:
        properties[s]['shape_leng'] = float(o)
    elif p == ns1.uebk25_k:
        properties[s]['uebk25_k'] = str(o)
    elif p == ns1.uebk25_l:
        properties[s]['uebk25_l'] = str(o)
    elif p == geo.asWKT:
        properties[s]['geom'] = o

# 遍历每个主题s的属性字典
num_index=0
for s, attrs in properties.items():
    # 确保所有需要的属性都存在
    print("..")
    if all(key in attrs for key in ['kategorie', 'red_jahr', 'shape_area','shape_leng', 'uebk25_k', 'uebk25_l','geom']):
        num_index+=1
        # 创建Building对象
        building = Building(
            id=num_index,
            kategorie=attrs['kategorie'],
            red_jahr=attrs['red_jahr'],
            shape_area=attrs['shape_area'],
            shape_leng=attrs['shape_leng'],
            uebk25_k=attrs['uebk25_k'],
            uebk25_l=attrs['uebk25_l'],
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
