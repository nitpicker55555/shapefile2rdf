# -*- coding: utf-8 -*-
import asyncio
import json
import re
from shapely.geometry import Polygon
from geo_functions import *
from ask_functions import *
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

global_variables={}

# 示例的 Markdown 文本（包含图片链接）
# ![示例图片](/static/data.png "这是一个示例图片")
socketio =SocketIO(app,async_mode='threading')


search = DuckDuckGoSearchResults()


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

            return str(len(result))+"(String)"
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
@app.route('/debug_mode', methods=['POST'])
def debug_mode():
    data = request.get_json().get('message')  # 获取JSON数据
    if data=='debug':
        session['template']=True
    else:
        session['template'] = False

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




        os = user_agent.os.family
        browser = user_agent.browser.family
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
    session['history']=[]
    return render_template('index.html')


def polygons_to_geojson(polygons_dict):
    """
    将键值都为Polygon对象的字典转换为键值都为GeoJSON的字典。

    :param polygons_dict: 一个键值都为Polygon对象的字典。
    :return: 一个键值都为GeoJSON格式的字典。
    """
    geojson_dict = {}
    for key, polygon in polygons_dict.items():
        # 将每个Polygon对象转换为GeoJSON格式的字典
        geojson_dict[key] = mapping(polygon)
    return geojson_dict

def send_data(data,mode="data"):
    if mode=="map":
        data=polygons_to_geojson(data)

    socketio.emit('text', {mode:  data})

@app.route('/submit', methods=['POST', 'GET'])
def submit():
    # 加载包含 Markdown 容器的前端页面
    data = request.get_json().get('text')  # 获取JSON数据
    messages = request.get_json().get('messages')  # 获取JSON数据
    processed_response=[]





    def generate(data):
        compelete = False
        template = False
        steps = 0  # 纯文字返回最多两次
        whole_step = 0  # 总返回数,可以调整数值来限制未来的返回数
        true_step = 0  # 总返回数
        stop_step = False  # 强制该轮停止

        if "User upload a file in:" in data:
            chat_response = "File uploaded successfully! You can ask your questions."
            compelete = True

            yield chat_response
        else:
            if session.get('uploaded_indication') != None:
                messages[0]['content'] ='ttl_prompt'
                messages[0]['content'] += f"\nUser uploaded a ttl file in: .\\uploads\\{session['uploaded_indication']}"
            else:
                messages[0]['content'] = 'question_template'
                # data+=f".(用户上传的文件地址: .\\uploads\\{session['uploaded_indication']})"
            # session['messages2'].append({"role": "user",
            #                              "content": data})

        code_list=[]
        if session['template']==True:
            code_list.append(data)
        else:
            if judge_query_first(data)['judge']:
                code_list=judge_query(data)['code'].split("\n")
            else:

                bounding_box_indicate = judge_bounding_box(data)
                if bounding_box_indicate != None:
                    code_list.append(f"set_bounding_box('{bounding_box_indicate}')")
                    if bounding_box_indicate in data:
                        if f"in {bounding_box_indicate}" in data:
                            data_without_placename=data.replace(f'in {bounding_box_indicate}','')
                        else:
                            data_without_placename = data.replace(f'{bounding_box_indicate}', '')
                        data=data_without_placename

                object_subject = judge_object_subject(data)  # primary_subject,related_geographic_element
                yield f"\n\n`{object_subject}`\n"
                geo_relation_dict = judge_geo_relation(data)
                yield f"\n\ngeo_relation:`{geo_relation_dict}`\n"
                code_list.append("""
graph_dict={}
graph_type_list={}
type_dict={}
element_list={'primary_subject':None,'related_geographic_element':None}
                        """)
                if geo_relation_dict==None:                                                                     #没有地理关系

                    code_list.append(f"""
graph_dict['primary_subject'] = judge_type('{object_subject['primary_subject']}')["database"]
graph_type_list['primary_subject'] = ids_of_attribute(graph_dict['primary_subject'])
type_dict['primary_subject'] = pick_match('{object_subject['related_geographic_element']}', graph_type_list['primary_subject'])
                            """)
                    code_list.append(
                        f"element_list['primary_subject'] = ids_of_type(graph_dict['primary_subject'], type_dict['primary_subject'])")
                else:

                    code_list.append(f"geo_relation_dict={geo_relation_dict}")


                    # graph_dict={}
                    # graph_type_list={}
                    # type_dict={}
                    # element_list={}

                    for item_, value in object_subject.items():
                        if value != None:
                            code_list.append(f"""
graph_dict['{item_}']=judge_type('{value}')['database']
graph_type_list['{item_}']=ids_of_attribute(graph_dict['{item_}'])
type_dict['{item_}']=pick_match('{value}',graph_type_list['{item_}'])
                                        """)
                            code_list.append(
                                f"element_list['{item_}'] = ids_of_type(graph_dict['{item_}'], type_dict['{item_}'])")
                            # graph_dict[item_]=judge_type(object_subject[item_])['database']               #判断图名
                            # graph_type_list[item_]=ids_of_attribute(graph_dict[item_])                    #得到该图所有的属性
                            # type_dict[item_]=pick_match(object_subject[item_],graph_type_list[item_])     #从所有的属性中找到符合字段描述的，比如park
                            # element_list[item_] = ids_of_type(graph_dict[item_], type_dict[item_])        #拿到这些id

                    code_list.append("geo_result=geo_calculate(element_list['related_geographic_element'],element_list['primary_subject'],geo_relation_dict['type'],geo_relation_dict['num'])")



        lines_list = code_list
        for lines in lines_list:
            yield f"\n\n```python\n{lines}\n```"
            yield "\n\n`Code running...`\n"

            lines=[lines]
            if '=' in lines[-1] and (
                    'geo_calculate' in lines[-1] or 'ids_of_type' in lines[-1] or 'set_bounding_box' in lines[
                -1] or 'area_calculate' in lines[-1]):
                variable_str = lines[-1].split('=')[0]
                new_line = f"""
send_data({variable_str}['geo_map'],'map')
            """
                lines.append(new_line)
            elif '=' not in lines[-1] and (
                    'geo_calculate' in lines[-1] or 'ids_of_type' in lines[-1] or 'set_bounding_box' in lines[
                -1] or 'area_calculate' in lines[-1]):

                new_line = f"""
temp_result={lines[-1]}
send_data(temp_result['geo_map'],'map')
            """
                lines[-1] = new_line


            code_str = '\n'.join(lines)

            print(code_str)
            sys.stdout = output
            start_time = time.time()  # 记录函数开始时间

            try:

                exec(code_str, globals())
            except Exception as e:
                print(f"An error occurred: {repr(e)}")
            end_time = time.time()  # 记录函数结束时间
            run_time = end_time - start_time
            code_result = str(output.getvalue().replace('\00', ''))
            output.truncate(0)
            sys.stdout = original_stdout
            code_result = str(code_result)
            yield details_span(code_result, run_time)



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
        url = f"http://ip-api.com/json/{ip}"
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



if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True,host='0.0.0.0',port=9090)