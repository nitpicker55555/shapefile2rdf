# -*- coding: utf-8 -*-

import traceback
from flask import Flask, Response, stream_with_context, request, render_template, jsonify, session, redirect, url_for

import time
from openai import OpenAI
import os
from dotenv import load_dotenv
import io
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()
import sys
from io import StringIO

from flask_socketio import SocketIO, emit
output = StringIO()
original_stdout = sys.stdout
app = Flask(__name__)

app.secret_key = 'secret_key'  # 用于启用 flash() 方法发送消息
@app.before_request
def initialize_session():
    if 'globals_dict' not in session:
        session['globals_dict']={'bounding_box_region_name': 'FREISING',
                              'bounding_coordinates': [48.061625, 48.248098, 11.360777, 11.72291],
                              'bounding_wkb': '01030000000100000005000000494C50C3B7B82640D9CEF753E3074840494C50C3B7B82640FC19DEACC11F484019E76F4221722740FC19DEACC11F484019E76F4221722740D9CEF753E3074840494C50C3B7B82640D9CEF753E3074840'}

        print('session 初始化')

# global_variables = {}

# 示例的 Markdown 文本（包含图片链接）
# ![示例图片](/static/data.png "这是一个示例图片")
socketio = SocketIO(app, manage_session=True, async_mode='threading')



@app.route('/')
def home():

    return render_template('index.html')



@app.route('/debug_mode', methods=['POST'])
def debug_mode():
    data = request.get_json().get('message')  # 获取JSON数据
    if data == 'debug':
        session['template'] = True
    else:
        session['template'] = False
    return jsonify({"text": True}), 400



def send_data(data, mode="data", index="", sid=''):
    target_labels = []

    if sid != '':
        socketio.emit('text', {mode: data, 'index': index,'target_label':target_labels}, room=sid)
    else:
        print('no sid')


@app.route('/submit', methods=['POST', 'GET'])
def submit():
    data = request.get_json().get('text')  # 获取代码

    # 普通函数来处理代码执行和会话修改
    def process_code(data):
        sys.stdout = output
        try:
            exec(data, globals())  # 执行代码
        except Exception as e:
            exc_info = traceback.format_exc()
            # 打印错误信息和代码行
            if session.get('template'):
                print(f"An error occurred: {repr(e)}\n{exc_info}")
            else:
                print("Nothing can I get! Please change an area and search again :)")

        session.modified = True  # 修改会话

        code_result = str(output.getvalue().replace('\00', ''))
        output.truncate(0)
        sys.stdout = original_stdout
        return code_result

    # 执行代码并获取结果
    code_result = process_code(data)

    # 将结果生成响应
    def generate():
        yield data  # 将代码数据发送给客户端
        yield code_result  # 将执行结果发送给客户端

    return Response(stream_with_context(generate()))


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0', port=9090)