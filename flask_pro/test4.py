code_str="""
geo_calculate(id1,id2,'buffer',100)
"""
# 移除字符串前后的空白字符（包括换行符）
lines = code_str.strip().split('\n')
# 分割字符串为行



# 尝试替换
new_code_str = code_str.replace(lines[-1], f"""
try:
    print({lines[-1]})
except:
    pass""")
print(new_code_str)


