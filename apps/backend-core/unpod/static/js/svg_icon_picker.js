// static/js/svg_icon_picker.js - Updated with color extraction

(function() {
    'use strict';

    // Popular SVG icon library
    const iconLibrary = {
        'home': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
        'user': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
        'heart': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
        'star': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
        'mail': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
        'shopping-cart': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>',
        'settings': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6m5.2-13.2l-4.2 4.2m0 6l4.2 4.2M23 12h-6m-6 0H1m18.2 5.2l-4.2-4.2m-6 0l-4.2 4.2"/></svg>',
        'check': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
        'x': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
        'plus': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
        'search': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>',
        'bell': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
        'calendar': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
        'camera': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
        'clock': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        'download': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
        'upload': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
        'folder': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
        'file': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>',
        'image': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>',
        'lock': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    };

    /**
     * Extract color from SVG string
     * Looks for stroke, fill, or color attributes
     */
    function extractColorFromSvg(svgString) {
        if (!svgString) return '#000000';

        // Try to find stroke color (most common in line icons)
        const strokeMatch = svgString.match(/stroke="(#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}|rgb\([^)]+\)|[a-z]+)"/);
        if (strokeMatch && strokeMatch[1] !== 'none' && strokeMatch[1] !== 'currentColor') {
            return normalizeColor(strokeMatch[1]);
        }

        // Try to find fill color
        const fillMatch = svgString.match(/fill="(#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}|rgb\([^)]+\)|[a-z]+)"/);
        if (fillMatch && fillMatch[1] !== 'none' && fillMatch[1] !== 'currentColor') {
            return normalizeColor(fillMatch[1]);
        }

        // Default to black
        return '#000000';
    }

    /**
     * Normalize color to hex format
     */
    function normalizeColor(color) {
        // If already hex, return as-is
        if (color.startsWith('#')) {
            // Convert 3-digit hex to 6-digit
            if (color.length === 4) {
                return '#' + color[1] + color[1] + color[2] + color[2] + color[3] + color[3];
            }
            return color;
        }

        // Handle rgb() format
        if (color.startsWith('rgb')) {
            const rgbMatch = color.match(/\d+/g);
            if (rgbMatch && rgbMatch.length >= 3) {
                const r = parseInt(rgbMatch[0]).toString(16).padStart(2, '0');
                const g = parseInt(rgbMatch[1]).toString(16).padStart(2, '0');
                const b = parseInt(rgbMatch[2]).toString(16).padStart(2, '0');
                return '#' + r + g + b;
            }
        }

        // Handle named colors
        const namedColors = {
            'black': '#000000',
            'white': '#FFFFFF',
            'red': '#FF0000',
            'green': '#008000',
            'blue': '#0000FF',
            'yellow': '#FFFF00',
            'cyan': '#00FFFF',
            'magenta': '#FF00FF',
            'gray': '#808080',
            'grey': '#808080',
        };

        return namedColors[color.toLowerCase()] || '#000000';
    }

    /**
     * Get all colors used in SVG (for multi-color icons)
     */
    function getAllColorsFromSvg(svgString) {
        const colors = new Set();

        // Find all stroke colors
        const strokeMatches = svgString.matchAll(/stroke="([^"]+)"/g);
        for (const match of strokeMatches) {
            if (match[1] !== 'none' && match[1] !== 'currentColor') {
                colors.add(normalizeColor(match[1]));
            }
        }

        // Find all fill colors
        const fillMatches = svgString.matchAll(/fill="([^"]+)"/g);
        for (const match of fillMatches) {
            if (match[1] !== 'none' && match[1] !== 'currentColor') {
                colors.add(normalizeColor(match[1]));
            }
        }

        return Array.from(colors);
    }

    function initSvgIconPicker(fieldWrapper) {
        const textarea = fieldWrapper.querySelector('textarea[name*="svg_icon"]');
        if (!textarea || textarea.dataset.svgInitialized) return;

        textarea.dataset.svgInitialized = 'true';

        // Create SVG icon picker HTML
        const pickerHTML = `
            <div class="svg-icon-picker-wrapper">
                <div class="svg-tabs">
                    <button type="button" class="svg-tab active" data-tab="library">Icon Library</button>
                    <button type="button" class="svg-tab" data-tab="custom">Custom SVG</button>
                </div>

                <div class="svg-tab-content" id="library-tab">
                    <div class="svg-icon-grid" id="${textarea.id}_grid"></div>
                </div>

                <div class="svg-tab-content" style="display: none;" id="custom-tab">
                    <div class="svg-custom-editor">
                        <div class="svg-editor-header">
                            <label>Paste your SVG code:</label>
                            <button type="button" class="svg-clear-btn">Clear</button>
                        </div>
                        <textarea class="svg-code-editor" id="${textarea.id}_editor" rows="8" placeholder="<svg>...</svg>"></textarea>
                        <div class="svg-info-panel" id="${textarea.id}_info" style="display: none;">
                            <strong>Detected colors:</strong>
                            <div id="${textarea.id}_colors"></div>
                        </div>
                    </div>
                </div>

                <div class="svg-preview-section">
                    <label>Preview:</label>
                    <div class="svg-preview-box" id="${textarea.id}_preview">
                        <span class="svg-preview-placeholder">No icon selected</span>
                    </div>
                    <div class="svg-color-controls">
                        <label for="${textarea.id}_color">Icon Color:</label>
                        <input type="color" id="${textarea.id}_color" value="#000000" class="svg-color-input">
                        <span id="${textarea.id}_color_value">#000000</span>
                        <button type="button" class="svg-detect-color-btn" id="${textarea.id}_detect">Detect Color</button>
                    </div>
                </div>
            </div>
        `;

        // Hide original textarea and insert picker
        textarea.style.display = 'none';
        textarea.insertAdjacentHTML('afterend', pickerHTML);

        const iconGrid = document.getElementById(`${textarea.id}_grid`);
        const preview = document.getElementById(`${textarea.id}_preview`);
        const colorInput = document.getElementById(`${textarea.id}_color`);
        const colorValue = document.getElementById(`${textarea.id}_color_value`);
        const codeEditor = document.getElementById(`${textarea.id}_editor`);
        const clearBtn = fieldWrapper.querySelector('.svg-clear-btn');
        const detectBtn = document.getElementById(`${textarea.id}_detect`);
        const infoPanel = document.getElementById(`${textarea.id}_info`);
        const colorsDiv = document.getElementById(`${textarea.id}_colors`);
        const tabs = fieldWrapper.querySelectorAll('.svg-tab');
        const libraryTab = document.getElementById('library-tab');
        const customTab = document.getElementById('custom-tab');

        // Populate icon library
        Object.entries(iconLibrary).forEach(([name, svg]) => {
            const iconBtn = document.createElement('button');
            iconBtn.type = 'button';
            iconBtn.className = 'svg-icon-btn';
            iconBtn.title = name;
            iconBtn.innerHTML = svg;
            iconBtn.addEventListener('click', () => selectIcon(svg));
            iconGrid.appendChild(iconBtn);
        });

        function selectIcon(svg) {
            const coloredSvg = applySvgColor(svg, colorInput.value);
            textarea.value = coloredSvg;
            updatePreview(coloredSvg);
            codeEditor.value = coloredSvg;
        }

        /**
         * Apply color to SVG - FIXED VERSION
         * Replaces all color references (stroke, fill, currentColor) with the new color
         */
        function applySvgColor(svg, newColor) {
            let result = svg;

            // Replace currentColor
            result = result.replace(/stroke="currentColor"/gi, `stroke="${newColor}"`);
            result = result.replace(/fill="currentColor"/gi, `fill="${newColor}"`);

            // Replace existing hex colors in stroke
            result = result.replace(/stroke="#[0-9A-Fa-f]{6}"/gi, `stroke="${newColor}"`);
            result = result.replace(/stroke="#[0-9A-Fa-f]{3}"/gi, `stroke="${newColor}"`);

            // Replace existing hex colors in fill (but keep fill="none")
            result = result.replace(/fill="#[0-9A-Fa-f]{6}"/gi, `fill="${newColor}"`);
            result = result.replace(/fill="#[0-9A-Fa-f]{3}"/gi, `fill="${newColor}"`);

            // Replace RGB colors in stroke
            result = result.replace(/stroke="rgb\([^)]+\)"/gi, `stroke="${newColor}"`);
            result = result.replace(/stroke="rgba\([^)]+\)"/gi, `stroke="${newColor}"`);

            // Replace RGB colors in fill
            result = result.replace(/fill="rgb\([^)]+\)"/gi, `fill="${newColor}"`);
            result = result.replace(/fill="rgba\([^)]+\)"/gi, `fill="${newColor}"`);

            // Replace named colors in stroke (but not 'none')
            result = result.replace(/stroke="(black|white|red|green|blue|yellow|cyan|magenta|gray|grey|orange|purple)"/gi, `stroke="${newColor}"`);

            // Replace named colors in fill (but not 'none')
            result = result.replace(/fill="(black|white|red|green|blue|yellow|cyan|magenta|gray|grey|orange|purple)"/gi, `fill="${newColor}"`);

            return result;
        }

        function updatePreview(svg) {
            if (svg && svg.trim()) {
                preview.innerHTML = svg;
                preview.classList.remove('empty');
                detectCurrentColor();
            } else {
                preview.innerHTML = '<span class="svg-preview-placeholder">No icon selected</span>';
                preview.classList.add('empty');
            }
        }

        // Detect current color from SVG
        function detectCurrentColor() {
            const svgContent = textarea.value || codeEditor.value;
            if (svgContent) {
                const detectedColor = extractColorFromSvg(svgContent);
                colorInput.value = detectedColor;
                colorValue.textContent = detectedColor.toUpperCase();

                // Show all colors if multiple
                const allColors = getAllColorsFromSvg(svgContent);
                if (allColors.length > 0) {
                    infoPanel.style.display = 'block';
                    colorsDiv.innerHTML = allColors.map(color =>
                        `<span class="color-chip" style="background: ${color};" title="${color}"></span>`
                    ).join('');
                } else {
                    infoPanel.style.display = 'none';
                }

                console.log('Detected color:', detectedColor);
                console.log('All colors:', allColors);
            }
        }

        // Color input handler
        colorInput.addEventListener('input', function() {
            const color = this.value;
            colorValue.textContent = color.toUpperCase();

            if (textarea.value) {
                const coloredSvg = applySvgColor(textarea.value, color);
                textarea.value = coloredSvg;
                codeEditor.value = coloredSvg;
                updatePreview(coloredSvg);
            }
        });

        // Custom code editor handler
        codeEditor.addEventListener('input', function() {
            textarea.value = this.value;
            updatePreview(this.value);
        });

        // Detect color button
        detectBtn.addEventListener('click', detectCurrentColor);

        // Clear button
        clearBtn.addEventListener('click', function() {
            codeEditor.value = '';
            textarea.value = '';
            updatePreview('');
            infoPanel.style.display = 'none';
        });

        // Tab switching
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                const tabName = this.dataset.tab;
                if (tabName === 'library') {
                    libraryTab.style.display = 'block';
                    customTab.style.display = 'none';
                } else {
                    libraryTab.style.display = 'none';
                    customTab.style.display = 'block';
                }
            });
        });

        // Initialize with existing value
        if (textarea.value) {
            updatePreview(textarea.value);
            codeEditor.value = textarea.value;

            // Auto-detect color from existing SVG
            const detectedColor = extractColorFromSvg(textarea.value);
            colorInput.value = detectedColor;
            colorValue.textContent = detectedColor.toUpperCase();
        }
    }

    // Initialize on page load
    function init() {
        const svgFields = document.querySelectorAll('[name*="svg_icon"]');
        svgFields.forEach(field => {
            const wrapper = field.closest('.form-row') || field.parentElement;
            if (wrapper) {
                initSvgIconPicker(wrapper);
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
