from flask import Flask, Response, stream_with_context, request, render_template

import time
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()
import sys
from io import StringIO

output = StringIO()
original_stdout = sys.stdout
app = Flask(__name__)

# 示例的 Markdown 文本（包含图片链接）
# ![示例图片](/static/data.png "这是一个示例图片")
markdown_text = """
要编写一个Python程序来读取一个文件夹（目录）中的所有文件和子目录，你可以使用标准库中的`os`模块。下面是一个简单的示例，展示了如何列出指定目录下的所有文件和文件夹。

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

"""
def chat_single(messages,mode="json"):
    if mode=="json":

        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            response_format={"type": "json_object"},
            messages=messages
        )
    else:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            stream=True,
            messages=messages
        )
    return response
messages2 = []
messages2.append({"role": "system",
                 "content": """
                 你现在拥有一个虚拟环境，你可以自由的运行python代码，并获得运行结果。你可以用python代码查看当前环境的所有信息。
                 """})
# 将Markdown文本渲染成HTML
# html_content = markdown2.markdown(markdown_text)

def extract_code(code_str):
    return code_str.split("```python")[1].split("```")[0]
@app.route('/')
def home():
    # 加载包含 Markdown 容器的前端页面
    return render_template('index.html')
@app.route('/submit', methods=['POST','GET'])
def submit():
    # 加载包含 Markdown 容器的前端页面
    data = request.get_json().get('text')  # 获取JSON数据
    print(data)  # 输出查看，实际应用中你可能会做其他处理
    messages2.append({"role": "user",
                 "content": data})

    chat_response=chat_single(messages2, "")



    def generate():
        chat_result=''
        for chunk in chat_response:
            if chunk.choices[0].delta.content is not None:
                char=chunk.choices[0].delta.content
                print(char, end="")
                chat_result+=char
                yield char

        messages2.append({"role": "assistant",
                          "content": str(chat_result)})
        if "```python" in chat_result:
            yield "`Code running...`\n"

            code_str=extract_code(chat_result)
            sys.stdout = output
            try:
                exec(code_str)
            except Exception as e:
                print(f"An error occurred: {e}")
            code_result=output.getvalue()
            output.truncate(0)
            sys.stdout = original_stdout
            yield "`Code result: `\n"
            yield "```"+code_result+"```"
            # print("code_result: ",code_result)
            messages2.append({"role": "user",
                              "content": "code result:"+code_result})
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

@app.route('/stream', methods=['POST','GET'])
def stream():
    # 生成逐字输出的HTML

    # data = request.get_json().get('text')  # 获取JSON数据
    # print(data)  # 输出查看，实际应用中你可能会做其他处理
    def generate():
        full_text=''
        for char in markdown_text:
            full_text+=char
            yield char
            time.sleep(0.001)  # 减小这个值以提高响应速度
        if "```python" in full_text:
            yield "\n\n`Code running...`\n"

            code_str=extract_code(full_text)
            sys.stdout = output
            try:
                exec(code_str)
            except Exception as e:
                print(f"An error occurred: {e}")
            code_result=output.getvalue()
            output.truncate(0)
            sys.stdout = original_stdout
            yield "\n`Code result: `\n"
            yield "```"+code_result+"```\n\n"


    return Response(stream_with_context(generate()))

if __name__ == '__main__':
    app.run(debug=True)
