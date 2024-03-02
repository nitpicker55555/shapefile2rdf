# -*- coding: utf-8 -*-
import asyncio
import json
import re
from geo_functions import *
from flask import Flask, Response, stream_with_context, request, render_template, jsonify,session
from werkzeug.utils import secure_filename
import time
from openai import OpenAI
import os
from dotenv import load_dotenv
import ast
from langchain_community.tools import DuckDuckGoSearchResults
from user_agents import parse
import requests
# import logging
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()
import sys
from io import StringIO
from datetime import datetime
from flask_socketio import SocketIO, emit
from repair_data import repair,crs_transfer
from shape2ttf import shapefile_to_ttl
output = StringIO()
original_stdout = sys.stdout
app = Flask(__name__)
# app.logger.setLevel(logging.WARNING)
app.secret_key = 'secret_key' # 用于启用 flash() 方法发送消息



# 示例的 Markdown 文本（包含图片链接）
# ![示例图片](/static/data.png "这是一个示例图片")
socketio =SocketIO(app,async_mode='threading')


search = DuckDuckGoSearchResults()
template_answer={
    "12":["""
```python
set_bounding_box("munich maxvorstadt")
```
    """,
          """
```python
id1=ids_of_type("http://example.com/landuse","forest")
```
              """
          ,
          """
```python
id2=ids_of_type("http://example.com/buildings",'building')
```
              """
          ,
          """
```python
geo_calculate(id1,id2,'buffer',100)
```
              """
          ],'13':[r"""
```python
subject_dict,predicate_dict=ttl_read(r'.\uploads\modified_Moore_Bayern_4326.ttl')
search_attribute(subject_dict,'http://example.org/property/uebk25_k','80')
```
          ""","""
          
          """]
}

markdown_text = """
asdasdafsdfsdfsafasfasf
```python
```
"""

# normal_prompt = r"""
# You have a virtual environment equipped with a python environment. The python code you
# give will be automatically run by the system, so you can freely achieve your goals through python
# code. The code running results will be returned to you after the execution is completed. You can use
# python code to view all information about the current environment, or use matplotlib to draw charts.
# But note that if you want to get the value of a variable, please use print() to print it out; the
# variables in the code you give will be stored in the environment and can be called directly next
# time.
#
# Process upload file:
# User can upload file in location: .\uploads\
# You can use python code to read and process it.
#
# Finish tag:
# When you think no further reply needed, please add ```status_complete``` at the end of response, if you think further
# response is needed, please add ```status_running``` at the end of response.
#
# Writing Python:
# If you want to get the value of a variable, please use print() to print it out.
# """
normal_prompt = r"""You have a virtual environment equipped with a python environment and internet.
You can use python code to process user upload files, or use matplotlib to draw charts, and use 'search_internet("news")' to access 
internet. The variables in the code you give will be stored in the environment and can be called directly next time. 

Please notice: If you want to write code, please write with markdown format. If user wants to search news or 
informations in internet, use python code: 'search_internet('what you want to search')' to get relevant information, 
do not use other python code. 

Access internet: You can access internet to search information by calling function search_internet("news"), Example: you 
can write python code '```python\nsearch_internet("西安新闻")\n```' to get news in 西安. Write '```python\nsearch_internet("Germany news")\n```' to get news in germany."""

