
from agent_function_call import tools

from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
import os
from dotenv import load_dotenv
load_dotenv()

#
os.environ['OPENAI_API_KEY']=os.getenv("OPENAI_API_KEY")
def message_template(role,new_info):
    new_dict={'role':role,'content':new_info}
    return new_dict

GPT_MODEL = "gpt-3.5-turbo-0613"
client = OpenAI()
@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=tools, tool_choice=None, model=GPT_MODEL):

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,#强制选用某个function
        )
        return response.choices[0].message
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
    print( response.choices[0].message.content)
    return response.choices[0].message.content

