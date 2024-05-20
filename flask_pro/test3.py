import re


def parse_coordinates_with_spaces(input_string):
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


input_string = """
11.360777	48.061625	11.72291	48.248098 Munich
10.7634	48.2581	10.9593	48.4587 Augsburg
11.465675	48.165392	11.541543	48.205211 Munich Moosach
11.538923	48.139603	11.588192	48.157637 Munich Maxvorstadt
11.643546	48.201643	11.759782	48.278978 Munich Ismaning
11.640451	48.330606	11.792508	48.449032 Freising
11.499759	48.213303	11.615142	48.280737 Oberschleissheim
"""

coordinates_dict = parse_coordinates_with_spaces(input_string)
print(coordinates_dict.keys())