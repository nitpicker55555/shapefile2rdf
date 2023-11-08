from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
import rdflib

Base = declarative_base()


class Building(Base):
    __tablename__ = 'buildings'
    id = Column(Integer, primary_key=True)
    code = Column(Integer)
    fclass = Column(String)
    name = Column(String)
    osm_id = Column(String)
    type = Column(String)
    # geom = Column(Geometry('POLYGON', srid=4326))
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326))


ns1 = rdflib.Namespace("http://example.org/property/")
geo = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")


engine = create_engine('postgresql://postgres:9417941@localhost:5432/osm_database')
Base.metadata.create_all(engine)  # 创建表结构（如果表不存在）
Session = sessionmaker(bind=engine)
session = Session()


g = rdflib.Graph()
g.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\modified_osm_buildings.ttl", format="turtle")
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
    if p == ns1.code:
        properties[s]['code'] = int(o)
    elif p == ns1.fclass:
        properties[s]['fclass'] = str(o)
    elif p == ns1.name:
        properties[s]['name'] = str(o)
    elif p == ns1.type:
        properties[s]['type'] = str(o)
    elif p == ns1.osm_id:
        properties[s]['osm_id'] = str(o)
    elif p == geo.asWKT:
        properties[s]['geom'] = o

# 遍历每个主题s的属性字典
for s, attrs in properties.items():
    # 确保所有需要的属性都存在
    print("..")
    if all(key in attrs for key in ['code', 'fclass', 'type','name', 'osm_id', 'geom']):

        # 创建Building对象
        building = Building(
            code=attrs['code'],
            fclass=attrs['fclass'],
            name=attrs['name'],
            osm_id=attrs['osm_id'],
            type=attrs['type'],
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
