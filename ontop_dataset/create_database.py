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
    geom = Column(Geometry('POLYGON', srid=4326))


# RDF Namespaces
ns1 = rdflib.Namespace("http://example.org/property/")
geo = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")

# 创建数据库连接
engine = create_engine('postgresql://postgres:9417941@localhost:5432/mydatabase')
Base.metadata.create_all(engine)  # 创建表结构（如果表不存在）
Session = sessionmaker(bind=engine)
session = Session()

# 解析Turtle文件
g = rdflib.Graph()
g.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\modified_osm.ttl", format="turtle")
print("finds")
# 在循环的开始处初始化所有变量
code = None
fclass = None
name = None
osm_id = None
type_ = None
geom = None

# 遍历图中的三元组
for s, p, o in g:
    # print(s,p,o)

    if p == ns1.code:
        code = int(o)
    elif p == ns1.fclass:
        fclass = str(o)
    elif p == ns1.name:
        name = str(o)
    elif p == ns1.osm_id:
        osm_id = str(o)
    elif p == ns1.type:
        type_ = str(o)
    elif p == geo.asWKT:
        geom = o

        # 只有当所有变量都已经被定义时，才创建Building实例
        if code is not None and fclass is not None and name is not None and osm_id is not None and type_ is not None and geom is not None:
            print("12")
            building = Building(code=code, fclass=fclass, name=name, osm_id=osm_id, type=type_, geom=geom)
            session.add(building)
            # 重置变量以准备下一个Building实例的创建
            code = None
            fclass = None
            name = None
            osm_id = None
            type_ = None
            geom = None

# 提交会话
try:
    session.commit()
except Exception as e:
    print("An error occurred:", e)
    session.rollback()
finally:
    session.close()
