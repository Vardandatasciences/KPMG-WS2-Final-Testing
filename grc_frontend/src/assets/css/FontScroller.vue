<template>
  <div class="font-scroller-container">
    <div class="font-scroller-wrapper">
      <span class="font-scroller-label">Font Size</span>
      <div 
        class="font-scroll-bar"
        ref="scrollBarRef"
        @mousedown="handleTrackClick"
        @wheel="handleWheel"
        :title="`Font Size: ${currentLabel}`"
      >
        <div class="scroll-bar-track">
          <!-- Fill indicator -->
          <div 
            class="scroll-bar-fill"
            :style="{ width: `${fillPercentage}%` }"
          ></div>
          
          <!-- Three markers/dots -->
          <div 
            v-for="(option, index) in fontSizeOptions" 
            :key="index"
            class="scroll-bar-marker"
            :class="{ 'marker-active': index === currentOptionIndex }"
            :style="{ left: `${(index / 2) * 100}%` }"
            @click.stop="setFontSizeByIndex(index)"
          ></div>
          
          <!-- Handle -->
          <div 
            class="scroll-bar-handle"
            :class="{ 'handle-active': isDragging }"
            :style="{ left: `${fillPercentage}%` }"
            @mousedown.stop="handleMouseDown"
          >          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useFontSize } from './useFontSize.js'
import './fontscroller.css'

// Props
const props = defineProps({
  // Enable global wheel scrolling with Ctrl key
  enableGlobalWheel: {
    type: Boolean,
    default: false
  }
})

const { 
  currentOptionIndex,
  increaseFontSize, 
  decreaseFontSize, 
  setFontSizeByIndex,
  getFontSizeValues,
  getCurrentLabel
} = useFontSize()

const scrollBarRef = ref(null)
const isDragging = ref(false)
const startX = ref(0)

// Font size options and labels
const fontSizeOptions = computed(() => getFontSizeValues())
const currentLabel = computed(() => getCurrentLabel())

// Calculate fill percentage (0%, 50%, or 100%)
const fillPercentage = computed(() => {
  return (currentOptionIndex.value / 2) * 100
})

// Handle mouse wheel on scroll bar
const handleWheel = (event) => {
  event.preventDefault()
  event.stopPropagation()
  
  if (event.deltaY < 0) {
    // Scrolling up - increase font
    increaseFontSize()
  } else {
    // Scrolling down - decrease font
    decreaseFontSize()
  }
}

// Handle global wheel scrolling (Ctrl + Wheel)
const handleGlobalWheel = (event) => {
  // Only trigger if Ctrl key is pressed
  if (event.ctrlKey || event.metaKey) {
    event.preventDefault()
    
    if (event.deltaY < 0) {
      // Scrolling up - increase font
      increaseFontSize()
    } else {
      // Scrolling down - decrease font
      decreaseFontSize()
    }
  }
}

// Handle clicking on the track - snap to nearest option
const handleTrackClick = (event) => {
  if (!scrollBarRef.value) return
  
  const rect = scrollBarRef.value.getBoundingClientRect()
  const trackWidth = rect.width
  const x = event.clientX - rect.left
  const percentage = Math.max(0, Math.min(100, (x / trackWidth) * 100))
  
  // Determine which option to snap to (0, 1, or 2)
  let targetIndex
  if (percentage < 25) {
    targetIndex = 0 // Small
  } else if (percentage < 75) {
    targetIndex = 1 // Medium
  } else {
    targetIndex = 2 // Large
  }
  
  setFontSizeByIndex(targetIndex)
  
  // Start dragging from the clicked position
  isDragging.value = true
  startX.value = event.clientX
  
  event.preventDefault()
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

// Handle mouse down on handle
const handleMouseDown = (event) => {
  if (!scrollBarRef.value) return
  
  isDragging.value = true
  startX.value = event.clientX
  
  event.preventDefault()
  event.stopPropagation()
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

// Handle mouse move while dragging - snap to nearest option
const handleMouseMove = (event) => {
  if (!isDragging.value || !scrollBarRef.value) return
  
  const rect = scrollBarRef.value.getBoundingClientRect()
  const trackWidth = rect.width
  const x = event.clientX - rect.left
  const percentage = Math.max(0, Math.min(100, (x / trackWidth) * 100))
  
  // Determine which option to snap to (0, 1, or 2)
  let targetIndex
  if (percentage < 25) {
    targetIndex = 0 // Small
  } else if (percentage < 75) {
    targetIndex = 1 // Medium
  } else {
    targetIndex = 2 // Large
  }
  
  setFontSizeByIndex(targetIndex)
}

// Handle mouse up
const handleMouseUp = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}

// Setup global wheel listener if enabled
onMounted(() => {
  if (props.enableGlobalWheel) {
    document.addEventListener('wheel', handleGlobalWheel, { passive: false })
  }
})

// Cleanup on unmount
onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  if (props.enableGlobalWheel) {
    document.removeEventListener('wheel', handleGlobalWheel)
  }
})
</script>

<style scoped>
.font-scroller-container {
  display: inline-flex;
  align-items: center;
  user-select: none;
}

.font-scroller-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.font-scroller-label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  white-space: nowrap;
}

.font-scroll-bar {
  position: relative;
  cursor: pointer;
}

.scroll-bar-track {
  position: relative;
  width: 150px;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: visible;
  cursor: pointer;
}

.scroll-bar-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: #9ca3af;
  transition: width 0.2s ease;
  border-radius: 2px;
}

.scroll-bar-marker {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 8px;
  height: 8px;
  background: #ffffff;
  border: 2px solid #9ca3af;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 5;
}

.scroll-bar-marker.marker-active {
  background: #6b7280;
  border-color: #6b7280;
  width: 10px;
  height: 10px;
}

.scroll-bar-handle {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  background: #6b7280;
  border: 2px solid #ffffff;
  border-radius: 50%;
  cursor: grab;
  transition: all 0.2s ease;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.scroll-bar-handle:hover {
  transform: translate(-50%, -50%) scale(1.1);
  background: #4b5563;
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.scroll-bar-handle.handle-active {
  cursor: grabbing;
  transform: translate(-50%, -50%) scale(1.05);
}
</style>
