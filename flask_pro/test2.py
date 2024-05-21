import time

in_code_block = False
code_block_start = "```python"
code_block_end = "```"
line_buffer = ""
# 输入的列表
input_list =['\n', '```', 'python', '\n', '#', ' Set', ' the', ' bounding', ' box', ' to', ' Munich', ' Max', 'vor', 'stadt', '\n', 'set', '_b', 'ounding', '_box', '("', 'Mun', 'ich', ' Max', 'vor', 'stadt', ',', ' Munich', '")\n\n', '#', ' Get', ' the', ' ID', ' list', ' of', ' residential', ' areas', '\n', 'res', 'idential', '_', 'areas', ' =', ' id', '_list', '_of', '_entity', '("', 'res', 'idential', ' area', '")\n\n', '#', ' Get', ' the', ' ID', ' list', ' of', ' forests', '\n', 'fore', 'sts', ' =', ' id', '_list', '_of', '_entity', '("', 'forest', '")\n\n', '#', ' Filter', ' residential', ' areas', ' that', ' are', ' within', ' ', '100', 'm', ' of', ' forests', '\n', 'res', 'idential', '_ne', 'ar', '_fore', 'sts', ' =', ' geo', '_filter', '("', 'in', ' ', '100', 'm', ' of', '",', ' residential', '_', 'areas', ',', ' forests', ')\n\n', '#', ' Output', ' the', ' result', '\n', 'res', 'idential', '_ne', 'ar', '_fore', 'sts', '\n', '```']
for item in input_list:
        line_buffer += item
        # 检查是否遇到了Python代码块的起始标志
        if code_block_start.startswith(line_buffer) and not in_code_block:
            in_code_block = True
            line_buffer = ""  # 清空行缓冲区
            continue
        # 检查是否遇到了Python代码块的结束标志
        elif code_block_end.startswith(line_buffer) and in_code_block:
            in_code_block = False
            line_buffer = ""  # 清空行缓冲区
            continue

        # 如果不在代码块中，则打印行缓冲区内容
        if (not in_code_block and line_buffer) or (line_buffer.startswith('#')):
            print(item.replace('#','##><'), end='', flush=True)
            # time.sleep(0.1)  # 模拟逐字打印的效果

        # 如果遇到换行符，重置line_buffer
        if '\n' in item:
            line_buffer = ""


# # set_bounding_box
# set_bounding_box("Munich Ismaning")
#
# # Get the ID list of buildings
# buildings_id_list = id_list_of_entity("buildings")
#
#
# # Get the ID list of landuse which is forest
# forest_id_list = id_list_of_entity("landuse which is forest")
#
# # Filter buildings that are within 100m of the forest
# filtered_buildings_forest = geo_filter("in 100m of", buildings_id_list, forest_id_list)