judge_prompt="""You are a task completion judge. I will tell you the goal and current completion status of this task. 
You need to output whether it is completed now in json format. If it is completed, output {"complete":true}. If not, 
output {"complete":false} """
question_template="""
You are an AI assistant that processes database queries. You have a virtual environment 
equipped with python. Environment has a graph database consists of three graphs:['http://example.com/landuse', 'http://example.com/soil', 
'http://example.com/buildings']

The following functions are provided for database action: 

region=set_bounding_box(address=None) #Set bounding box for a specific region
types=types_of_graph(graph) #Get types of specific graph
ids=ids_of_type(graph,type,region=None) #Get ids of specific graph
geo_calculate(id_list_1=[],id_list_2=[],geo_relation,buffer_number=0) #Get ids with specific geo relation

geo_relation={
        "contains": "return which id in id_list_2 geographically contains which id in id_list_1",
        "intersects": "return which id in id_list_2 geographically intersects which id in id_list_1",
        "buffer": "return which id in id_list_2 geographically intersects the buffer of which id in id_list_1, if you want to 
        call buffer, you need to specify the last argument "buffer_number" as a number"

Example1:
User: I want to know which building in 100m around the forest in munich ismaning.
You:
Ok, let me find out.
```python
region=set_bounding_box('munich ismaning')
id1=ids_of_type('http://example.com/landuse','forest',region)
id2=ids_of_type('http://example.com/buildings','building',region)
geo_calculate(id1,id2,'buffer',100)
```
Example2:
User: I want to know which land is suitable for agriculture.
You:
```python
region=set_bounding_box(None)
types=types_of_graph('http://example.com/soil')
types
```
Based on semantic meaning of these types, I think 61a,65c is good for agriculture.
```python
id1=ids_of_type('http://example.com/soil',['65c','61a'],region)
```
Example3:
User: Please draw ids in map
You:
```python
draw_geo_map(id1, "geo")
```
}
"""

ttl_prompt=r"""
You can read .ttl file by calling flowing functions.
subject_dict,predicate_list=ttl_read(path)
search_attribute(subject_dict,predicate,predicate_value)
Example1:
User: I want know which predicate the ttl file has.
You:
```python
subject_dict,predicate_dict=ttl_read(r'\path\.ttl')
predicate_dict.keys()
```
Example3:
User: I want to know the value of predicate 'predicate'.
You:
```python
predicate_dict['predicate']
```
Example2:
User: I want to know the subject which has value 'a','b' of predicate 'predicate':
You:
```python
search_attribute(subject_dict,'predicate',['a','b'])
```
"""
geo_prompt = """You are an AI assistant that processes complex database queries. You have a virtual environment 
equipped with python. The following functions are provided for database action: 

{

    "set_bounding_box": { "Argument": ["region_name"], "Description": "If user wants to get query result from a 
    specific location, you need to first run this function with argument region_name, then the other function would 
    limit its result in this region automatically (you don't need to add region name to other function). Example: if 
    user wants to search result from munich germany, input of this function would be ['munich germany']." 
    }, 
    "types_of_graph": { "Argument": ["graph_name"], "Description": "Enter the name of the graph you want to 
    query and it returns all types of that graph. For example, the types of landuse are park, forest, etc." 
    }, 
    "ids_of_type": { "Arguments": ["graph_name", "type_name"], "Description": "Enter the graph name and type 
    name you want to query, and it returns the corresponding element IDs. If you want to get id_list from multi types 
    at the same time, you can input arg type_name as a list.","Example":" 

        If user wants to search soil that suitable for agriculture, first you need to call function 
        types_of_graph to get types in soil graph: soil_types=types_of_graph("http://example.com/soil"). 
        Then input type list you think is good for agriculture, for example ['62c','64c','66b','80b'].
        Next, use function ids_of_type to get its id_list soil_ids=ids_of_type( "http://example.com/soil",['62c','64c','66b']) 
        "
    },

        "geo_calculate": {
        "Arguments": [id_list_1, id_list_2,"function name",buffer_number=0],
        "Description": "
        geo_calculate function has functions: contains, intersects, buffer. 
        Input should be two id_list which generated by function ids_of_type and geo_calculate function name you want to use. 

        function contains: return which id in id_list_2 geographically contains which id in id_list_1; function 
        intersects: return which id in id_list_2 geographically intersects which id in id_list_1; function buffer: 
        return which id in id_list_2 geographically intersects the buffer of which id in id_list_1, if you want to 
        call buffer, you need to specify the last argument "buffer_number" as a number. "Example": If user wants to 
        search buildings in farmland, first you need to figure out farmland and buildings in which graph using 
        function types_of_graph, then generate id_list for buildings and farmland using function 
        ids_of_type, id_list1=ids_of_type("http://example.com/buildings","building")
        id_list2=ids_of_type("http://example.com/landuse","farmland"), 
        finally call function geo_calculate: contains_list=geo_calculate(id_list_1,id_list_2,"contains")
        "
    }
}

Database: The database has three graphs: ['http://example.com/landuse', 'http://example.com/soil', 
'http://example.com/buildings']; The soil graph contains many soil types. If a user asks you which soil types are 
suitable for agriculture, you need to make a semantic judgment based on the names of the types. 
"""

