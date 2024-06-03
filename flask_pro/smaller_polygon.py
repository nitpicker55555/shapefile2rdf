from shapely.geometry import Polygon
from shapely.wkt import loads, dumps

def half_area_polygon(input_wkt):
    # 加载WKT字符串为多边形
    polygon = loads(input_wkt)
    # 获取原始多边形的面积
    original_area = polygon.area
    target_area = original_area / 2

    # 设定一个初始的缩放距离
    delta = -0.01  # 初始缩小量，负值表示向内缩
    tolerance = 0.0001  # 容差值，用于确定何时停止
    scaled_polygon = polygon

    # 循环调整缩放距离，直到达到目标面积的一半
    while True:
        # 使用buffer进行缩放
        scaled_polygon = polygon.buffer(delta, resolution=16)
        if scaled_polygon.area <= target_area + tolerance:
            break
        delta -= 0.01  # 逐步增加缩小的程度

    # 将结果多边形转换为WKT格式并返回
    return dumps(scaled_polygon)
def double_area_polygon(input_wkt):
    # 加载WKT字符串为多边形
    polygon = loads(input_wkt)
    # 获取原始多边形的面积
    original_area = polygon.area
    target_area = original_area * 2

    # 设定一个初始的扩展距离
    delta = 0.01  # 初始扩展量，正值表示向外扩
    tolerance = 0.0001  # 容差值，用于确定何时停止
    scaled_polygon = polygon

    # 循环调整扩展距离，直到达到目标面积的两倍
    while True:
        # 使用buffer进行扩展
        scaled_polygon = polygon.buffer(delta, resolution=16)
        if scaled_polygon.area >= target_area - tolerance:
            break
        delta += 0.01  # 逐步增加扩展的程度

    # 将结果多边形转换为WKT格式并返回
    return dumps(scaled_polygon)
# # 示例使用
# input_wkt = "POLYGON ((29.5 9.5, 30.5 9.5, 30.5 10.5, 29.5 10.5, 29.5 9.5))"
# output_wkt = double_area_polygon(input_wkt)
# print(output_wkt)
