import { ref } from 'vue'

// Three discrete font size options (like Android)
const FONT_SIZE_OPTIONS = {
  SMALL: 75,    // Small
  MEDIUM: 100,  // Medium (default)
  LARGE: 125    // Large
}

const FONT_SIZE_LABELS = {
  [FONT_SIZE_OPTIONS.SMALL]: 'Small',
  [FONT_SIZE_OPTIONS.MEDIUM]: 'Medium',
  [FONT_SIZE_OPTIONS.LARGE]: 'Large'
}

const STORAGE_KEY = 'app_font_size'

// Global font size state (default to MEDIUM)
const fontSize = ref(FONT_SIZE_OPTIONS.MEDIUM)
const currentOptionIndex = ref(1) // 0 = Small, 1 = Medium, 2 = Large

// Get all font size values as array
const getFontSizeValues = () => [
  FONT_SIZE_OPTIONS.SMALL,
  FONT_SIZE_OPTIONS.MEDIUM,
  FONT_SIZE_OPTIONS.LARGE
]

// Get current option index from font size value
const getOptionIndex = (size) => {
  const values = getFontSizeValues()
  return values.indexOf(size)
}

// Get font size value from option index
const getFontSizeFromIndex = (index) => {
  const values = getFontSizeValues()
  return values[Math.max(0, Math.min(2, index))]
}

// Load font size from localStorage on initialization
const loadFontSize = () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    const parsed = parseInt(saved, 10)
    const values = getFontSizeValues()
    // Find closest matching option
    const closest = values.reduce((prev, curr) => 
      Math.abs(curr - parsed) < Math.abs(prev - parsed) ? curr : prev
    )
    fontSize.value = closest
    currentOptionIndex.value = getOptionIndex(closest)
  } else {
    fontSize.value = FONT_SIZE_OPTIONS.MEDIUM
    currentOptionIndex.value = 1
  }
  applyFontSize()
}

// Apply font size to document root
const applyFontSize = () => {
  document.documentElement.style.fontSize = `${fontSize.value}%`
}

// Save font size to localStorage
const saveFontSize = () => {
  localStorage.setItem(STORAGE_KEY, fontSize.value.toString())
}

// Set font size to specific option index (0, 1, or 2)
const setFontSizeByIndex = (index) => {
  const newSize = getFontSizeFromIndex(index)
  fontSize.value = newSize
  currentOptionIndex.value = index
  applyFontSize()
  saveFontSize()
}

// Increase font size (move to next option)
const increaseFontSize = () => {
  if (currentOptionIndex.value < 2) {
    setFontSizeByIndex(currentOptionIndex.value + 1)
  }
}

// Decrease font size (move to previous option)
const decreaseFontSize = () => {
  if (currentOptionIndex.value > 0) {
    setFontSizeByIndex(currentOptionIndex.value - 1)
  }
}

// Set font size directly (will snap to nearest option)
const setFontSize = (size) => {
  const values = getFontSizeValues()
  const closest = values.reduce((prev, curr) => 
    Math.abs(curr - size) < Math.abs(prev - size) ? curr : prev
  )
  fontSize.value = closest
  currentOptionIndex.value = getOptionIndex(closest)
  applyFontSize()
  saveFontSize()
}

// Reset to default (Medium)
const resetFontSize = () => {
  setFontSizeByIndex(1) // Medium
}

// Initialize on module load
if (typeof window !== 'undefined') {
  loadFontSize()
}

export const useFontSize = () => {
  return {
    fontSize,
    currentOptionIndex,
    increaseFontSize,
    decreaseFontSize,
    setFontSize,
    setFontSizeByIndex,
    resetFontSize,
    FONT_SIZE_OPTIONS,
    FONT_SIZE_LABELS,
    getFontSizeValues,
    getCurrentLabel: () => FONT_SIZE_LABELS[fontSize.value] || 'Medium'
  }
}
