# -*- coding: utf-8 -*-
import asyncio
import json
import re
import traceback

from shapely.geometry import Polygon

import geo_functions
from geo_functions import *
from ask_functions_agent import *
from flask import Flask, Response, stream_with_context, request, render_template, jsonify, session
from werkzeug.utils import secure_filename
import time
from openai import OpenAI
import os
from dotenv import load_dotenv
import ast
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
app.secret_key = 'secret_key'  # 用于启用 flash() 方法发送消息

global_variables = {}

# 示例的 Markdown 文本（包含图片链接）
# ![示例图片](/static/data.png "这是一个示例图片")
socketio = SocketIO(app, async_mode='threading')


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
def reorder_relations(relations):
    for relation in relations:
        if 0 not in (relation['head'], relation['tail']):
            break
    else:
        # 0 simultaneously exists in all dictionaries
        return relations

    reordered_relations = []
    zero_relation = None
    for relation in relations:
        if 0 in (relation['head'], relation['tail']):
            zero_relation = relation
        else:
            reordered_relations.append(relation)

    if zero_relation:
        reordered_relations.append(zero_relation)

    return reordered_relations


def extract_code_blocks(code_str):
    code_blocks = []
    parts = code_str.split("```python")
    for part in parts[1:]:  # 跳过第一个部分，因为它在第一个代码块之前
        code_block = part.split("```")[0]
        code_blocks.append(code_block)
    return code_blocks


def len_str2list(result):
    if result == None:
        return 0
    # result=result.replace("None","").replace(" ","")
    try:
        # 尝试使用 ast.literal_eval 解析字符串
        result = ast.literal_eval(result)
        # 检查解析结果是否为列表
        if result != None:
            if not isinstance(result, int):
                return len(result)
            else:
                return result
        else:
            return result
    except (ValueError, SyntaxError):
        # 如果解析时发生错误，说明字符串不是有效的列表字符串
        try:
            dict_result = json.loads(result)
            return len(dict_result)
        except:

            return str(len(result)) + "(String)"


def judge_list(result):
    try:
        # 尝试使用 ast.literal_eval 解析字符串
        result = ast.literal_eval(result)
        # 检查解析结果是否为列表
        return True
    except (ValueError, SyntaxError):
        # 如果解析时发生错误，说明字符串不是有效的列表字符串
        return False


def details_span(result, run_time):
    if result == None:
        result = "None"
    pattern = r"An error occurred:.*\)"
    match = re.search(pattern, result)

    if match:
        error_message = match.group(0)
        aa = error_message
        return {'error': result + " \n " + aa}
    else:
        length = len_str2list(str(result))
        attention = ''
        if 'String' not in str(length) and int(length) > 10000:
            attention = 'Due to the large volume of data, visualization may take longer.'
            if int(length) == 20000:
                attention = 'Due to the large volume of data in your current search area, only 20,000 entries are displayed.'
        aa = f"""
<details>
    <summary>`Code result: Length:{length},Run_time:{round(run_time, 2)}s`</summary>
       {str(result)}
</details>
{attention}


            """

        return {'normal': aa}


def short_response(text_list):
    if len(str(text_list)) > 1000 and judge_list(text_list):
        if len_str2list(text_list) < 40:
            result = ast.literal_eval(text_list)
            short_suitable_types = [t[:35] for t in result]
            return str(short_suitable_types)
        else:
            return text_list[:1000]
    else:
        return text_list[:1000]


# 设置文件上传的目录和大小限制
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xlsx', 'csv', 'ttl'}
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
    if data == 'debug':
        session['template'] = True
    else:
        session['template'] = False
    return jsonify({"text": True}), 400


@app.route('/submit_email', methods=['POST'])
def submit_email():
    data = request.get_json().get('text')
    with open("./static/email.text", 'a', encoding='utf-8') as file:
        file.write('\n' + json.dumps(
            {"email": data, "time": str(datetime.now()), "ip": session['ip_'], "os": session['os'],
             "device": session['device_type'], 'browser': session['browser']}))
    return jsonify({"text": True}), 400


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "The file is too large. Maximum file size is 50MB."}), 413


@app.route('/')
def home():
    # 加载包含 Markdown 容器的前端页面
    # session['globals_dict'] ={}
    # session['locals_dict'] = locals()
    print("initial")
    geo_functions.globals_dict = {}
    geo_functions.global_id_attribute = {}
    geo_functions.global_id_geo = {}
    # globals_dict = {}
    # global_id_attribute = {}
    # global_id_geo = {}
    ip_ = request.headers.get('X-Real-IP')
    session['ip_'] = ip_
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
        session['os'] = os
        session['browser'] = browser
        session['device_type'] = device_type
    else:
        session['os'] = None
        session['browser'] = None
        session['device_type'] = None
    session['template'] = False
    session['history'] = []
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


def send_data(data, mode="data"):
    if mode == "map":
        data = polygons_to_geojson(data)

    socketio.emit('text', {mode: data})


