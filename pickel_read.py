import pickle
result_list=[]
# 从文件反序列化列表+
import matplotlib.pyplot as plt
from collections import Counter
def calculate_and_print_frequencies(lst):
    # 计算列表中每个元素的频率
    frequencies = Counter(lst)

    # 打印每个元素及其频率
    for item, frequency in frequencies.items():
        print(f"{item}: {frequency}")
def plot_histogram(building_types):
    # 绘制直方图
    plt.hist(building_types, bins=len(set(building_types)), color='skyblue', edgecolor='black')

    # 设置标题和标签
    plt.title('Building Types')
    plt.xlabel('Type of Building')
    plt.ylabel('Frequency')

    # 使x轴的标签倾斜45度
    plt.xticks(rotation=45, ha='right')

    # 显示直方图
    plt.show()

with open('my_list.pkl', 'rb') as file:
    loaded_list = pickle.load(file)
for i in loaded_list:
    result_list.append(i.split("/")[1])
print(result_list)
# plot_histogram(result_list)
calculate_and_print_frequencies(result_list)