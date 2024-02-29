import webbrowser

import folium
import random


# 定义一个生成随机颜色的函数
def random_color():
    return "#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])


# 初始化地图
m = folium.Map(location=[45.372, -121.6972], zoom_start=12, tiles='Stamen Terrain')

# 初始化一个字典来存储名字到颜色的映射
name_to_color = {}

# 假设有一个列表，存储你的名字和相应的几何数据
# 这里用(name, geometry)元组的列表来模拟
data1={
  "type": "Polygon",
  "coordinates": [
    [
      [-121.6972, 45.372],
      [-121.696, 45.373],
      [-121.695, 45.374],
      [-121.694, 45.372],
      [-121.6972, 45.372]
    ]
  ]
}
data2={
  "type": "Polygon",
  "coordinates": [
    [
      [-121.6972, 45.372],
      [-121.696, 45.373],
      [-121.695, 45.374],
      [-121.694, 45.372],
      [-121.6972, 45.372]
    ]
  ]
}

features = [
    ('Name1', data1),
    ('Name2', data2),
    # 添加更多的名字和几何数据
]

# 为每个名字创建一个FeatureGroup，并添加到地图上
for name, geometry in features:
    # 如果名字还没有分配颜色，则分配一个新颜色
    if name not in name_to_color:
        name_to_color[name] = random_color()

    # 创建FeatureGroup
    fg = folium.FeatureGroup(name=name, show=True)

    # 添加GeoJson到FeatureGroup
    folium.GeoJson(
        geometry,
        style_function=lambda x, color=name_to_color[name]: {'fillColor': color, 'color': color},
        tooltip=name  # 添加带有名字的提示
    ).add_to(fg)

    # 将FeatureGroup添加到地图上
    fg.add_to(m)

# 添加图层控制器
folium.LayerControl().add_to(m)

# 显示地图
map_path = r'C:\Users\Morning\Desktop\hiwi\ttl_query\visualized_geometry_map.html'
m.save(map_path)
webbrowser.open('file://' + map_path)
# print(m._repr_html_())