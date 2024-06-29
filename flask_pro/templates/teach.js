function teach_assistent(tips){
    document.addEventListener('DOMContentLoaded', function () {

        let currentTipIndex = 0;
        const overlay = document.getElementById('overlay');
        const tooltip = document.getElementById('tooltip');
        const tooltipText = document.getElementById('tooltip-text');
        const tooltipButton = document.getElementById('tooltip-button');

        function showTip(index) {
            const tip = tips[index];
            if (!tip) return;

            const element = document.evaluate(tip.xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (!element) return;

            // Add highlight class to element
            element.classList.add('highlight');

            tooltipText.textContent = tip.text;
            tooltipButton.textContent = tip.button_name || "Got it";

            // Temporarily show the tooltip to get the correct height
            tooltip.style.display = 'block';
            tooltip.classList.add('visible');
            overlay.classList.add('visible');

            // Get the correct position after rendering
            const rect = element.getBoundingClientRect();
            tooltip.style.top = `${rect.top + window.scrollY - tooltip.offsetHeight - 20}px`; // Adjusted to show above the element
            tooltip.style.left = `${rect.left + window.scrollX + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;
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
