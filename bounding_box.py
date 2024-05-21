import re

import requests
from shapely.geometry import Polygon
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


def parse_coordinates(input_string):
    # Split input string by lines
    lines = input_string.strip().split('\n')

    coordinates_dict = {}

    for line in lines:
        # Use regex to capture coordinates and place names with spaces
        match = re.match(r'([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+(.+)', line)
        if match:
            lon1, lat1, lon2, lat2, place = match.groups()
            # Create list with latitudes first, then longitudes
            coordinates = [lat1, lat2, lon1, lon2]
            coordinates_dict[place] = coordinates


    return coordinates_dict
def find_boundbox(name,mode='keep'):
    # nominatim_url = "https://nominatim.openstreetmap.org/search"
    # name=name.lower()
    # bounding_box=''
    # if 'germany' in name.lower():
    #     name=name.replace('germany','')
    # if ',' in name.lower():
    #     name=name.replace(',','')
    #
    # # Query parameters
    # query_params = {
    #     'q': ''+name,  # Your search query
    #     'format': 'json'
    # }
    #
    # # Send GET request
    # response = requests.get(nominatim_url, params=query_params)
    # response_str=""
    # # Handle the response
    # if response.status_code == 200:
    #     search_results = response.json()
    #     if search_results:
    #         first_result = search_results[0]
    #         bounding_box = first_result.get('boundingbox', None)
    #         if bounding_box:
    #             response_str=f"The bounding box for {first_result.get('display_name', 'unknown')} is: {bounding_box}"
    #             print(f"The bounding box for {first_result.get('display_name', 'unknown')} is: {bounding_box}")
    #         else:
    #             response_str="Bounding box not found for the first result."
    #             print("Bounding box not found for the first result.")
    #     else:
    #         print("No results found.")
    # else:
    #     print(f"Failed to retrieve data: {response.status_code}")
    # print(bounding_box)
    # coordinates = re.findall(r"\d+\.\d+", bounding_box)

    # 将字符串坐标转换为浮点数
    # coordinates =  modify_region_advanced( [48.2016433, 48.2403103, 11.6435458, 11.70167735],(0.2, 0.6), (0.3,0.9))
    #10.81879,48.30329,12.26486,48.00646
    # 11.360777	48.061625	11.72291	48.248098
    # 11.625186	48.178202	11.804967	48.248098
    # POLYGON((11.360777 48.248098, 11.72291 48.248098, 11.72291 48.061625, 11.360777 48.061625, 11.360777 48.248098))
    aa = """
11.360777	48.061625	11.72291	48.248098 Munich
10.7634	48.2581	10.9593	48.4587 Augsburg
11.465675	48.165392	11.541543	48.205211 Munich Moosach
11.538923	48.139603	11.588192	48.157637 Munich Maxvorstadt
11.643546	48.201643	11.759782	48.278978 Munich Ismaning
11.640451	48.330606	11.792508	48.449032 Freising
11.499759	48.213303	11.615142	48.280737 Oberschleissheim
    """
    address_dict=parse_coordinates(aa)
    # print(address_dict)
    if mode=='changed':
        bounding_box=name
    else:
        bounding_box=address_dict[name]

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

    return coordinates,wkb,'bounding'

def bounding_box_test(name):
    name=name.lower()
    if 'germany' in name.lower():
        name=name.replace('germany','')
    if ',' in name.lower():
        name=name.replace(',','')
    nominatim_url = "https://nominatim.openstreetmap.org/search"

    # Query parameters
    query_params = {
        'q': ''+name,  # Your search query
        'format': 'json'
    }

    # Send GET request
    response = requests.get(nominatim_url, params=query_params)
    response_str=""
    # Handle the response
    if response.status_code == 200:
        search_results = response.json()
        if search_results:
            print(search_results)
# print(find_boundbox("Munich Moosach"))