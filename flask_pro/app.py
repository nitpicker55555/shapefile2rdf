from flask import Flask, Response, stream_with_context, render_template
import markdown2
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
markdown_text = """
如果你遇到了`$ is not defined`的错误，这意味着JavaScript在执行的时候无法识别`$`符号，这通常是因为jQuery没有被正确加载到你的页面中。`$`是jQuery的一个标志，用于访问jQuery库的功能。解决这个问题的方法有几个：

### 1. 确认jQuery的引入

确保你的HTML页面中包含了对jQuery库的引入。这通常通过在`<head>`部分或者页面的`<body>`结束标签之前，添加一个`<script>`标签来完成，指向jQuery的CDN地址或者是一个本地的jQuery文件。例如，使用Google的CDN来引入jQuery：

```html
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
```

请确认这段代码在你尝试使用`$`之前的某个地方正确引入。

### 2. 检查jQuery引入的位置

在某些情况下，如果你在引入jQuery库之前尝试使用`$`，也会遇到这个问题。确保所有使用`$`的脚本都在jQuery库引入之后运行。

### 3. 确保没有JavaScript加载顺序的问题

如果你的页面上还包含其他JavaScript文件或库，确保jQuery库是第一个被加载的，特别是在任何使用jQuery的脚本之前加载。

### 4. 检查是否有冲突

在极少数情况下，如果页面上还使用了其他也定义了`$`作为变量或函数的JavaScript库，可能会发生冲突。jQuery提供了`jQuery.noConflict()`方法来解决这个问题。使用这个方法后，你可以用`jQuery`代替`$`来避免冲突。

### 5. 检查浏览器的控制台错误

浏览器的开发者工具（通常可以通过按F12或右键选择“检查”打开）的控制台（Console）会显示具体的错误信息，这可能会给出为什么jQuery没有被定义的更多线索。可能是因为网络问题导致CDN上的jQuery库没有成功加载。

通过以上步骤，你应该能够找到导致`$ is not defined`错误的原因，并解决它，以确保jQuery正常工作。
这段代码包含两个函数，`addRequestMessage`和`addResponseMessage`，它们用于在一个简单的聊天界面中添加用户请求和系统响应。这个界面通过使用HTML和JavaScript构建，允许实现动态内容的添加和更新。下面是对这两个函数的详细解释：

### `addRequestMessage(message)`
此函数用于将用户的请求消息添加到聊天窗口中。它执行以下步骤：
1. 清空聊天输入框。
2. 对用户输入的消息进行HTML转义，以防止任何HTML标签被浏览器解析和渲染。这是一种防止跨站脚本攻击(XSS)的安全措施。
3. 创建一个包含用户消息的新的HTML元素，并使用转义后的消息内容。该元素设计成一个带有用户头像的消息气泡。
4. 将这个新元素添加到聊天窗口中。
5. 紧接着，创建一个带有加载图标的响应消息元素，并将其也添加到聊天窗口中，表示正在等待响应。
6. 最后，自动滚动聊天窗口到底部，确保最新的消息可见。

### `addResponseMessage(message)`
此函数用于将系统的响应消息添加到聊天窗口中，并支持流式响应，因此可能会被多次调用来追加消息。它包含以下逻辑：
1. 首先找到最后一个响应消息元素。
2. 清空该元素的内容，准备添加新的响应消息。
3. 检测消息中的代码块标记(````)，以判断是否所有的代码块都已正确闭合。
4. 如果发现有未闭合的代码块（即代码块标记的数量为奇数），则在消息末尾追加闭合标记，然后使用`marked.parse`将Markdown格式的消息转换为HTML。这是为了确保任何代码块都能被正确地渲染。
5. 如果代码块标记的数量为偶数且不为零，直接将Markdown消息转换为HTML。
6. 如果消息中没有代码块标记，先使用`escapeHtml`函数转义消息内容，然后再将其转换为HTML，防止XSS攻击。
7. 将转换后的HTML内容添加到响应消息元素中。
8. 自动滚动聊天窗口到底部，确保最新的响应消息可见。

整体来说，这段代码通过对用户请求和系统响应的动态添加与更新，实现了一个基本的流式聊天界面。同时，它还采用了安全措施（如HTML转义和Markdown解析）来防止潜在的安全风险。
"""

# 将Markdown文本渲染成HTML
html_content = markdown2.markdown(markdown_text)

def extract_code(code_str):
    return code_str.split("```python")[1].split("```")[0]
@app.route('/')
def home():
    # 加载包含 Markdown 容器的前端页面
    return render_template('index.html')

@app.route('/stream')
def stream():
    # 生成逐字输出的HTML
    def generate():
        full_text=''
        for char in markdown_text:
            full_text+=char
            yield char
            time.sleep(0.001)  # 减小这个值以提高响应速度
        if "```python" in full_text:
            code_str=extract_code(full_text)
            sys.stdout = output
            print(code_str)
            (exec(code_str))
            code_result=output.getvalue()
            output.truncate(0)
            sys.stdout = original_stdout

    return Response(stream_with_context(generate()))

if __name__ == '__main__':
    app.run(debug=True)
