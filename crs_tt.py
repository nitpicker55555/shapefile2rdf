import geopandas as gpd

# 读取数据文件
gdf = gpd.read_file(r"C:\Users\Morning\Desktop\hiwi\ttl_query\shape_file\mbk25_epsg25832\shape\Moore_Bayern.shp")

# 查看数据的CRS信息
print(gdf.crs)
