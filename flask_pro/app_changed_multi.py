# -*- coding: utf-8 -*-
import asyncio
import json
import re
import traceback

from shapely.geometry import Polygon
from geo_functions import *
from ask_functions_multi import *
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
# from repair_data import repair,crs_transfer
# from shape2ttf import shapefile_to_ttl
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
    if result==None:
        return 0
    # result=result.replace("None","").replace(" ","")
    try:
        # 尝试使用 ast.literal_eval 解析字符串
        result = ast.literal_eval(result)
        # 检查解析结果是否为列表
        if result!=None:
            if not isinstance(result,int):
                return len(result)
            else:
                return result
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
    if result==None:
        result="None"
    pattern = r"An error occurred:.*\)"
    match = re.search(pattern, result)

    if match:
        error_message = match.group(0)
        aa=error_message
        return {'error':result+" \n "+aa}
    else:
        length=len_str2list(str(result))
        attention=''
        if 'String' not in str(length) and int(length)>10000:
            attention='Due to the large volume of data, visualization may take longer.'
            if int(length)==20000:
                attention='Due to the large volume of data in your current search area, only 20,000 entries are displayed.'
        aa = f"""
<details>
    <summary>`Code result: Length:{length},Run_time:{round(run_time, 2)}s`</summary>
       {str(result)}
</details>
{attention}


            """


        return {'normal':aa}
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
    return jsonify({"text": True}), 400
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
    globals_dict = {}
    global_id_attribute = {}
    global_id_geo = {}
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
    session['template']=False
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

        # if "User upload a file in:" in data:
        #     chat_response = "File uploaded successfully! You can ask your questions."
        #     compelete = True
        #
        #     yield chat_response
        # else:
        #     if session.get('uploaded_indication') != None:
        #         messages[0]['content'] ='ttl_prompt'
        #         messages[0]['content'] += f"\nUser uploaded a ttl file in: .\\uploads\\{session['uploaded_indication']}"
        #     else:
        #         messages[0]['content'] = 'question_template'
                # data+=f".(用户上传的文件地址: .\\uploads\\{session['uploaded_indication']})"
            # session['messages2'].append({"role": "user",
            #                              "content": data})

        code_list=[]
        if session['template']==True:
            code_list.append(data)
        else:
            data=data.lower()
            # if data.startswith('next'):




            bounding_box_indicate,data_without_placename = judge_bounding_box(data)
            print( bounding_box_indicate,data_without_placename)
            if bounding_box_indicate != None:
                code_list.append(f"set_bounding_box('{bounding_box_indicate}')")
                data=data_without_placename

            # code_list.append(f"set_bounding_box('munich')")


            """
            {
              "query": "Identify residential buildings within 50 meters of parks with playgrounds on sandy soil under them?",
              "entities": [
                {
                  "entity_text": "buildings",
                  "non_spatial_modify_statement": "residential"
                },
                {
                  "entity_text": "parks",
                  "non_spatial_modify_statement": "with playgrounds"
                },
                {
                  "entity_text": "soil",
                  "non_spatial_modify_statement": "sandy"
                }
              ],
              "spatial_relations": [
                {
                  "type": "within 50 meters of",
                  "head": 0,
                  "tail": 1
                },
                {
                  "type": "under",
                  "head": 2,
                  "tail": 0
                }
              ]
            }
            """

            # multi_result = {'entities': [{'entity_text': 'farmlands', 'non_spatial_modify_statement': None}, {'entity_text': 'soil', 'non_spatial_modify_statement': 'unsuitable for agriculture'}], 'spatial_relations': [{'type': 'on', 'head': 0, 'tail': 1}]}
            multi_result = judge_object_subject_multi(data)
            code_list.append(
                f"""
multi_result={multi_result}                
                """
            )
            code_block="""
all_geo_id={}
            """
            for num, entity in enumerate(multi_result['entities']):

                code_block+=(f"""
graph{num} = judge_type(multi_result['entities'][{num}])["database"]
graph_type_list = ids_of_attribute(graph{num})
type{num} = pick_match(multi_result['entities'][{num}], graph_type_list, graph{num})
                """)
            code_list.append(code_block)
            for num, entity in enumerate(multi_result['entities']):
                code_list.append(f"""
id_list{num}=ids_of_type(graph{num},type{num})

                            """)
            if len(multi_result['spatial_relations'])!=0:
                for num, relations in enumerate(multi_result['spatial_relations']):
                    code_list.append(f"""
geo_relation{num}=judge_geo_relation(multi_result['spatial_relations'][{num}]['type'])
geo_result{num}=geo_calculate(id_list{relations['head']},id_list{relations['tail']},geo_relation{num}['type'],geo_relation{num}['num'])
                                """)
                    code_list.append(f"""
id_list{relations['head']}=geo_result{num}['subject']
id_list{relations['tail']}=geo_result{num}['object']
                    """)
            else:                                                                                           #no geo_relationship, show all entities
                pass
#                 if not judge_area(data):
#                     code_list.append(
#                     """
# send_data(all_geo_id,'map')
#                     """
#                 )


        lines_list = code_list

        for line_num,lines in enumerate(lines_list):
            yield f"\n\n```python\n{lines}\n```"
            yield "\n\n`Code running...`\n"
            lines=lines.split('\n')
            # lines=[lines]
            # print(lines)
            filtered_lst = [item for item in lines if item.strip()]
            for i in filtered_lst:
                print('----',i)
            lines=filtered_lst

            if '=' in lines[-1] and (
                    'geo_calculate' in lines[-1] or 'ids_of_type' in lines[-1] or 'set_bounding_box' in lines[
                -1]):

                variable_str = lines[-1].split('=')[0]
                explain_row=''
                if 'set_bounding_box' not in lines[-1] and line_num==(len(lines_list)-1) :
                    explain_row=f"""
explain=id_explain({variable_str})
print(judge_result(explain))
"""
                new_line = f"""
send_data({variable_str}['geo_map'],'map')

            """
                lines.append(new_line)
            elif '=' not in lines[-1] and (
                    'geo_calculate' in lines[-1] or 'ids_of_type' in lines[-1] or 'set_bounding_box' in lines[
                -1]):
                explain_row = ''
                if 'set_bounding_box' not in lines[-1]  and line_num==(len(lines_list)-1):
                    explain_row = f"""
explain=id_explain(temp_result)
print(judge_result(explain))    
                """
                new_line = f"""
temp_result={lines[-1]}
send_data(temp_result['geo_map'],'map')

            """
                lines[-1] = new_line
            elif '=' not in lines[-1] and 'send_data' not in lines[-1]:
                new_line = f"""
print({lines[-1]})
                            """
                lines[-1] = new_line



            code_str = '\n'.join(lines)

            # print(code_str)
            sys.stdout = output
            start_time = time.time()  # 记录函数开始时间

            try:

                exec(code_str, globals())

            except Exception as e:
                exc_info = traceback.format_exc()
                # 打印错误信息和代码行
                print(f"An error occurred: {repr(e)}\n{exc_info}")
            end_time = time.time()  # 记录函数结束时间
            run_time = end_time - start_time
            code_result = str(output.getvalue().replace('\00', ''))
            output.truncate(0)
            sys.stdout = original_stdout
            code_result = str(code_result)
            show_template=details_span(code_result, run_time)
            yield list(show_template.values())[0]
            if 'error' in show_template:
                break




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