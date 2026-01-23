/**
 * Colorblindness Utility
 * Reads color mappings from CSS variables in Colourblindness.css
 * This ensures all color conversions come from a single source of truth
 */

/**
 * Get CSS variable value
 */
export function getCSSVariable(varName, fallback = null) {
  if (typeof document === 'undefined') return fallback;
  const value = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  return value || fallback;
}

/**
 * Convert rgba/rgb to hex
 */
export function rgbaToHex(rgba) {
  if (!rgba) return rgba;
  if (rgba.startsWith('#')) return rgba.toLowerCase();
  
  const match = rgba.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/);
  if (match) {
    const r = parseInt(match[1]).toString(16).padStart(2, '0');
    const g = parseInt(match[2]).toString(16).padStart(2, '0');
    const b = parseInt(match[3]).toString(16).padStart(2, '0');
    return `#${r}${g}${b}`.toLowerCase();
  }
  return rgba.toLowerCase();
}

/**
 * Get colorblindness mode from document
 */
export function getColorblindMode() {
  if (typeof document === 'undefined') return null;
  const html = document.documentElement;
  return html.getAttribute('data-colorblind') || null;
}

/**
 * Convert color for colorblindness using CSS variables
 * This is the single source of truth for all color conversions
 */
export function convertColorForColorblind(color) {
  if (!color) return color;
  
  const mode = getColorblindMode();
  if (!mode) return color;
  
  const hexColor = rgbaToHex(color);
  const normalizedColor = hexColor.toLowerCase();
  
  // Map color hex codes to CSS variable names
  // This is the single source of truth - all color mappings come from Colourblindness.css
  const colorVarMap = {
    // Green colors
    '#2ecc71': '--cb-green-2ecc71',
    '#10b981': '--cb-green-10b981',
    '#22c55e': '--cb-green-22c55e',
    '#34d399': '--cb-green-34d399',
    '#1abc9c': '--cb-green-1abc9c',
    '#4caf50': '--cb-green-4caf50',
    '#4ade80': '--cb-green-4ade80',
    '#84cc16': '--cb-green-84cc16',
    '#16a34a': '--cb-success',
    '#059669': '--cb-success',
    '#27ae60': '--cb-success',
    '#14b8a6': '--cb-success', // Teal - use success for protanopia/tritanopia
    '#4bc0c0': '--cb-success', // Teal/cyan -> use success for protanopia/tritanopia
    '#006837': '--cb-success', // Dark green (heatmap)
    '#1a9850': '--cb-success', // Green (heatmap)
    '#91cf60': '--cb-success', // Light green (heatmap)
    
    // Blue colors
    '#3498db': '--cb-blue-3498db',
    '#60a5fa': '--cb-blue-60a5fa',
    '#3b82f6': '--cb-blue-3b82f6',
    '#2563eb': '--cb-primary',
    '#4f6cff': '--cb-blue-4f6cff',
    '#2196f3': '--cb-blue-2196f3',
    '#36a2eb': '--cb-blue-36a2eb',
    '#818cf8': '--cb-blue-818cf8',
    '#06b6d4': '--cb-blue-06b6d4',
    '#4f46e5': '--cb-blue-4f46e5',
    '#6366f1': '--cb-blue-3b82f6', // Indigo -> use blue mapping
    '#3f51b5': '--cb-blue-3b82f6', // Indigo -> use blue mapping
    
    // Orange colors
    '#f39c12': '--cb-orange-f39c12',
    '#f59e0b': '--cb-orange-f59e0b', // Use specific orange variable for proper colorblindness conversion
    '#f97316': '--cb-warning',
    '#e67e22': '--cb-orange-e67e22',
    '#ff9800': '--cb-orange-ff9800',
    '#ff9f40': '--cb-orange-ff9f40',
    '#fb923c': '--cb-orange-f39c12', // Light orange -> use orange mapping
    '#ea580c': '--cb-warning',
    '#d97706': '--cb-orange-f39c12', // Use orange mapping
    
    // Yellow colors
    '#fbbf24': '--cb-yellow-fbbf24',
    '#facc15': '--cb-yellow-facc15',
    '#eab308': '--cb-yellow-eab308',
    '#ffeb3b': '--cb-yellow-ffeb3b',
    '#ffce56': '--cb-yellow-ffce56',
    '#f1c40f': '--cb-yellow-f1c40f',
    '#d9ef8b': '--cb-yellow-fbbf24', // Yellow-green (heatmap) -> use yellow mapping
    '#fee08b': '--cb-yellow-fbbf24', // Light yellow (heatmap) -> use yellow mapping
    
    // Red colors
    '#e74c3c': '--cb-red-e74c3c',
    '#ef4444': '--cb-red-ef4444',
    '#f44336': '--cb-red-f44336',
    '#dc2626': '--cb-error',
    '#d73027': '--cb-red-d73027',
    '#f43f5e': '--cb-error',
    '#f87171': '--cb-error', // Light red -> use error
    '#d32f2f': '--cb-error', // Deep red -> use error
    
    // Purple colors
    '#9b59b6': '--cb-purple-9b59b6',
    '#a78bfa': '--cb-purple-a78bfa',
    '#c4b5fd': '--cb-purple-c4b5fd',
    '#8b5cf6': '--cb-accent-purple',
    '#7c3aed': '--cb-accent-purple',
    '#9c27b0': '--cb-accent-purple', // Material purple -> use accent purple
    '#9932cc': '--cb-accent-purple', // Dark orchid -> use accent purple
    
    // Pink colors
    '#f472b6': '--cb-pink-f472b6',
    '#fb7185': '--cb-pink-fb7185',
    '#ff6384': '--cb-pink-ff6384',
    '#ec4899': '--cb-pink-ec4899',
    
    // Gray colors (no conversion needed)
    '#94a3b8': null, // Gray - no conversion
  };
  
  // Get CSS variable name for this color
  const varName = colorVarMap[normalizedColor];
  if (!varName) {
    // If no mapping found (or explicitly null like gray), return original color
    return color;
  }
  
  // Read the CSS variable value
  const convertedColor = getCSSVariable(varName);
  if (!convertedColor) {
    return color;
  }
  
  // If original was rgba/rgb, preserve the opacity
  if (color.startsWith('rgba') || color.startsWith('rgb')) {
    const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
    if (match && convertedColor.startsWith('#')) {
      const opacity = match[4] || '1';
      const r = parseInt(convertedColor.slice(1, 3), 16);
      const g = parseInt(convertedColor.slice(3, 5), 16);
      const b = parseInt(convertedColor.slice(5, 7), 16);
      if (color.startsWith('rgba')) {
        return `rgba(${r}, ${g}, ${b}, ${opacity})`;
      } else {
        return `rgb(${r}, ${g}, ${b})`;
      }
    }
  }
  
  return convertedColor;
}