def chat_single(messages, mode="json"):
    if mode == "json":

        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            response_format={"type": "json_object"},
            messages=messages,
            stream=True,
        max_tokens = 4096
        )
        return response
        # return response.choices[0].message.content
    else:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            stream=True,
            messages=messages,
        max_tokens=4096
        )
        return response
def search_internet(news):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def async_task():
        # 你的异步代码
        print(search.run(news))

    loop.run_until_complete(async_task())
    loop.close()
# async def async_task(news):
#     # 你的异步代码
#     print(search.run(news))
#
# def search_internet(news):
#     # 使用 eventlet 来 "模拟" 异步操作
#     pool = eventlet.GreenPool()
#     pool.spawn(async_task,news)
#     pool.waitall()
def complete_json(input_stream):
    """
    尝试补全一个不完整的JSON字符串，包括双引号和括号。

    参数:
    - input_stream: 一个可能不完整的JSON字符串

    返回:
    - 完整的JSON对象
    """
    brackets = {'{': '}', '[': ']'}
    quotes = {'"': '"'}
    stack = []
    in_string = False

    # 尝试解析JSON，如果失败则补全
    try:
        return json.loads(input_stream)
    except json.JSONDecodeError:
        pass  # 继续到补全逻辑

    # 逐字符遍历输入字符串
    for char in input_stream:
        if char in quotes and not in_string:
            # 进入字符串
            in_string = True
            stack.append(quotes[char])
        elif char in quotes and in_string:
            # 结束字符串
            in_string = False
            stack.pop()
        elif char in brackets and not in_string:
            # 进入对象或数组
            stack.append(brackets[char])
        elif stack and char == stack[-1] and not in_string:
            # 退出对象或数组
            stack.pop()

    # 补全字符串
    if in_string:
        input_stream += '"'
        stack.pop()

    # 根据栈中剩余的括号补全JSON
    while stack:
        input_stream += stack.pop()

    # 再次尝试解析补全后的JSON
    return json.loads(input_stream)




# html_content = markdown2.markdown(markdown_text)

def extract_code(code_str):
    return code_str.split("```python")[1].split("```")[0]
