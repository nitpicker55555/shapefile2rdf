from rdflib import Graph, URIRef, Namespace,Literal
from rdflib.namespace import RDF

def add_fclass_to_subjects(ttl_file_path):
    # 加载TTL文件
    g = Graph()
    g.parse(ttl_file_path, format="ttl")

    # 定义命名空间
    ns1 = Namespace("http://example.org/property/") # 更新命名空间URI

    # 遍历所有subject
    for subject in set(g.subjects()):
        # 检查是否存在ns1:fclass属性
        if (subject, ns1.fclass, None) not in g:
            # 如果不存在，添加ns1:fclass属性，值为"soil"
            g.add((subject, ns1.fclass, Literal("soil")))

    # 将修改后的图保存回原文件或新文件
    g.serialize(r"C:\Users\Morning\Downloads\ontop-cli-5.1.1\input\modified_osm22.ttl", format="ttl")
    print("Added missing ns1:fclass 'soil' to subjects.")

# 使用函数示例
add_fclass_to_subjects(r"C:\Users\Morning\Downloads\ontop-cli-5.1.1\input\modified_osm.ttl")
