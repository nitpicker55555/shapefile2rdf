function reorderDictionary(dict) {
    // 获取字典的键并排序
    let keys = Object.keys(dict).sort();

    // 将最后一个键移动到第0个位置
    if (keys.length > 1) {
        keys.unshift(keys.pop());
    }

    // 创建一个新的字典并按照新的顺序赋值
    let newDict = {};
    for (let key of keys) {
        newDict[key] = dict[key];
    }

    return newDict;
}

// 示例字典
let dict = {
    "banana": 1,
    "apple": 2,
    "cherry": 3,
    "date": 4
};

let sortedDict = reorderDictionary(dict);
console.log(sortedDict);