@app.route('/submit', methods=['POST', 'GET'])
def submit():
    # 加载包含 Markdown 容器的前端页面
    data = request.get_json().get('text')  # 获取JSON数据
    messages = request.get_json().get('messages')  # 获取JSON数据
    new_message = request.get_json().get('new_message')  # 获取JSON数据
    processed_response = []

    def generate(data):
        compelete = False
        template = False
        steps = 0  # 纯文字返回最多两次
        whole_step = 0  # 总返回数,可以调整数值来限制未来的返回数
        true_step = 0  # 总返回数
        stop_step = False  # 强制该轮停止

        while compelete != True and steps < 3 and whole_step <= 5 and stop_step != True:
            # print(messages)
            print(whole_step, "whole_step")
            whole_step += 1
            true_step += 1
            # chat_response = str(datetime.now())+"   "+str(len(messages)) #test

            code_list = []
            #
            if session['template'] == True:
                code_list.append(data)
                compelete=True
            else:
                bounding_box, new_message = judge_bounding_box(data)
                if bounding_box:
                    code_list.append(f"set_bounding_box('{bounding_box}')")
                    messages.append(message_template('user', new_message))
                else:
                    messages.append(message_template('user', data))

                print(messages)

                chat_response = (chat_single(messages, "stream", 'gpt-4o-2024-05-13'))
                content_str = ''
                chat_result = ''
                chunk_num = 0

                for chunk in chat_response:
                    if chunk is not None:
                        # if chunk['message']['content'] is not None:
                        if chunk_num == 0:
                            char = "\n" + chunk.choices[0].delta.content

                        else:
                            char = chunk.choices[0].delta.content

                        chunk_num += 1

                        print(char, end="", flush=True)
                        if chunk.choices[0].delta.content is not None:
                            chat_result += char

                            yield char

                full_result = (chat_result)
                processed_response.append({'role': 'assistant', 'content': chat_result})
                messages.append({'role': 'assistant', 'content': chat_result})

                compelete = False
                # print("complete: ", compelete)

                if "```python" in full_result and ".env" not in full_result and "pip install" not in full_result:

                    code_list .extend( extract_code_blocks(full_result))
                    compelete=True
                else:
                    steps += 1
                    if steps < 2 and whole_step < 5:
                        messages.append({"role": "user",
                                         "content": "ok"})
                        processed_response.append({"role": "user",
                                                   "content": "ok"})
                        final_conv = 'ok'
            print(code_list)
            for line_num, lines in enumerate(code_list):

                yield f"\n\n```python\n{lines}\n```"
                yield "\n\n`Code running...`\n"
                plt_show = False
                if "plt.show()" in lines:
                    plt_show = True
                    print("plt_show")
                    filename = f"plot_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                    lines = lines.replace("import matplotlib.pyplot as plt",
                                          "import matplotlib.pyplot as plt\nfrom matplotlib.font_manager import FontProperties\nfont = FontProperties(fname=r'static\msyh.ttc')\n")
                    lines = lines.replace("plt.show()", f"plt.savefig('static/{filename}')")

                    print(lines)

                lines = lines.split('\n')
                # lines=[lines]
                # print(lines)
                filtered_lst = [item for item in lines if item.strip()]
                lines = filtered_lst
                new_lines = []
                for each_line in lines:

                    if '=' in each_line and (
                            'geo_filter' in each_line or 'id_list_of_entity' in each_line or 'area_filter(' in each_line or 'set_bounding_box' in each_line):

                        variable_str = each_line.split('=')[0]

                        new_line = f"""
send_data({variable_str}['geo_map'],'map')
    
                            """
                        new_lines.append(each_line)
                        new_lines.append(new_line)
                    elif '=' not in each_line and (
                            'geo_filter' in each_line or 'id_list_of_entity' in each_line or 'area_filter(' in each_line or 'set_bounding_box' in each_line):

                        new_line = f"""
temp_result={each_line}
send_data(temp_result['geo_map'],'map')
    
                            """
                        new_lines.append(each_line)
                        new_lines.append(new_line)
                    else:
                        new_lines.append(each_line)
                if '=' not in new_lines[-1] and 'send_data' not in new_lines[-1]:
                    new_line = f"""
print({lines[-1]})
                                        """
                    new_lines[-1] = new_line

                code_str = '\n'.join(new_lines)

                print(code_str)
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
                if plt_show and "An error occurred: " not in code_result:
                    code_result = f'![matplotlib_diagram](/static/{filename} "matplotlib_diagram")'
                    whole_step = 5  # 确保图返回结果只会被描述一次
                    yield code_result
                show_template = details_span(code_result, run_time)
                yield list(show_template.values())[0]
                if 'error' in show_template:
                    return
                send_result = "code_result:" + short_response(code_result)
                print(send_result)
                messages.append({"role": "user",
                                 "content": send_result})
                processed_response.append({'role': 'user', 'content': send_result})

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
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0', port=9090)
