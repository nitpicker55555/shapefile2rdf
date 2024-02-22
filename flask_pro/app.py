from geo_functions import *
from flask import Flask, Response, stream_with_context, request, render_template

import time
from openai import OpenAI
import os
from dotenv import load_dotenv
import ast
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()
import sys
from io import StringIO
from datetime import datetime

output = StringIO()
original_stdout = sys.stdout
app = Flask(__name__)

# 示例的 Markdown 文本（包含图片链接）
# ![示例图片](/static/data.png "这是一个示例图片")
import inspect
locals_dict = {}
globals_dict = globals()

# 筛选出所有的函数
functions_dict = {name: obj for name, obj in globals_dict.items() if inspect.isfunction(obj)}


markdown_text = """
要编写一个Python程序来读取一个文件夹（目录）中的所有文件和子目录
```python
import math

def draw_heart():
        for y in range(15, -15, -1):
            for x in range(-30, 30):
                if ((x * 0.04)**2 + (y * 0.1)**2 - 1)**3 - (x * 0.04)**2 * (y * 0.1)**3 <= 0:
                    print("*", end="")
                else:
                    print(" ", end="")
            print()
draw_heart()
```
<details>
    <summary>`Code result ▲`</summary>
       15
14
13
</details>


    


"""

geo_prompt = """You are an AI assistant that processes complex database queries. You have a virtual environment 
equipped with python. The python code you give will be automatically run by the system, so you can freely achieve 
your goals through python code. The code running results will be returned to you after the execution is completed. 
You can use python code to view all information about the current environment, or use matplotlib to draw charts. But 
note that if you want to get the value of a variable, please use print() to print it out; the variables in the code 
you give will be stored in the environment and can be called directly next time. The following functions are provided 
by me and you can use them directly: 

{

    "find_bounding_box": { "Argument": ["region_name"], "Description": "If user wants to get query result from a 
    specific location, you need to first run this function with argument region_name, then the other function would 
    limit its result in this region automatically (you don't need to add region name to other function). Example: if 
    user wants to search result from munich germany, input of this function would be ['munich germany']." 
    }, 
    "list_type_of_graph_name": { "Argument": ["graph_name"], "Description": "Enter the name of the graph you want to 
    query and it returns all types of that graph. For example, for a soil graph, the types are different soil types." 
    }, 
    "list_id_of_type": { "Arguments": ["graph_name", "type_name"], "Description": "Enter the graph name and type 
    name you want to query, and it returns the corresponding element IDs. If you want to get id_list from multi types 
    at the same time, you can input arg type_name as a list.","Example":" 
                
        If user wants to search soil that suitable for agriculture, first you need to figure out what kind of soil 
        the soil graph have using list_type_of_graph_name, soil_types=list_type_of_graph_name(
        "http://example.com/soil") then input type list you think is good for agriculture(please pick its full name 
        but not only index of this type), and use list_id_of_type to get its id_list soil_ids=list_id_of_type(
        "http://example.com/soil",[type_list]) 
        
        "
    },

        "geo_calculate": {
        "Arguments": [id_list_1, id_list_2,"function name",buffer_number=0],
        "Description": "
        geo_calculate function has functions: contains, intersects, buffer. 
        Input should be two id_list which generated by function list_id_of_type and function name you want to use. 
        
        function contains: return which id in id_list_2 geographically contains which id in id_list_1; function 
        intersects: return which id in id_list_2 geographically intersects which id in id_list_1; function buffer: 
        return which id in id_list_2 geographically intersects the buffer of which id in id_list_1, if you want to 
        call buffer, you need to specify the last argument "buffer_number" as a number. "Example": If user wants to 
        search buildings in farmland, first you need to figure out farmland and buildings in which graph using 
        function list_type_of_graph_name, then generate id_list for buildings and farmland using function 
        list_id_of_type, id_list1=list_id_of_type("http://example.com/buildings","building")
        id_list2=list_id_of_type("http://example.com/landuse","farmland"), 
        finally call function geo_calculate: contains_list=geo_calculate(id_list_1,id_list_2,"contains")
        

        
        "
    }
}

Database: The database has three graphs: ['http://example.com/landuse', 'http://example.com/soil', 
'http://example.com/buildings']; The soil graph contains many soil types. If a user asks you which soil types are 
suitable for agriculture, you need to make a semantic judgment based on the names of the types. 

Constraints: After each step you will receive feedback from functions, which contains results length and results, 
but you can only receive top 500 characters due to memory limitation. 
"""
normal_prompt = """
You have a virtual environment equipped with a python environment. The python code you 
give will be automatically run by the system, so you can freely achieve your goals through python 
code. The code running results will be returned to you after the execution is completed. You can use 
python code to view all information about the current environment, or use matplotlib to draw charts. 
But note that if you want to get the value of a variable, please use print() to print it out; the 
variables in the code you give will be stored in the environment and can be called directly next 
time.
"""



