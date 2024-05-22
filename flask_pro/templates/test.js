function createSequentialPicker(array) {
    if (!Array.isArray(array) || array.length === 0) {
        throw new Error("Array must be a non-empty array.");
    }

    let currentIndex = 0;
    const usedElements = [];

    function getNextElement() {
        // 获取当前索引的元素
        const element = array[currentIndex];

        // 更新索引，如果到达数组末尾则重置为0
        currentIndex = (currentIndex + 1) % array.length;

        // 记录已经抽取过的元素
        usedElements.push(element);

        return element;
    }

    function getUsedElements() {
        return usedElements;
    }

    return {
        getNextElement,
        getUsedElements
    };
}

// 示例用法
const elements = ["A", "B", "C", "D", "E"];
const picker = createSequentialPicker(elements);

for (let i = 0; i < 15; i++) {
    console.log(`抽取到的元素: ${picker.getNextElement()}`);
}

console.log('已抽取过的元素:', picker.getUsedElements());
