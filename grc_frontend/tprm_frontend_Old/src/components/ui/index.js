// Basic UI Components for Contract Module

// Card Components
export const Card = {
  name: 'Card',
  template: `
    <div class="rounded-lg border bg-card text-card-foreground shadow-sm">
      <slot />
    </div>
  `
}

export const CardHeader = {
  name: 'CardHeader',
  template: `
    <div class="flex flex-col space-y-1.5 p-6">
      <slot />
    </div>
  `
}

export const CardTitle = {
  name: 'CardTitle',
  template: `
    <h3 class="text-2xl font-semibold leading-none tracking-tight">
      <slot />
    </h3>
  `
}

export const CardDescription = {
  name: 'CardDescription',
  template: `
    <p class="text-sm text-muted-foreground">
      <slot />
    </p>
  `
}

export const CardContent = {
  name: 'CardContent',
  template: `
    <div class="p-6 pt-0">
      <slot />
    </div>
  `
}

export const CardFooter = {
  name: 'CardFooter',
  template: `
    <div class="flex items-center p-6 pt-0">
      <slot />
    </div>
  `
}

// Button Component
export const Button = {
  name: 'Button',
  props: {
    variant: {
      type: String,
      default: 'default'
    },
    size: {
      type: String,
      default: 'default'
    },
    disabled: {
      type: Boolean,
      default: false
    },
    // Ensure buttons don't act as implicit form submits
    type: {
      type: String,
      default: 'button'
    }
  },
  computed: {
    buttonClasses() {
      const baseClasses = 'inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50'
      
      const variants = {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline'
      }
      
      const sizes = {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10'
      }
      
      return [
        baseClasses,
        variants[this.variant] || variants.default,
        sizes[this.size] || sizes.default
      ].join(' ')
    }
  },
  template: `
    <button 
      :class="buttonClasses" 
      :disabled="disabled"
      :type="type"
      @click="$emit('click', $event)"
    >
      <slot />
    </button>
  `
}

// Badge Component
export const Badge = {
  name: 'Badge',
  props: {
    variant: {
      type: String,
      default: 'default'
    }
  },
  computed: {
    badgeClasses() {
      const baseClasses = 'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'
      
      const variants = {
        default: 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
        secondary: 'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
        destructive: 'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
        outline: 'text-foreground'
      }
      
      return [
        baseClasses,
        variants[this.variant] || variants.default
      ].join(' ')
    }
  },
  template: `
    <div :class="badgeClasses">
      <slot />
    </div>
  `
}

// Input Component
export const Input = {
  name: 'Input',
  props: {
    type: {
      type: String,
      default: 'text'
    },
    placeholder: String,
    disabled: Boolean,
    modelValue: [String, Number]
  },
  emits: ['update:modelValue'],
  template: `
    <input
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
      class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
    />
  `
}

// Label Component
export const Label = {
  name: 'Label',
  template: `
    <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
      <slot />
    </label>
  `
}

// Select Components
export const Select = {
  name: 'Select',
  props: {
    modelValue: [String, Number],
    placeholder: String
  },
  emits: ['update:modelValue'],
  template: `
    <select
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
      class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
    >
      <option value="" v-if="placeholder">{{ placeholder }}</option>
      <slot />
    </select>
  `
}

export const SelectTrigger = {
  name: 'SelectTrigger',
  template: `
    <div class="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50">
      <slot />
    </div>
  `
}

export const SelectValue = {
  name: 'SelectValue',
  template: `<span><slot /></span>`
}

export const SelectContent = {
  name: 'SelectContent',
  template: `
    <div class="relative z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md">
      <slot />
    </div>
  `
}

export const SelectItem = {
  name: 'SelectItem',
  props: {
    value: [String, Number]
  },
  template: `
    <option :value="value">
      <slot />
    </option>
  `
}

// Textarea Component
export const Textarea = {
  name: 'Textarea',
  props: {
    placeholder: String,
    disabled: Boolean,
    modelValue: String,
    rows: {
      type: Number,
      default: 3
    }
  },
  emits: ['update:modelValue'],
  template: `
    <textarea
      :placeholder="placeholder"
      :disabled="disabled"
      :rows="rows"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
      class="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
    />
  `
}

// Dialog Components
export const Dialog = {
  name: 'Dialog',
  props: {
    open: Boolean
  },
  emits: ['close'],
  template: `
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="fixed inset-0 bg-background/80 backdrop-blur-sm" @click="$emit('close')"></div>
      <slot />
    </div>
  `
}

export const DialogContent = {
  name: 'DialogContent',
  template: `
    <div class="relative z-50 grid w-full max-w-lg gap-4 border bg-background p-6 shadow-lg sm:rounded-lg">
      <slot />
    </div>
  `
}

