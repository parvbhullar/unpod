// static/js/gradient_picker.js

(function() {
    'use strict';

    function initGradientPicker(fieldWrapper) {
        const input = fieldWrapper.querySelector('input[type="text"]');
        if (!input || input.dataset.gradientInitialized) return;

        input.dataset.gradientInitialized = 'true';

        // Create gradient picker HTML
        const pickerHTML = `
            <div class="gradient-picker-wrapper">
                <div class="gradient-controls">
                    <div class="color-control">
                        <label>Start:</label>
                        <input type="color" class="gradient-color-input" id="${input.id}_color1" value="#9FC0FC">
                        <span class="color-value" id="${input.id}_color1_value">#9FC0FC</span>
                    </div>

                    <div class="color-control">
                        <label>End:</label>
                        <input type="color" class="gradient-color-input" id="${input.id}_color2" value="#D49FFD">
                        <span class="color-value" id="${input.id}_color2_value">#D49FFD</span>
                    </div>

                    <div class="direction-control">
                        <label>Direction:</label>
                        <select id="${input.id}_direction">
                            <option value="to right">Left to Right</option>
                            <option value="to left">Right to Left</option>
                            <option value="to bottom">Top to Bottom</option>
                            <option value="to top">Bottom to Top</option>
                            <option value="to bottom right">Diagonal ↘</option>
                            <option value="to bottom left">Diagonal ↙</option>
                            <option value="135deg">Diagonal ↗</option>
                            <option value="45deg">Diagonal ↖</option>
                            <option value="radial">Radial</option>
                        </select>
                    </div>
                </div>

                <div class="gradient-preview" id="${input.id}_preview"></div>

                <div class="gradient-value-display" id="${input.id}_display"></div>

                <div class="gradient-divider"></div>

                <div class="gradient-actions">
                    <button type="button" class="gradient-btn gradient-copy-btn">Copy CSS</button>
                    <div class="gradient-main_actions">
                        <button type="button" class="gradient-btn gradient-set-btn">Save</button>
                        <button type="button" class="gradient-btn gradient-clear-btn">Clear</button>
                    </div>
                </div>
            </div>
        `;

        // Hide original input and insert picker
        input.style.display = 'none';
        input.insertAdjacentHTML('afterend', pickerHTML);

        const color1Input = document.getElementById(`${input.id}_color1`);
        const color2Input = document.getElementById(`${input.id}_color2`);
        const directionSelect = document.getElementById(`${input.id}_direction`);
        const preview = document.getElementById(`${input.id}_preview`);
        const display = document.getElementById(`${input.id}_display`);
        const color1Value = document.getElementById(`${input.id}_color1_value`);
        const color2Value = document.getElementById(`${input.id}_color2_value`);
        const copyBtn = fieldWrapper.querySelector('.gradient-copy-btn');
        const setBgBtn = fieldWrapper.querySelector('.gradient-set-btn');
        const clearBgBtn = fieldWrapper.querySelector('.gradient-clear-btn');

        // Parse existing value if present
        if (input.value) {
            parseExistingGradient(input.value, color1Input, color2Input, directionSelect);
        }

        function updateGradient(apply = false) {
            const color1 = color1Input.value;
            const color2 = color2Input.value;
            const direction = directionSelect.value;

            color1Value.textContent = color1.toUpperCase();
            color2Value.textContent = color2.toUpperCase();

            let gradientCSS;
            if (direction === 'radial') {
                gradientCSS = `radial-gradient(circle, ${color1} 0%, ${color2} 100%)`;
            } else {
                gradientCSS = `linear-gradient(${direction}, ${color1} 0%, ${color2} 100%)`;
            }

            preview.style.background = gradientCSS;
            display.textContent = gradientCSS;

            if(apply) {
                input.value = gradientCSS;
                copyBtn.disabled = false;
                clearBgBtn.disabled = false;

                const originalText = setBgBtn.textContent;
                setBgBtn.textContent = 'Saved!';
                setTimeout(() => {
                    setBgBtn.textContent = originalText;
                }, 2000);
            }
        }

        function parseExistingGradient(value, color1, color2, direction) {
            // Simple parser for gradient values
            const colorRegex = /#[0-9A-Fa-f]{6}/g;
            const colors = value.match(colorRegex);

            if (colors && colors.length >= 2) {
                color1.value = colors[0];
                color2.value = colors[1];
            }

            // Parse direction
            if (value.includes('radial')) {
                direction.value = 'radial';
            } else if (value.includes('to bottom right')) {
                direction.value = 'to bottom right';
            } else if (value.includes('to bottom left')) {
                direction.value = 'to bottom left';
            } else if (value.includes('to right')) {
                direction.value = 'to right';
            } else if (value.includes('to left')) {
                direction.value = 'to left';
            } else if (value.includes('to bottom')) {
                direction.value = 'to bottom';
            } else if (value.includes('to top')) {
                direction.value = 'to top';
            } else if (value.includes('135deg')) {
                direction.value = '135deg';
            } else if (value.includes('45deg')) {
                direction.value = '45deg';
            } else {
                direction.value = 'to right';
            }
        }

        // Event listeners
        color1Input.addEventListener('input', updateGradient);
        color2Input.addEventListener('input', updateGradient);
        color1Input.addEventListener('change', updateGradient);
        color2Input.addEventListener('change', updateGradient);
        directionSelect.addEventListener('change', updateGradient);
        setBgBtn.addEventListener("click", function () {
            updateGradient(true)
        })

        clearBgBtn.addEventListener("click", function () {
            preview.style.background = '';
            display.textContent = '';
            input.value = '';

            // disabled set background button
            copyBtn.disabled = true;
            clearBgBtn.disabled = true;

            const originalText = clearBgBtn.textContent;
            clearBgBtn.textContent = 'Cleared!';
            setTimeout(() => {
                clearBgBtn.textContent = originalText;
            }, 2000);
        })

        copyBtn.addEventListener('click', function() {
            navigator.clipboard.writeText(input.value).then(() => {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                }, 2000);
            });
        });

        // Initialize
        updateGradient();
    }

    // Initialize on page load
    function init() {
        // Find all gradient fields (adjust selector based on your field name)
        const gradientFields = document.querySelectorAll('[name*="gradient"]');
        gradientFields.forEach(field => {
            const wrapper = field.closest('.form-row') || field.parentElement;
            if (wrapper) {
                initGradientPicker(wrapper);
            }
        });
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Support for Django's inline formsets
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).on('formset:added', function() {
            setTimeout(init, 100);
        });
    }
})();
