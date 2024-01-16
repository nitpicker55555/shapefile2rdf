import requests
import re
from shapely.geometry import Polygon
from draw_geo import draw_geo_map
from shapely.wkb import dumps
# Nominatim API endpoint for search
def modify_region_advanced(region, horizontal_range, vertical_range):
    """
    Modify a region by specifying the horizontal and vertical ranges to keep.

    :param region: A list of coordinates [lower_latitude, upper_latitude, lower_longitude, upper_longitude]
    :param horizontal_range: A tuple (min_fraction, max_fraction) for the horizontal direction
    :param vertical_range: A tuple (min_fraction, max_fraction) for the vertical direction
    :return: A list of modified coordinates
    """
    lower_latitude, upper_latitude, lower_longitude, upper_longitude = region
    min_horizontal, max_horizontal = horizontal_range
    min_vertical, max_vertical = vertical_range

    # Calculate the new coordinates
    new_width = upper_longitude - lower_longitude
    new_height = upper_latitude - lower_latitude

    new_lower_longitude = lower_longitude + new_width * min_horizontal
    new_upper_longitude = lower_longitude + new_width * max_horizontal
    new_lower_latitude = lower_latitude + new_height * min_vertical
    new_upper_latitude = lower_latitude + new_height * max_vertical

    return [new_lower_latitude, new_upper_latitude, new_lower_longitude, new_upper_longitude]



def find_boundbox(name):
    nominatim_url = "https://nominatim.openstreetmap.org/search"

    # Query parameters
    query_params = {
        'q': ''+name,  # Your search query
        'format': 'json'
    }

    # Send GET request
    response = requests.get(nominatim_url, params=query_params)

    # Handle the response
    if response.status_code == 200:
        search_results = response.json()
        if search_results:
            first_result = search_results[0]
            bounding_box = first_result.get('boundingbox', None)
            if bounding_box:
                print(f"The bounding box for {first_result.get('display_name', 'unknown')} is: {bounding_box}")
            else:
                print("Bounding box not found for the first result.")
        else:
            print("No results found.")
    else:
        print(f"Failed to retrieve data: {response.status_code}")
    # print(bounding_box)
    # coordinates = re.findall(r"\d+\.\d+", bounding_box)

    # 将字符串坐标转换为浮点数
    # coordinates =  modify_region_advanced( [48.2016433, 48.2403103, 11.6435458, 11.70167735],(0.2, 0.6), (0.3,0.9))
    #
    coordinates = [float(coord) for coord in bounding_box]
    # print(coordinates)
    # print(coordinates)

    # 将坐标分解为纬度和经度
    lat1, lat2, lon1, lon2 = coordinates

    # 构建矩形的四个角点
    rectangle = Polygon([(lon1, lat1), (lon1, lat2), (lon2, lat2), (lon2, lat1), (lon1, lat1)])

    # 将矩形转换为WKB格式
    wkb = dumps(rectangle, hex=True)
    # draw_geo_map({name:wkb})

    return coordinates,wkb
# find_boundbox("garching")