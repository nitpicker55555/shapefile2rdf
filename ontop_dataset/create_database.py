from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
import rdflib

Base = declarative_base()


class Building(Base):
    __tablename__ = 'land_use'
    id = Column(Integer, primary_key=True)
    code = Column(Integer)
    fclass = Column(String)
    name = Column(String)
    osm_id = Column(String)
    type = Column(String)
    # geom = Column(Geometry('POLYGON', srid=4326))
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326))


ns1 = rdflib.Namespace("http://land_use/property/")
geo = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")


engine = create_engine('postgresql://postgres:9417941@localhost:5432/osm_database')
Base.metadata.create_all(engine)  # 创建表结构（如果表不存在）
Session = sessionmaker(bind=engine)
session = Session()


g = rdflib.Graph()
g.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\modified_osm2.ttl", format="turtle")
print("finds")

code = None
fclass = None
name = None
osm_id = None
type_ = None
geom = None


for s, p, o in g:
    print(s,p,o)
    print(ns1.code)
    if p == ns1.code:
        code = int(o)
    elif p == ns1.fclass:
        fclass = str(o)
    elif p == ns1.name:
        name = str(o)
    elif p == ns1.osm_id:
        osm_id = str(o)
    # elif p == ns1.type:
    #     type_ = str(o)
    elif p == geo.asWKT:
        geom = o


        if code is not None and fclass is not None and name is not None and osm_id is not None and geom is not None:
        # if code is not None and fclass is not None and name is not None and osm_id is not None and type_ is not None and geom is not None:
            print("12")
            building = Building(code=code, fclass=fclass, name=name, osm_id=osm_id, type=type_, geom=geom)
            session.add(building)

            code = None
            fclass = None
            name = None
            osm_id = None
            type_ = None
            geom = None

try:
    session.commit()
except Exception as e:
    print("An error occurred:", e)
    session.rollback()
finally:
    session.close()