def len_str2list(result):
    # result=result.replace("None","").replace(" ","")
    try:
        # 尝试使用 ast.literal_eval 解析字符串
        result = ast.literal_eval(result)
        # 检查解析结果是否为列表
        if not isinstance(result,int):
            return len(result)
        else:
            return result
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
def details_span(result,run_time):

    aa=f"""
<details>
    <summary>`Code result: Length:{len_str2list(str(result))},Run_time:{round(run_time,2)}s`</summary>
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
# 设置文件上传的目录和大小限制
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg','doc','docx','xlsx','csv','ttl'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        session['uploaded_indication'] = filename
        return jsonify({"filename": filename}), 200
    else:
        return jsonify({"error": "File type not allowed"}), 400
@app.route('/submit_email', methods=['POST'])
def submit_email():
    data=request.get_json().get('text')
    with open("./static/email.text",'a',encoding='utf-8') as file:
        file.write('\n'+json.dumps({"email":data,"time":str(datetime.now()),"ip":session['ip_'],"os":session['os'],"device":session['device_type'],'browser':session['browser']}))
    return jsonify({"text": True}), 400

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "The file is too large. Maximum file size is 50MB."}), 413

@app.route('/')
def home():
    # 加载包含 Markdown 容器的前端页面
    # session['globals_dict'] ={}
    # session['locals_dict'] = locals()
    print("初始化")
    ip_=request.headers.get('X-Real-IP')
    session['ip_']=ip_
    session['uploaded_indication'] = None
    # if 'messages2' not in session:
    #     session['messages2'] = []
    #     session['messages2'].append({"role": "system",
    #                                  "content": normal_prompt
    #                                  })
    user_agent_string = request.headers.get('User-Agent')
    if user_agent_string:
        user_agent = parse(user_agent_string)




        # 获取操作系统和浏览器信息
        os = user_agent.os.family  # 操作系统
        browser = user_agent.browser.family  # 浏览器
        if user_agent.is_mobile:
            device_type = 'Mobile'
        elif user_agent.is_tablet:
            device_type = 'Tablet'
        elif user_agent.is_pc:
            device_type = 'Desktop'
        else:
            device_type = 'Unknown'
        session['os']=os
        session['browser']=browser
        session['device_type']=device_type
    else:
        session['os']=None
        session['browser']=None
        session['device_type']=None
    session['template']=True
    return render_template('index.html')

def send_data(data,mode="data"):
    # 假设这个函数在某些事件发生时被触发，并向所有客户端发送信息
    # template_poly={
    #     'Label3': 'POLYGON((10 10, 11 10, 11 11, 10 11, 10 10))',
    #     'Label4': 'POLYGON((12 12, 13 12, 13 13, 12 13, 12 12))'
    # }
    # print(data)
    socketio.emit('text', {mode:  data})

@app.route('/submit', methods=['POST', 'GET'])
def submit():
    # 加载包含 Markdown 容器的前端页面
    data = request.get_json().get('text')  # 获取JSON数据
    messages = request.get_json().get('messages')  # 获取JSON数据
    processed_response=[]
    print(len(messages))



    def generate(data):
        compelete = False
        template = False
        steps = 0  # 纯文字返回最多两次
        whole_step = 0  # 总返回数,可以调整数值来限制未来的返回数
        true_step = 0  # 总返回数
        stop_step = False  # 强制该轮停止

        if "User upload a file in:" in data:
            chat_response = "文件上传完成！告诉我你想做什么？"
            compelete = True

            yield chat_response
        else:
            if session.get('uploaded_indication') != None:
                messages[0]['content'] =ttl_prompt
                messages[0]['content'] += f"\nUser uploaded a ttl file in: .\\uploads\\{session['uploaded_indication']}"
            else:
                messages[0]['content'] = question_template
                # data+=f".(用户上传的文件地址: .\\uploads\\{session['uploaded_indication']})"
            # session['messages2'].append({"role": "user",
            #                              "content": data})
        print(messages[0]['content'])
        while compelete!=True and steps<2 and whole_step<=5 and stop_step!=True:
                # print(messages)
                # print(whole_step,"whole_step")
                whole_step+=1
                true_step+=1
                # chat_response = str(datetime.now())+"   "+str(len(messages)) #test

                if data in template_answer:
                    session['template']=True
                    chat_response = template_answer[data]
                    template=True
                    # stop_step=True
                    # time.sleep(2)
                elif session['template']:
                    chat_response="```python\n"+data+"\n```"
                    stop_step = True
                else:

                    chat_response = (chat_single(messages, ""))
                content_str=''
                chat_result = ''
                chunk_num=0
                if template:
                    # print(true_step,len(chat_response))

                    for chunk in chat_response[true_step-1]:
                        if chunk_num == 0:
                            char = "\n" + chunk
                            # char = "\n"+chunk #test
                        else:
                            char = chunk
                            # char =  chunk #test
                        chunk_num += 1
                        chat_result += char
                        time.sleep(0.001)
                        if true_step==len(chat_response):
                            stop_step=True

                        yield char
                elif session['template']:
                    chat_result=chat_response
                    yield chat_response
                else:
                    for chunk in chat_response:
                    # if chunk is not None:
                        if chunk.choices[0].delta.content is not None:
                            if chunk_num==0:
                                char = "\n"+chunk.choices[0].delta.content
                                # char = "\n"+chunk #test
                            else:
                                char =  chunk.choices[0].delta.content
                                # char =  chunk #test
                            chunk_num+=1

                            print(char, end="")
                            chat_result += char

                            yield char
                        # try:
                        #     json_str = complete_json(chat_result)
                        #     new_content = json_str['content']
                        #     if new_content != content_str:
                        #         char_content = new_content[len(content_str):]
                        #         content_str = new_content
                        #         print(char_content, end="")
                        #
                        #         yield char_content
                        # except:
                        #     pass
                full_result=(chat_result)
                processed_response.append({'role':'assistant','content':chat_result})
                messages.append({'role':'assistant','content':chat_result})

                compelete=False
                print("complete: ",compelete)

                if "```python" in full_result and ".env" not in full_result and "pip install" not in full_result:
                    yield "\n\n`Code running...`\n"

                    # code_str = re.sub(r'(?<!\\)\\n', r'\\\\n', extract_code(full_result['content']))
                    code_str = extract_code(full_result)
                    print(code_str, "code_original")
                    plt_show = False
                    if "plt.show()" in code_str:
                        plt_show = True
                        print("plt_show")
                        filename = f"plot_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                        code_str = code_str.replace("import matplotlib.pyplot as plt",
                                                    "import matplotlib.pyplot as plt\nfrom matplotlib.font_manager import FontProperties\nfont = FontProperties(fname=r'static\msyh.ttc')\n")
                        code_str = code_str.replace("plt.show()", f"plt.savefig('static/{filename}')")

                        print(code_str)
                    else:
                        lines = code_str.strip().split('\n')

                        # last_line = [line for line in lines if '=' in line][-1]
                        if "print" not in lines[-1] and "=" not in lines[-1] and "#" not in lines[-1] and "search_internet" not in lines[-1]:
                            if "geo_calculate" in lines[-1] or "search_attribute" in lines[-1] or 'ids_of_type' in lines[-1]:
                                new_last_line=f"""
