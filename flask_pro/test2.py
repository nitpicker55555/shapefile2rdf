chat_result="""
```python
soil_types = list_type_of_graph_name("http://example.com/soil")
print(soil_types)

```
"""
chat2="""
```python
# 对土壤类型进行语义判断，筛选适合农业的类型
agricultural_soil_types = [
    "Anmoorgley",
    "Pseudogley",
    "Podsol",
    "Lehm",
    "Torf",
    "Humusreicher Gley"
]

# 利用语义判断，筛选出适合农业的土壤类型
suitable_types = [soil_type for soil_type in soil_types if any(agri_type in soil_type for agri_type in agricultural_soil_types)]
print(suitable_types)
```
"""
chat3="""
```python
suitable_for_agriculture = [
    '61a: Bodenkomplex: Vorherrschend An',
    '62c: Fast ausschließlich kalkhaltig',
    '64c: Fast ausschließlich kalkhaltig'
]

# 获取这些类型的id_list
soil_ids = list_id_of_type("http://example.com/soil", suitable_for_agriculture)
print(soil_ids)
```
"""
import ast

from geo_functions import *
import inspect
import sys
from io import StringIO
locals_dict = {}
globals_dict = globals()
output = StringIO()
original_stdout = sys.stdout

# 筛选出所有的函数
functions_dict = {name: obj for name, obj in globals_dict.items() if inspect.isfunction(obj)}
def main(chat_result):
    def extract_code(code_str):
        return code_str.split("```python")[1].split("```")[0]
    code_str=extract_code(chat_result)
    plt_show=False
    if "plt.show()" in code_str:
        plt_show=True
        print("plt_show")
        code_str=code_str.replace("plt.show()","plt.savefig('static/mat.png')")
    sys.stdout = output
    try:
        exec(code_str, functions_dict)
    except Exception as e:
        print(f"An error occurred: {e}")

    code_result = output.getvalue().replace('\00', '')
    output.truncate(0)
    sys.stdout = original_stdout
    if chat_result==chat2:

        print(code_result[:20])


    print(len((code_result)))
# main(chat_result)
# main(chat2)
main(chat3)