def chat_single(messages, mode="json"):
    if mode == "json":

        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            response_format={"type": "json_object"},
            messages=messages
        )
    else:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            stream=True,
            messages=messages,
        max_tokens=4096
        )
    return response


messages2 = []
messages2.append({"role": "system",
                  "content": geo_prompt
                  })


# html_content = markdown2.markdown(markdown_text)

def extract_code(code_str):
    return code_str.split("```python")[1].split("```")[0]
def len_str2list(result):
    try:
        # 尝试使用 ast.literal_eval 解析字符串
        result = ast.literal_eval(result)
        # 检查解析结果是否为列表
        return len(result)
    except (ValueError, SyntaxError):
        # 如果解析时发生错误，说明字符串不是有效的列表字符串
        try:
            dict_result=json.loads(result)
            return len(dict_result)
        except:

            return len(result)
def judge_list(result):
        try:
            # 尝试使用 ast.literal_eval 解析字符串
            result = ast.literal_eval(result)
            # 检查解析结果是否为列表
            return True
        except (ValueError, SyntaxError):
            # 如果解析时发生错误，说明字符串不是有效的列表字符串
            return False
def details_span(result):

    aa=f"""
<details>
    <summary>`Code result ▲ Length:{len_str2list(result)}`</summary>
       {str(result)}
</details>
    """

    return aa
def short_response(text_list):
    if len(str(text_list))>1000 and judge_list(text_list):
        if len_str2list(text_list)<40:
            result = ast.literal_eval(text_list)
            short_suitable_types = [t[:35] for t in result]
            return str(short_suitable_types)
        else:
            return text_list[:1000]
    else:
        return text_list[:1000]
@app.route('/')
def home():
    # 加载包含 Markdown 容器的前端页面
    return render_template('index.html')


@app.route('/submit', methods=['POST', 'GET'])
def submit():
    # 加载包含 Markdown 容器的前端页面
    data = request.get_json().get('text')  # 获取JSON数据
    print(data)  # 输出查看，实际应用中你可能会做其他处理
    messages2.append({"role": "user",
                      "content": data})

    chat_response = chat_single(messages2, "")

    def generate():
        chat_result = ''
        for chunk in chat_response:
            if chunk.choices[0].delta.content is not None:
                char = chunk.choices[0].delta.content
                print(char, end="")
                chat_result += char
                yield char

        messages2.append({"role": "assistant",
                          "content": str(chat_result)})
        if "```python" in chat_result:
            yield "\n\n`Code running...`\n"

            code_str = extract_code(chat_result)
            plt_show = False
            if "plt.show()" in code_str:
                plt_show = True
                print("plt_show")
                filename = f"plot_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                code_str = code_str.replace("plt.show()", f"plt.savefig('static/{filename}')")
            sys.stdout = output
            try:
                exec(code_str, functions_dict)
            except Exception as e:
                print(f"An error occurred: {e}")
            code_result = output.getvalue().replace('\00', '')
            output.truncate(0)
            sys.stdout = original_stdout

            if plt_show:
                code_result = f'![matplotlib_diagram](/static/{filename} "matplotlib_diagram")'
                yield code_result
            else:
                code_result=code_result

                yield details_span(code_result)
            send_result= "result length:" + str(len_str2list(code_result))+";result:"+short_response(code_result)
            print(send_result)
            # print("code_result: ",code_result)
            messages2.append({"role": "user",
                              "content": send_result})
            chat_response_code = (chat_single(messages2, ""))
            chat_result = ''
            for chunk in chat_response_code:
                if chunk.choices[0].delta.content is not None:
                    char = chunk.choices[0].delta.content
                    print(char, end="")
                    chat_result += char
                    yield char
            messages2.append({"role": "assistant",
                              "content": chat_result})

    return Response(stream_with_context(generate()))


@app.route('/stream', methods=['POST', 'GET'])
def stream():
    # 生成逐字输出的HTML

    # data = request.get_json().get('text')  # 获取JSON数据
    # print(data)  # 输出查看，实际应用中你可能会做其他处理
    def generate():
        full_text = ''
        for char in markdown_text:
            full_text += char
            yield char
            time.sleep(0.001)  # 减小这个值以提高响应速度
        if "```python" in full_text:
            yield "\n\n`Code running...`\n"

            code_str = extract_code(full_text)
            sys.stdout = output
            try:
                exec(code_str)
            except Exception as e:
                print(f"An error occurred: {e}")
            code_result = output.getvalue()
            output.truncate(0)
            sys.stdout = original_stdout
            # yield "\n`Code result: `\n"
            print(details_span(code_result))

            yield details_span(code_result)

    return Response(stream_with_context(generate()))


if __name__ == '__main__':
    app.run(debug=True)
