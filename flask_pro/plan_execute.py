import json
from agent_function_call import tools,simiplified_tools

from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
def message_template(role,new_info):
    new_dict={'role':role,'content':new_info}
    return new_dict

GPT_MODEL = "gpt-3.5-turbo-0613"
client = OpenAI(api_key='')
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
    return response.choices[0].message.content
# chat_completion_request('')
system_propmt='For the following task, make plans that can solve the problem step by step. For each plan, indicate \
which external tool together with tool input to retrieve evidence. You can store the evidence into a \
variable #E that can be called by later tools. (Plan, #E1, Plan, #E2, Plan, ...)Tools can be one of the following:'+str(tools)+"""
For example,
Task: Thomas, Toby, and Rebecca worked a total of 157 hours in one week. Thomas worked x
hours. Toby worked 10 hours less than twice what Thomas worked, and Rebecca worked 8 hours
less than Toby. How many hours did Rebecca work?
Plan: Given Thomas worked x hours, translate the problem into algebraic expressions and solve
with Wolfram Alpha. #E1 = WolframAlpha[Solve x + (2x − 10) + ((2x − 10) − 8) = 157]
Plan: Find out the number of hours Thomas worked. #E2 = LLM[What is x, given #E1]
Plan: Calculate the number of hours Rebecca worked. #E3 = Calculator[(2 ∗ #E2 − 10) − 8]

Begin! 
Describe your plans with rich details. Each Plan should be followed by only one #E.
"""
messages=[]
messages.append(message_template('system',system_propmt))
messages.append(message_template('user','I want to search which buildings in forest in munich ismaning'))
result=chat_single(messages,'')
print(result)
