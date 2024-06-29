function waitForTrue(variableReference, checkInterval = 100) {
    return new Promise((resolve) => {
        const intervalId = setInterval(() => {
            if (!variableReference.value) {
                clearInterval(intervalId);
                resolve(true);
            }
        }, checkInterval);
    });
}
function teach_assistent(tips){
    document.addEventListener('DOMContentLoaded', function () {

        let currentTipIndex = 0;
        const overlay = document.getElementById('overlay');
        const tooltip = document.getElementById('tooltip');
        const tooltipText = document.getElementById('tooltip-text');
        const tooltipButton = document.getElementById('tooltip-button');
        function checkElementExists(xpath) {
            return new Promise(resolve => {
                const interval = setInterval(() => {
                    const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (element) {
                        clearInterval(interval);
                        resolve(element);
                    }
                    console.log('wait for elements',xpath)
                }, 1000); // Check every 100ms
            });
        }

        async function showTip(index) {
            const tip = tips[index];
            if (!tip) return;

            const element = await checkElementExists(tip.xpath);
            if (!element) return;

            // Add highlight class to element
            element.classList.add('highlight');

            tooltipText.innerHTML = tip.text;
            tooltipButton.textContent = tip.button_name || "Got it";

            // Temporarily show the tooltip to get the correct height
            tooltip.style.display = 'block';
            tooltip.classList.add('visible');
            overlay.classList.add('visible');

            // Get the correct position after rendering
            const rect = element.getBoundingClientRect();
            let tooltipTop = rect.top + window.scrollY - tooltip.offsetHeight - 20;
            if (tooltipTop < 0) {
                tooltip.style.top = '0px';
            } else {
                tooltip.style.top = `${tooltipTop}px`;
            }
            tooltip.style.left = `${rect.left + window.scrollX + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;

// 获取元素的z-index


            // console.log('The z-index of the element is: ' + window.getComputedStyle(element).zIndex);
            // console.log('The z-index of the tool is: ' + window.getComputedStyle(tooltip).zIndex);
            // console.log('The z-index of the overlay is: ' + window.getComputedStyle(overlay).zIndex);
        }


        tooltipButton.addEventListener('click', async function () {

            const tip = tips[currentTipIndex];
            const element = document.evaluate(tip.xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (element) {
                // Remove highlight class from element
                element.classList.remove('highlight');
            }

            tooltip.classList.remove('visible');
            overlay.classList.remove('visible');
            if (tip.command) {
                tip.command();
            }
            // Check the goal function
            if (tip.goal) {
                const goalAchieved = await tip.goal();
                if (!goalAchieved) return;
            }

            currentTipIndex++;
            if (currentTipIndex < tips.length) {
                setTimeout(() => {
                    showTip(currentTipIndex);
                }, 500); // Wait for the fade-out animation to complete
            } else {
                setTimeout(() => {
                    tooltip.style.display = 'none';
                }, 500); // Wait for the fade-out animation to complete
            }
        });

        // Show the first tip initially
        showTip(currentTipIndex);
    });
}
