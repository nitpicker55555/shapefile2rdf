# global_var.py
from flask import session

def get_my_var():
    return session.get('my_var', 'Initial Value')

def set_my_var(value):
    session['my_var'] = value

# 示例函数，展示如何引用全局变量
def example_function():
    my_var_value = get_my_var()
    print(f"The value of my_var in example_function is: {my_var_value}")