send_data({lines[-1]},'map')
"""

                            else:

                                new_last_line = f"""
try:
        print({lines[-1]})
except:
        pass
                            """
                            lines[-1] = new_last_line

                            # 将所有行重新连接成一个新的字符串
                            code_str = '\n'.join(lines)
                        # var_name = last_line.split('=')[0].strip()
                    print(code_str,"code after processed")
                    sys.stdout = output
                    start_time = time.time()  # 记录函数开始时间
                    try:

                        exec(code_str, globals())

                    except Exception as e:
                        print(f"An error occurred: {repr(e)}")
                    end_time = time.time()  # 记录函数结束时间
                    run_time = end_time - start_time
                    code_result =str( output.getvalue().replace('\00', ''))
                    output.truncate(0)
                    sys.stdout = original_stdout

                    if plt_show and "An error occurred: " not in code_result:
                        code_result = f'![matplotlib_diagram](/static/{filename} "matplotlib_diagram")'
                        whole_step=5 #确保图返回结果只会被描述一次
                        yield code_result


                    else:
                        code_result=str(code_result)

                        yield details_span(code_result,run_time)

                    send_result= "code_result:"+short_response(code_result)
                    print(send_result)
                    messages.append({"role": "user",
                                  "content": send_result})
                    processed_response.append({'role':'user','content':send_result})
                    compelete=False
                    final_conv=send_result

                else:
                    steps += 1
                    if steps<2 and whole_step<5:
                        messages.append({"role": "user",
                                          "content": "ok"})
                        processed_response.append({"role": "user",
                                          "content": "ok"})
                        final_conv='好'

        send_data(processed_response)
        data_with_response = {
            'len': str(len(messages)),
            'time': str(datetime.now()),
            'ip': str(session['ip_']),
            'location': query_ip_location(session['ip_']),
            'user': str(data),
            'os': str(session['os']),
            'browser': str(session['browser']),
            'device': str(session['device_type']),
            'answer': str(processed_response)
            # 'answer': response_str
        }


        formatted_data = json.dumps(data_with_response, indent=2, ensure_ascii=False)

        # 写入文本文件
        with open('static/data3.txt', 'a', encoding='utf-8') as file:
            file.write(formatted_data)
    return Response(stream_with_context(generate(data)))


def query_ip_location(ip):
    try:
        ip = ip.replace(" ", "")
        url = f"http://ip-api.com/json/{ip}"  # 使用ip-api.com提供的API
        response = requests.get(url)
        data = json.loads(response.text)

        if data["status"] == "success":
            country = data["country"]
            city = data["city"]
            region = data["regionName"]
            isp = data["isp"]
            res = str(region + "  " + city + "  " + isp)
            return res
        else:
            return ip
    except:
        return ip

@app.route('/stream', methods=['POST', 'GET'])
def stream():
    # 生成逐字输出的HTML

    # data = request.get_json().get('text')  # 获取JSON数据
    # print(data)  # 输出查看，实际应用中你可能会做其他处理
    def generate():
        full_text = ''
        content_str = ""
        code_indicator=False
        for char in markdown_text:

            full_text += char
            yield char
            print(char,end="")
            time.sleep(0.001)
        # yield "\n```\n"
        # json_response=json.loads(full_text)
        # yield f"\n`{str(json_response['complete'])}`\n"
        # yield "json_response['complete']"
        if "```python" in full_text:
            yield "\n\n`Code running...`\n"

            # code_str = re.sub(r'(?<!\\)\\n', r'\\\\n', extract_code(json_response['content']))
            code_str = extract_code(full_text)
            print(code_str,"code")
            plt_show = False
            if "plt.show()" in code_str:
                plt_show = True
                print("plt_show")

                filename = f"plot_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                code_str=code_str.replace("import matplotlib.pyplot as plt","import matplotlib.pyplot as plt\nfrom matplotlib.font_manager import FontProperties\nfont = FontProperties(fname=r'static\msyh.ttc')\n")
                code_str = code_str.replace("plt.show()", f"plt.savefig('static/{filename}')")

            # elif "search.run" in code_str:
            #     code_str="search = DuckDuckGoSearchResults()\n"+code_str
            else:
                lines = code_str.strip().split('\n')
                # last_line = [line for line in lines if '=' in line][-1]
                if "print" not in lines[-1] and "=" not in lines[-1] and "#" not in lines[-1]:
                    # if "search.run" in code_str:
                    #     code_str=code_str.replace("search.run","print(search.run")+")"
                    # else:
                    code_str += f"""
try:
                   print({lines[-1]})
except:
                   pass
                                        """
                # var_name = last_line.split('=')[0].strip()
            print(code_str,"code_after_process")
            sys.stdout = output
            try:
                exec(code_str, globals())
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                print(f"An error occurred: {repr(e)}")
            code_result = output.getvalue().replace('\00', '')
            output.truncate(0)
            sys.stdout = original_stdout

            if plt_show and "An error occurred: " not in code_result:
                code_result = f'![matplotlib_diagram](/static/{filename} "matplotlib_diagram")'
                yield code_result
            else:
                code_result = code_result

                yield details_span(code_result)

    return Response(stream_with_context(generate()))


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)