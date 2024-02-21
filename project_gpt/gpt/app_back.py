# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, Response
import requests
import json
import datetime
import socket
app = Flask(__name__)

# 从配置文件中settings加载配置
app.config.from_pyfile('settings.py')

@app.route("/", methods=["GET"])
def index():
    return render_template("chat.html")
@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template("404.html"), 404
@app.route("/chat", methods=["POST"])
def chat():
    global final_conv,now,ip_,a
    ip_=request.headers.get('X-Real-IP')
    messages = request.form.get("prompts", None)
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
    user_list_ = str(prompts).split("'role': 'user', 'content': ")
    final_conv = user_list_[-1][:-2]
    a = len(user_list_) - 1

    final_ass_conv=""
    try:
        assistant_list_ = ass.split("'role': 'assistant', 'content': ")

        final_ass_conv = assistant_list_[-1][:-2].split("}, {'role': 'user', 'content': ")[0]
        print(final_ass_conv)
    except:
        pass


    with open("static/data1.txt", "a") as f:
        f.write(f"‘len:’，{a}  ‘time:’，  {now}, ‘ip:’，  {ip_}    {str(final_conv)},  \n")
    data = {
        "messages": prompts,
        "model": "gpt-3.5-turbo",
        "max_tokens": 1024,
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
    # 迭代器实现流式响应
    def generate():
        global final_conv,now,ip_,a
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
        with open("static/data2.txt", "a") as f:
            f.write(f"‘len:’，{a}， ‘time:’，  {now}，  ‘ip:’，  {ip_},  {query_ip_location(ip_)} \n")
            f.write(f"‘user:’，  {final_conv}\n")
            f.write(f"‘answer:’，  {response_str}\n")
        # 如果出现错误，此时错误信息迭代器已处理完，app_context已经出栈，要返回错误信息，需要将app_context手动入栈
        if errorStr != "":
            with app.app_context():
                yield errorStr

    return Response(generate(), content_type='application/octet-stream')


if __name__ == '__main__':
    app.run(port=5000)