# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, Response,session
import requests
import json
import datetime
import socket
from user_agents import parse

app = Flask(__name__)
# load_dotenv()

# app = Flask(__name__)
# openai.api_key = os.getenv('OPENAI_API_KEY')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.secret_key = 'your_very_secret_key_here22'  # 设置一个安全的密钥
# streaming_state = {'value': True}
# streaming_stopped = Signal()
# app.config.from_pyfile('settings.py')
# apiKey = app.config['OPENAI_API_KEY']
# 从配置文件中settings加载配置

import sys
from io import StringIO


output = StringIO()
original_stdout = sys.stdout



app.config.from_pyfile('settings.py')

@app.route("/", methods=["GET"])
def index():
    user_agent_string = request.headers.get('User-Agent')
    user_agent = parse(user_agent_string)

    # 获取操作系统和浏览器信息
    os = user_agent.os.family  # 操作系统
    browser = user_agent.browser.family  # 浏览器

    # 判断设备类型
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
    return render_template("chat.html")
@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template("404.html"), 404
@app.route("/chat", methods=["POST"])
def chat():
    # global final_conv,now,ip_,a
    ip_=request.headers.get('X-Real-IP')
    session['ip_']=ip_
    messages = request.form.get("prompts", None)

    print(messages)

    apiKey = request.form.get("apiKey", None)
    if messages is None:
        return jsonify({"error": {"message": "请输入prompts!", "type": "invalid_request_error"}})

    if apiKey is None:
        apiKey = app.config['OPENAI_API_KEY']

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {apiKey}",
    }

    # json串转对象
    prompts = json.loads(messages)


    now = datetime.datetime.now()
    session['now']=now
    user_list_ = str(prompts).split("'role': 'user', 'content': ")
    final_conv = user_list_[-1][:-2]
    session['final_conv']=final_conv
    ques_length = len(user_list_) - 1
    session['ques_length']=ques_length
    final_ass_conv=""

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
    data_no_response = {
        'len': str(ques_length),
        'time': str(now),
        'ip': str(ip_),
        'location': query_ip_location(ip_),
        'user': str(final_conv),
        'os':str(session['os']),
        'browser':str(session['browser']),
        'device':str(session['device_type'])
        # 'answer': str(response_str)
        # 'answer': response_str
    }

    # 打开JSONL文件并写入数据
    # with open("static/data3.txt", "a",encoding='utf-8') as f:
    #     f.write(json.dumps(data_no_response) + '\n')
    # with open("static/data3.txt", "a") as f:
    formatted_data = json.dumps(data_no_response, indent=2,ensure_ascii=False)

    # 写入文本文件
    with open('static/data3.txt', 'a',encoding='utf-8') as file:
        file.write(formatted_data)
    #     f.write(f"‘len:’，{ques_length}  ‘time:’，  {now}, ‘ip:’，  {ip_}    {str(final_conv)},  \n")
    # prompts.append({"role": "system", "content": "You are an assistant that provides concise and few words answers."})
    print(prompts)

    data = {
        "messages": prompts,
        "model": "gpt-3.5-turbo",
        "max_tokens": 512,
        "temperature": 0.5,
        "top_p": 1,
        "n": 1,
        "stream": True,
    }

    try:
        resp = requests.post(
            url=app.config["URL"],
            headers=headers,
            json=data,
            stream=True,
            timeout=(10, 10)  # 连接超时时间为10秒，读取超时时间为10秒
        )

    except TimeoutError:
        return jsonify({"error": {"message": "请求超时!", "type": "timeout_error"}})

    def extract_code(code_str):
        return code_str.split("```python")[1].split("```")[0]

    # 迭代器实现流式响应
    def generate(now,ip_,os,browser,device_type):
        # global final_conv,now,ip_,a
        errorStr = ""
        response_str=""

        for chunk in resp.iter_lines():
            if chunk:
                streamStr = chunk.decode("utf-8").replace("data: ", "")
                try:
                    streamDict = json.loads(streamStr)  # 说明出现返回信息不是正常数据,是接口返回的具体错误信息
                except:
                    errorStr += streamStr.strip()  # 错误流式数据累加
                    continue
                delData = streamDict["choices"][0]
                if delData["finish_reason"] != None :
                    break
                else:
                    if "content" in delData["delta"]:
                        respStr = delData["delta"]["content"]
                        # print(respStr)
                        response_str+=respStr
                        yield respStr
        # with open("static/data4.txt", "a") as f:
        #     f.write(f"‘len:’，{ques_length}， ‘time:’，  {now}，  ‘ip:’，  {ip_},  {query_ip_location(ip_)} \n")
        #     f.write(f"‘user:’，  {final_conv}\n")
        #     f.write(f"‘answer:’，  {response_str}\n")
        if "```python" in response_str:
            code_str = extract_code(response_str)
            sys.stdout = output
            print(code_str)
            (exec(code_str))
            code_result = output.getvalue()
            output.truncate(0)
            sys.stdout = original_stdout
            print("code_result: ", code_result)

        data_with_response = {
            'len': str(ques_length),
            'time': str(now),
            'ip': str(ip_),
            'location':query_ip_location(ip_),
            'os':str(os),
            'browser':str(browser),
            'device':str(device_type),
            'user': str(final_conv),
            'answer': str(response_str)

        }

        # 打开JSONL文件并写入数据
        with open("static/data4.txt", "a",encoding='utf-8') as f:
            f.write(json.dumps(data_with_response) + '\n')
        # 如果出现错误，此时错误信息迭代器已处理完，app_context已经出栈，要返回错误信息，需要将app_context手动入栈
        if errorStr != "":
            with app.app_context():
                yield errorStr

    return Response(generate(session['now'],session['ip_'],session['os'],session['browser'],session['device_type']), content_type='application/octet-stream')


if __name__ == '__main__':
    app.run(port=5000)