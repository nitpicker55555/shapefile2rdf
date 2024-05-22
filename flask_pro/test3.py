import time

# 输入的列表
input_list = ['\n', '\n```', '\npython', '\n\n', '\n#', '\n Set', '\n the', '\n bounding', '\n box', '\n to', '\n Munich', '\n Max', '\nvor', '\nstadt', '\n\n', '\nset', '\n_b', '\nounding', '\n_box', '\n("', '\nMun', '\nich', '\n Max', '\nvor', '\nstadt', '\n,', '\n Munich', '\n")\n\n', '\n#', '\n Get', '\n the', '\n ID', '\n list', '\n of', '\n residential', '\n areas', '\n\n', '\nres', '\nidential', '\n_', '\nareas', '\n =', '\n id', '\n_list', '\n_of', '\n_entity', '\n("', '\nres', '\nidential', '\n area', '\n")\n\n', '\n#', '\n Get', '\n the', '\n ID', '\n list', '\n of', '\n forests', '\n\n', '\nfore', '\nsts', '\n =', '\n id', '\n_list', '\n_of', '\n_entity', '\n("', '\nforest', '\n")\n\n', '\n#', '\n Filter', '\n residential', '\n areas', '\n that', '\n are', '\n within', '\n ', '\n100', '\nm', '\n of', '\n forests', '\n\n', '\nres', '\nidential', '\n_ne', '\nar', '\n_fore', '\nsts', '\n =', '\n geo', '\n_filter', '\n("', '\nin', '\n ', '\n100', '\nm', '\n of', '\n",', '\n residential', '\n_', '\nareas', '\n,', '\n forests', '\n)\n\n', '\n#', '\n Output', '\n the', '\n result', '\n\n', '\nres', '\nidential', '\n_ne', '\nar', '\n_fore', '\nsts', '\n\n', '\n```']
# 定义一个标志变量来标记是否在Python代码块中
in_code_block = False
code_block_start = "```python"
code_block_end = "```"
line_buffer = ""

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
    if (not in_code_block and line_buffer) or line_buffer.startswith('#'):
        print(item, end='', flush=True)
        time.sleep(0.1)  # 模拟逐字打印的效果

    # 如果遇到换行符，重置line_buffer
    if '\n' in item  :
        line_buffer = ""
