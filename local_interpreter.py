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

def extract_code(code_str):
    return code_str.split("```python")[1].split("```")[0]
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
            messages=messages
        )
    # print(response.choices[0].message.content)
    return response.choices[0].message.content

messages2 = []
messages2.append({"role": "system",
                 "content": """
                 你现在拥有一个虚拟环境，你可以自由的运行python代码，并获得运行结果。你可以用python代码查看当前环境的所有信息。
                 """})
while True:
    text=input("input: ")
    messages2.append({"role": "user",
                 "content": text})

    chat_result=(chat_single(messages2, ""))
    messages2.append({"role": "assistant",
                 "content": chat_result})
    if "```python" in chat_result:
        code_str=extract_code(chat_result)
        sys.stdout = output
        print(code_str)
        (exec(code_str))
        code_result=output.getvalue()
        output.truncate(0)
        sys.stdout = original_stdout
        print("code_result: ",code_result)
        messages2.append({"role": "user",
                          "content": "code result:"+code_result})
        chat_result = (chat_single(messages2, ""))
        print(chat_result)
        messages2.append({"role": "assistant",
                          "content": chat_result})