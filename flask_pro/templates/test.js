async function waitForFalse(getVariableValue, checkInterval = 100, initialDelay = 1000) {
    return new Promise((resolve) => {
        setTimeout(() => {
            const intervalId = setInterval(() => {
                if (!getVariableValue()) { // 检查getVariableValue()的返回值是否为false
                    clearInterval(intervalId);
                    resolve(true);
                }
            }, checkInterval);
        }, initialDelay);
    });
}

let variableReference = { value: true };

function getVariableValue() {
    return variableReference.value;
}

async function checkVariable() {
    console.log("Waiting for variableReference.value to become false...");
    await waitForFalse(getVariableValue);
    console.log("variableReference.value is now false");
}

// 模拟在3秒后将variableReference.value设为false
setTimeout(() => {
    variableReference.value = false;
}, 3000);

// 调用异步函数
checkVariable();
