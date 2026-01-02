<template>
  <div class="p-6 max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">Accordion Component Demo</h1>
    
    <div class="space-y-6">
      <!-- Basic Accordion -->
      <div>
        <h2 class="text-xl font-semibold mb-3">Basic Accordion</h2>
        <Accordion>
          <AccordionItem value="item-1">
            <AccordionTrigger value="item-1">
              What is Vue.js?
            </AccordionTrigger>
            <AccordionContent value="item-1">
              Vue.js is a progressive JavaScript framework for building user interfaces. 
              It is designed to be incrementally adoptable and can be used to build 
              single-page applications or complex web applications.
            </AccordionContent>
          </AccordionItem>
          
          <AccordionItem value="item-2">
            <AccordionTrigger value="item-2">
              Why choose Vue.js?
            </AccordionTrigger>
            <AccordionContent value="item-2">
              Vue.js offers excellent performance, small bundle size, and a gentle 
              learning curve. It provides reactive data binding, component-based 
              architecture, and excellent tooling support.
            </AccordionContent>
          </AccordionItem>
          
          <AccordionItem value="item-3">
            <AccordionTrigger value="item-3">
              How does Vue.js compare to React?
            </AccordionTrigger>
            <AccordionContent value="item-3">
              Vue.js and React are both excellent frameworks. Vue.js is often praised 
              for its simplicity and ease of learning, while React has a larger ecosystem 
              and community. Both are great choices for modern web development.
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>

      <!-- Accordion with Custom Styling -->
      <div>
        <h2 class="text-xl font-semibold mb-3">Accordion with Custom Styling</h2>
        <Accordion>
          <AccordionItem value="custom-1" class="border-2 border-blue-200 rounded-lg mb-2">
            <AccordionTrigger value="custom-1" class="px-4 py-3 bg-blue-50 hover:bg-blue-100">
              <span class="flex items-center gap-2">
                <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
                Custom Styled Item 1
              </span>
            </AccordionTrigger>
            <AccordionContent value="custom-1" class="px-4">
              <p class="text-gray-700 leading-relaxed">
                This accordion item has custom styling with blue borders, 
                background colors, and custom spacing. The content area 
                also has custom padding for better visual hierarchy.
              </p>
            </AccordionContent>
          </AccordionItem>
          
          <AccordionItem value="custom-2" class="border-2 border-green-200 rounded-lg mb-2">
            <AccordionTrigger value="custom-2" class="px-4 py-3 bg-green-50 hover:bg-green-100">
              <span class="flex items-center gap-2">
                <span class="w-2 h-2 bg-green-500 rounded-full"></span>
                Custom Styled Item 2
              </span>
            </AccordionTrigger>
            <AccordionContent value="custom-2" class="px-4">
              <p class="text-gray-700 leading-relaxed">
                Another custom styled item with green theme. Notice how 
                the hover effects and transitions work smoothly with 
                the custom styling applied.
              </p>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>

      <!-- Interactive Demo -->
      <div>
        <h2 class="text-xl font-semibold mb-3">Interactive Demo</h2>
        <div class="bg-gray-50 p-4 rounded-lg">
          <p class="text-sm text-gray-600 mb-3">
            Currently open items: {{ Array.from(accordion.openItems).join(', ') || 'None' }}
          </p>
          <div class="flex gap-2">
            <Button @click="openAll" variant="outline" size="sm">Open All</Button>
            <Button @click="closeAll" variant="outline" size="sm">Close All</Button>
          </div>
        </div>
        
        <Accordion ref="accordionRef">
          <AccordionItem value="demo-1">
            <AccordionTrigger value="demo-1">
              Interactive Item 1
            </AccordionTrigger>
            <AccordionContent value="demo-1">
              <p>This item can be controlled programmatically.</p>
            </AccordionContent>
          </AccordionItem>
          
          <AccordionItem value="demo-2">
            <AccordionTrigger value="demo-2">
              Interactive Item 2
            </AccordionTrigger>
            <AccordionContent value="demo-2">
              <p>Try using the buttons above to control all items.</p>
            </AccordionContent>
          </AccordionItem>
          
          <AccordionItem value="demo-3">
            <AccordionTrigger value="demo-3">
              Interactive Item 3
            </AccordionTrigger>
            <AccordionContent value="demo-3">
              <p>You can also click individual items to toggle them.</p>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { 
  Accordion, 
  AccordionItem, 
  AccordionTrigger, 
  AccordionContent,
  Button 
} from '@/components/ui_contract'

const accordion = inject('accordion')

const openAll = () => {
  accordion.openItems.value = new Set(['demo-1', 'demo-2', 'demo-3'])
}

const closeAll = () => {
  accordion.openItems.value.clear()
}
</script>
