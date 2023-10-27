from rdflib import Graph

# 加载Shapefile转换得到的RDF数据
shapefile_graph = Graph()
shapefile_graph.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\osm_land_use.ttl")

# 加载OSM转换得到的RDF数据
osm_graph = Graph()
osm_graph.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\path_to_output.ttl")

# 融合两个图
merged_graph = shapefile_graph + osm_graph

# 保存融合后的RDF文件
merged_graph.serialize(destination="merged.ttl", format="turtle")
