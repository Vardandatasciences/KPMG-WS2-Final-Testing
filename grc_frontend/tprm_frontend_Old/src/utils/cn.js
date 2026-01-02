import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs) {
  return twMerge(clsx(inputs))
}

// Utility function for conditional classes
function conditionalClass(condition, trueClass, falseClass = '') {
  return condition ? trueClass : falseClass
}

// Utility function for combining classes
function combineClasses(...classes) {
  return classes.filter(Boolean).join(' ')
}

export {
  cn,
  conditionalClass,
  combineClasses
}
