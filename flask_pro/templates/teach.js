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

            const rect = element.getBoundingClientRect();
            tooltipText.textContent = tip.text;
            tooltip.style.top = `${rect.top + window.scrollY - tooltip.offsetHeight - 20}px`; // Adjusted to show above the element
            tooltip.style.left = `${rect.left + window.scrollX + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;

            tooltip.classList.add('visible');
            overlay.classList.add('visible');
            tooltip.style.display = 'block';
        }

        tooltipButton.addEventListener('click', function () {
            const element = document.evaluate(tips[currentTipIndex].xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (element) {
                // Remove highlight class from element
                element.classList.remove('highlight');
            }

            tooltip.classList.remove('visible');
            overlay.classList.remove('visible');
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
