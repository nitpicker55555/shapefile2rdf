chat_result="""
下每个文件夹的大小信息并绘制柱状图的Python代码：

```python
import os
import matplotlib.pyplot as plt

# 获取当前路径
current_path = os.getcwd()

# 获取当前路径下每个文件夹的大小
folders = [f for f in os.listdir(current_path) if os.path.isdir(f)]
folder_sizes = [sum(os.path.getsize(os.path.join(folder, f)) for f in os.listdir(os.path.join(current_path, folder)) if os.path.isfile(os.path.join(folder, f)))/1024/1024 for folder in folders]

# 绘制柱状图
plt.bar(range(len(folders)), folder_sizes, align='center')
plt.xticks(range(len(folders)), folders, rotation=45)
plt.xlabel('Folders')
plt.ylabel('Size (MB)')
plt.title('Folder Sizes in Current Path')
plt.show()
```

现在，我将运行这段代码并返回绘制的柱状图给您。
"""
def extract_code(code_str):
    return code_str.split("```python")[1].split("```")[0]
code_str=extract_code(chat_result)
plt_show=False
if "plt.show()" in code_str:
    plt_show=True
    print("plt_show")
    code_str=code_str.replace("plt.show()","plt.savefig('static/mat.png')")

try:
    exec(code_str)
except Exception as e:
    print(f"An error occurred: {e}")