export const DialogHeader = {
  name: 'DialogHeader',
  template: `
    <div class="flex flex-col space-y-1.5 text-center sm:text-left">
      <slot />
    </div>
  `
}

export const DialogTitle = {
  name: 'DialogTitle',
  template: `
    <h2 class="text-lg font-semibold leading-none tracking-tight">
      <slot />
    </h2>
  `
}

export const DialogDescription = {
  name: 'DialogDescription',
  template: `
    <p class="text-sm text-muted-foreground">
      <slot />
    </p>
  `
}

export const DialogFooter = {
  name: 'DialogFooter',
  template: `
    <div class="flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2">
      <slot />
    </div>
  `
}

// Tabs Components
export const Tabs = {
  name: 'Tabs',
  props: {
    modelValue: String,
    defaultValue: String
  },
  emits: ['update:modelValue'],
  data() {
    return {
      activeTab: this.modelValue || this.defaultValue || ''
    }
  },
  watch: {
    modelValue(newValue) {
      this.activeTab = newValue
    },
    activeTab(newValue) {
      this.$emit('update:modelValue', newValue)
    }
  },
  provide() {
    return {
      activeTab: () => this.activeTab,
      setActiveTab: (value) => {
        this.activeTab = value
      }
    }
  },
  template: `
    <div class="w-full">
      <slot />
    </div>
  `
}

export const TabsList = {
  name: 'TabsList',
  template: `
    <div class="inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground">
      <slot />
    </div>
  `
}

export const TabsTrigger = {
  name: 'TabsTrigger',
  props: {
    value: String
  },
  inject: ['activeTab', 'setActiveTab'],
  computed: {
    isActive() {
      return this.activeTab() === this.value
    }
  },
  template: `
    <button
      @click="setActiveTab(value)"
      :class="[
        'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
        isActive ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
      ]"
    >
      <slot />
    </button>
  `
}

export const TabsContent = {
  name: 'TabsContent',
  props: {
    value: String
  },
  inject: ['activeTab'],
  computed: {
    isActive() {
      return this.activeTab() === this.value
    }
  },
  template: `
    <div v-if="isActive" class="mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
      <slot />
    </div>
  `
}

// Table Components
export const Table = {
  name: 'Table',
  template: `
    <div class="relative w-full overflow-auto">
      <table class="w-full caption-bottom text-sm">
        <slot />
      </table>
    </div>
  `
}

export const TableHeader = {
  name: 'TableHeader',
  template: `
    <thead class="[&_tr]:border-b">
      <slot />
    </thead>
  `
}

export const TableBody = {
  name: 'TableBody',
  template: `
    <tbody class="[&_tr:last-child]:border-0">
      <slot />
    </tbody>
  `
}

export const TableFooter = {
  name: 'TableFooter',
  template: `
    <tfoot class="bg-primary font-medium text-primary-foreground">
      <slot />
    </tfoot>
  `
}

export const TableHead = {
  name: 'TableHead',
  template: `
    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">
      <slot />
    </th>
  `
}

export const TableRow = {
  name: 'TableRow',
  template: `
    <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
      <slot />
    </tr>
  `
}

export const TableCell = {
  name: 'TableCell',
  template: `
    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
      <slot />
    </td>
  `
}

// Checkbox Component
export const Checkbox = {
  name: 'Checkbox',
  props: {
    checked: Boolean,
    disabled: Boolean,
    id: String
  },
  emits: ['update:checked'],
  computed: {
    checkboxClasses() {
      return [
        'peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
        this.checked ? 'data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground' : ''
      ].join(' ')
    }
  },
  template: `
    <input
      type="checkbox"
      :id="id"
      :checked="checked"
      :disabled="disabled"
      @change="$emit('update:checked', $event.target.checked)"
      :class="checkboxClasses"
      class="peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground"
    />
  `
}

// Separator Component
export const Separator = {
  name: 'Separator',
  props: {
    orientation: {
      type: String,
      default: 'horizontal'
    }
  },
  computed: {
    separatorClasses() {
      return this.orientation === 'horizontal' 
        ? 'h-[1px] w-full bg-border'
        : 'h-full w-[1px] bg-border'
    }
  },
  template: `
    <div :class="separatorClasses"></div>
  `
}

// Progress Component
export const Progress = {
  name: 'Progress',
  props: {
    value: {
      type: Number,
      default: 0
    },
    max: {
      type: Number,
      default: 100
    }
  },
  computed: {
    percentage() {
      return Math.min(Math.max((this.value / this.max) * 100, 0), 100)
    }
  },
  template: `
    <div class="relative h-4 w-full overflow-hidden rounded-full bg-secondary">
      <div 
        class="h-full w-full flex-1 bg-primary transition-all" 
        :style="{ transform: \`translateX(-\${100 - percentage}%)\` }"
      ></div>
    </div>
  `
}