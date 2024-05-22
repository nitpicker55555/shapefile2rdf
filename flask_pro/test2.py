import pandas as pd
import numpy as np


def equal_interval_stats(data_dict, num_intervals=5):
    # 将字典值转换为DataFrame
    data = pd.DataFrame(list(data_dict.items()), columns=['Key', 'Value'])

    # 获取数据的最小值和最大值
    min_value = data['Value'].min()
    max_value = data['Value'].max()

    # 确保最小值不为零
    if min_value == 0:
        min_value = min(data['Value'][data['Value'] > 0])

    # 创建等间距区间
    intervals = np.linspace(min_value, max_value, num_intervals + 1)
    interval_labels = [f"{intervals[i]:.2f} - {intervals[i + 1]:.2f}" for i in range(len(intervals) - 1)]

    # 创建一个新的字典存储结果
    result = {label: 0 for label in interval_labels}

    # 计算每个区间内的数量
    for i in range(len(intervals) - 1):
        lower_bound = intervals[i]
        upper_bound = intervals[i + 1]
        count = data[(data['Value'] > lower_bound) & (data['Value'] <= upper_bound)].shape[0]
        result[interval_labels[i]] = count

    return result


# 示例数据
data_dict = {
    'A': 0,
    'B': 1500,
    'C': 3000,
    'D': 4500,
    'E': 8000,
    'F': 12000,
    'G': 25000,
    'H': 60000,
    'I': 100000
}

# 调用函数
result = equal_interval_stats(data_dict, num_intervals=6)
print(result)
