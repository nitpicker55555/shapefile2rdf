import geopandas as gpd


def convert_and_reproject_shapefile(input_shapefile, output_geojson, input_epsg, output_epsg):
    # 读取Shapefile
    gdf = gpd.read_file(input_shapefile)

    # 设置原始EPSG坐标系统（如果GeoDataFrame未自动检测）
    if not gdf.crs:
        gdf.set_crs(epsg=input_epsg, inplace=True)

    # 转换坐标系统到目标EPSG
    gdf = gdf.to_crs(epsg=output_epsg)

    # 将转换后的GeoDataFrame保存为GeoJSON
    gdf.to_file(output_geojson, driver='GeoJSON')


# 使用示例
input_shapefile_path = r"C:\Users\Morning\Documents\WeChat Files\wxid_pv2qqr16e4k622\FileStorage\File\2024-04\可视化\Munich_boundary\Munich_boundary.shp"
output_geojson_path = r'C:\Users\Morning\Documents\WeChat Files\wxid_pv2qqr16e4k622\FileStorage\File\2024-04\可视化\output_file.geojson'
convert_and_reproject_shapefile(input_shapefile_path, output_geojson_path, 3035, 4326)
