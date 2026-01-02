<template>
  <div class="rich-response-editor" :class="{ 'is-disabled': disabled }">
    <div class="editor-toolbar">
      <button
        type="button"
        class="toolbar-button"
        :class="{ active: editor?.isActive('bold') }"
        @click="toggleMark('bold')"
        :disabled="!editor || disabled"
      >
        <Bold class="icon" />
      </button>
      <button
        type="button"
        class="toolbar-button"
        :class="{ active: editor?.isActive('italic') }"
        @click="toggleMark('italic')"
        :disabled="!editor || disabled"
      >
        <Italic class="icon" />
      </button>
      <button
        type="button"
        class="toolbar-button"
        :class="{ active: editor?.isActive('underline') }"
        @click="toggleUnderline"
        :disabled="!editor || disabled"
      >
        <UnderlineIcon class="icon" />
      </button>
      <button
        type="button"
        class="toolbar-button"
        :class="{ active: editor?.isActive('bulletList') }"
        @click="toggleBulletList"
        :disabled="!editor || disabled"
      >
        <List class="icon" />
      </button>
      <button
        type="button"
        class="toolbar-button"
        :class="{ active: editor?.isActive('orderedList') }"
        @click="toggleOrderedList"
        :disabled="!editor || disabled"
      >
        <ListOrdered class="icon" />
      </button>
      <button
        type="button"
        class="toolbar-button"
        @click="setTextAlign('left')"
        :disabled="!editor || disabled"
      >
        <AlignLeft class="icon" />
      </button>
      <button
        type="button"
        class="toolbar-button"
        @click="setTextAlign('center')"
        :disabled="!editor || disabled"
      >
        <AlignCenter class="icon" />
      </button>
      <button
        type="button"
        class="toolbar-button"
        @click="setTextAlign('right')"
        :disabled="!editor || disabled"
      >
        <AlignRight class="icon" />
      </button>
      <button
        type="button"
        class="toolbar-button"
        @click="insertTable"
        :disabled="!editor || disabled"
      >
        <TableIcon class="icon" />
      </button>
      <div class="toolbar-divider" />
      <button
        type="button"
        class="toolbar-button"
        @click="triggerImageUpload"
        :disabled="disabled || uploading"
      >
        <ImageIcon class="icon" />
        <span class="sr-only">Insert image</span>
      </button>
      <button
        type="button"
        class="toolbar-button"
        @click="triggerFileUpload"
        :disabled="disabled || uploading"
      >
        <Paperclip class="icon" />
        <span class="sr-only">Attach file</span>
      </button>
    </div>

    <EditorContent
      v-if="editor"
      class="editor-content"
      :editor="editor"
    />

    <div v-if="attachments.length" class="attachment-list">
      <div
        v-for="attachment in attachments"
        :key="attachment.id || attachment.url"
        class="attachment-item"
      >
        <div class="attachment-info">
          <Paperclip class="icon attachment-icon" />
          <div>
            <p class="attachment-name">
              {{ attachment.originalFilename || attachment.fileName }}
            </p>
            <p class="attachment-meta">
              {{ formatSize(attachment.fileSize) }}
              <span v-if="attachment.contentType">• {{ attachment.contentType }}</span>
            </p>
          </div>
        </div>
        <div class="attachment-actions">
          <button
            type="button"
            class="attachment-button"
            @click="downloadAttachment(attachment)"
          >
            <Download class="icon" />
            Download
          </button>
          <button
            type="button"
            class="attachment-button destructive"
            @click="removeAttachment(attachment)"
            :disabled="disabled"
          >
            <Trash2 class="icon" />
            Remove
          </button>
        </div>
      </div>
    </div>

    <p v-if="uploading" class="upload-indicator">Uploading attachment...</p>

    <input
      ref="imageInput"
      type="file"
      accept="image/*"
      class="hidden-input"
      @change="handleImageSelection"
    />
    <input
      ref="fileInput"
      type="file"
      class="hidden-input"
      multiple
      @change="handleFileSelection"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Underline from '@tiptap/extension-underline'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import TextAlign from '@tiptap/extension-text-align'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'

import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Bold,
  Download,
  Image as ImageIcon,
  Italic,
  List,
  ListOrdered,
  Paperclip,
  Table as TableIcon,
  Trash2,
  Underline as UnderlineIcon
} from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  placeholder: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  uploadAttachment: {
    type: Function,
    required: true
  }
})

const emit = defineEmits([
  'update:modelValue',
  'blur',
  'attachment-uploaded',
  'attachment-removed',
  'error'
])

const createEmptyValue = () => ({
  htmlContent: '',
  attachments: []
})

const normalizeValue = (value) => {
  if (!value) {
    return createEmptyValue()
  }

  if (typeof value === 'string') {
    return {
      htmlContent: value,
      attachments: []
    }
  }

  const attachments = Array.isArray(value.attachments)
    ? value.attachments.map((attachment) => ({ ...attachment }))
    : []

  return {
    ...value,
    htmlContent: value.htmlContent || value.text || '',
    attachments
  }
}

const cloneValue = (value) => JSON.parse(JSON.stringify(value))

const internalValue = ref(normalizeValue(props.modelValue))
const uploading = ref(false)
const imageInput = ref(null)
const fileInput = ref(null)

const editor = useEditor({
  content: internalValue.value.htmlContent,
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [2, 3, 4]
      }
    }),
    Underline,
    Placeholder.configure({
      placeholder: props.placeholder || 'Type your response here...',
      includeChildren: true
    }),
    Link.configure({
      openOnClick: true,
      autolink: true,
      HTMLAttributes: {
        rel: 'noopener noreferrer nofollow',
        target: '_blank',
        class: 'editor-link'
      }
    }),
    Image.configure({
      inline: false,
      allowBase64: false,
      HTMLAttributes: {
        class: 'editor-image'
      }
    }),
    TextAlign.configure({
      types: ['heading', 'paragraph'],
      defaultAlignment: 'left'
    }),
    Table.configure({
      resizable: true,
      allowTableNodeSelection: true
    }),
    TableRow,
    TableHeader,
    TableCell
  ],
  editable: !props.disabled,
  onUpdate: ({ editor }) => {
    const htmlContent = editor.getHTML()
    const currentValue = normalizeValue(internalValue.value)
    
    // Extract image URLs from HTML to ensure they're tracked in attachments
    const imageUrls = new Set()
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = htmlContent
    const images = tempDiv.querySelectorAll('img[src]')
    images.forEach(img => {
      const src = img.getAttribute('src')
      if (src && !src.startsWith('data:')) {
        imageUrls.add(src)
      }
    })
    
    // Ensure all image URLs in HTML are tracked in attachments
    const existingAttachments = currentValue.attachments || []
    const trackedUrls = new Set(existingAttachments.map(a => a.url).filter(Boolean))
    
    // Add any images in HTML that aren't tracked yet
    const missingImages = Array.from(imageUrls).filter(url => !trackedUrls.has(url))
    if (missingImages.length > 0) {
      const newAttachments = missingImages.map(url => ({
        id: `img-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        url: url,
        fileName: url.split('/').pop() || 'image',
        originalFilename: url.split('/').pop() || 'image',
        contentType: 'image/*',
        isImage: true,
        uploadedAt: new Date().toISOString()
      }))
      
      emitUpdate({ 
        htmlContent,
        attachments: [...existingAttachments, ...newAttachments]
      })
    } else {
      emitUpdate({ htmlContent })
    }
  },
  onBlur: () => emit('blur')
})

const attachments = computed(() => {
  const value = normalizeValue(internalValue.value)
  return Array.isArray(value.attachments) ? value.attachments : []
})

watch(
  () => props.modelValue,
  (newValue) => {
    const normalized = normalizeValue(newValue)
    const current = normalizeValue(internalValue.value)

    const htmlChanged = normalized.htmlContent !== current.htmlContent
    const attachmentsChanged = JSON.stringify(normalized.attachments) !== JSON.stringify(current.attachments)

    if (htmlChanged || attachmentsChanged) {
      internalValue.value = normalized
      if (editor.value && htmlChanged) {
        const currentHtml = editor.value.getHTML()
        if (currentHtml !== normalized.htmlContent) {
          editor.value.commands.setContent(normalized.htmlContent || '<p></p>', false)
        }
      }
    }
  },
  { deep: true }
)

watch(
  () => props.disabled,
  (isDisabled) => {
    if (editor.value) {
      editor.value.setEditable(!isDisabled)
    }
  }
)

const emitUpdate = (patch = {}) => {
  const current = normalizeValue(internalValue.value)
  const next = {
    ...current,
    ...patch
  }

  if ('attachments' in patch && Array.isArray(patch.attachments)) {
    next.attachments = patch.attachments
  } else if (!Array.isArray(next.attachments)) {
    next.attachments = []
  }

  console.log('RichResponseEditor: emitUpdate', {
    patch,
    currentAttachments: current.attachments?.length || 0,
    nextAttachments: next.attachments?.length || 0,
    hasHtmlContent: !!next.htmlContent,
    htmlContentLength: next.htmlContent?.length || 0
  })

  internalValue.value = next
  const cloned = cloneValue(next)
  console.log('RichResponseEditor: Emitting update:modelValue', {
    hasHtmlContent: !!cloned.htmlContent,
    htmlContentLength: cloned.htmlContent?.length || 0,
    attachmentsCount: cloned.attachments?.length || 0,
    attachments: cloned.attachments
  })
  emit('update:modelValue', cloned)
}

const sanitizeAttachment = (attachment = {}) => {
  const fallbackId = Math.random().toString(36).slice(2)
  return {
    id: attachment.id !== undefined ? String(attachment.id) : (attachment.s3_file_id ? String(attachment.s3_file_id) : fallbackId),
    url: attachment.url || attachment.document_url || attachment.attachmentUrl || '',
    key: attachment.key || attachment.s3_key,
    fileName: attachment.fileName || attachment.storedName || attachment.originalFilename || attachment.name || 'attachment',
    originalFilename: attachment.originalFilename || attachment.fileName || attachment.storedName || attachment.name || 'attachment',
    fileSize: attachment.fileSize || attachment.size || null,
    contentType: attachment.contentType || attachment.mimeType || '',
    uploadedAt: attachment.uploadedAt || new Date().toISOString(),
    isImage: attachment.isImage ?? Boolean((attachment.contentType || '').startsWith('image/')),
    criteriaId: attachment.criteriaId ? String(attachment.criteriaId) : undefined,
    responseId: attachment.responseId || undefined
  }
}

const addAttachment = (attachment) => {
  console.log('RichResponseEditor: addAttachment called', attachment)
  const sanitized = sanitizeAttachment(attachment)
  console.log('RichResponseEditor: sanitized attachment', sanitized)
  
  if (!sanitized.url) {
    console.warn('RichResponseEditor: Cannot add attachment - missing URL', sanitized)
    return
  }

  const existing = attachments.value || []
  const alreadyExists = existing.some((item) => item.id && sanitized.id && item.id === sanitized.id)

  if (alreadyExists) {
    console.log('RichResponseEditor: Attachment already exists, skipping', sanitized.id)
    return
  }

  const newAttachments = [...existing, sanitized]
  console.log('RichResponseEditor: Updating attachments', {
    existingCount: existing.length,
    newCount: newAttachments.length,
    newAttachment: sanitized
  })

  emitUpdate({
    attachments: newAttachments
  })
  emit('attachment-uploaded', sanitized)
  
  console.log('RichResponseEditor: Attachment added successfully', {
    attachment: sanitized,
    totalAttachments: newAttachments.length
  })
}

const removeAttachment = (attachment) => {
  if (props.disabled) {
    return
  }

  const sanitized = sanitizeAttachment(attachment)
  const filtered = (attachments.value || []).filter((item) => item.id !== sanitized.id && item.url !== sanitized.url)
  emitUpdate({ attachments: filtered })
  emit('attachment-removed', sanitized)
}

const toggleMark = (mark) => {
  if (!editor.value || props.disabled) {
    console.warn('RichResponseEditor: Cannot toggle mark - editor not ready or disabled', { mark, hasEditor: !!editor.value, disabled: props.disabled })
    return
  }
  console.log('RichResponseEditor: Toggling mark', mark)
  editor.value.chain().focus().toggleMark(mark).run()
}

const toggleUnderline = () => {
  if (!editor.value || props.disabled) {
    console.warn('RichResponseEditor: Cannot toggle underline - editor not ready or disabled')
    return
  }
  console.log('RichResponseEditor: Toggling underline')
  editor.value.chain().focus().toggleUnderline().run()
}

const toggleBulletList = () => {
  if (!editor.value || props.disabled) {
    console.warn('RichResponseEditor: Cannot toggle bullet list - editor not ready or disabled')
    return
  }
  console.log('RichResponseEditor: Toggling bullet list')
  editor.value.chain().focus().toggleBulletList().run()
}

const toggleOrderedList = () => {
  if (!editor.value || props.disabled) {
    console.warn('RichResponseEditor: Cannot toggle ordered list - editor not ready or disabled')
    return
  }
  console.log('RichResponseEditor: Toggling ordered list')
  editor.value.chain().focus().toggleOrderedList().run()
}

const setTextAlign = (alignment) => {
  if (!editor.value || props.disabled) {
    console.warn('RichResponseEditor: Cannot set text align - editor not ready or disabled', alignment)
    return
  }
  console.log('RichResponseEditor: Setting text align', alignment)
  editor.value.chain().focus().setTextAlign(alignment).run()
}

const insertTable = () => {
  if (!editor.value || props.disabled) {
    console.warn('RichResponseEditor: Cannot insert table - editor not ready or disabled')
    return
  }
  console.log('RichResponseEditor: Inserting table')
  editor.value
    .chain()
    .focus()
    .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
    .run()
}

const triggerImageUpload = () => {
  console.log('RichResponseEditor: triggerImageUpload called', {
    disabled: props.disabled,
    hasUploadAttachment: !!props.uploadAttachment,
    hasImageInput: !!imageInput.value,
    uploadAttachmentType: typeof props.uploadAttachment
  })
  
  if (props.disabled) {
    console.warn('RichResponseEditor: Cannot upload image - editor is disabled')
    return
  }
  
  if (!props.uploadAttachment || typeof props.uploadAttachment !== 'function') {
    console.error('RichResponseEditor: Cannot upload image - uploadAttachment prop is missing or not a function', {
      uploadAttachment: props.uploadAttachment,
      type: typeof props.uploadAttachment
    })
    return
  }
  
  if (!imageInput.value) {
    console.error('RichResponseEditor: Cannot upload image - image input ref is missing')
    return
  }
  
  console.log('RichResponseEditor: Triggering image file input click')
  imageInput.value.click()
}

const triggerFileUpload = () => {
  console.log('RichResponseEditor: triggerFileUpload called', {
    disabled: props.disabled,
    hasUploadAttachment: !!props.uploadAttachment,
    hasFileInput: !!fileInput.value,
    uploadAttachmentType: typeof props.uploadAttachment
  })
  
  if (props.disabled) {
    console.warn('RichResponseEditor: Cannot upload file - editor is disabled')
    return
  }
  
  if (!props.uploadAttachment || typeof props.uploadAttachment !== 'function') {
    console.error('RichResponseEditor: Cannot upload file - uploadAttachment prop is missing or not a function', {
      uploadAttachment: props.uploadAttachment,
      type: typeof props.uploadAttachment
    })
    return
  }
  
  if (!fileInput.value) {
    console.error('RichResponseEditor: Cannot upload file - file input ref is missing')
    return
  }
  
  console.log('RichResponseEditor: Triggering file input click')
  fileInput.value.click()
}

const handleImageSelection = async (event) => {
  console.log('RichResponseEditor: handleImageSelection called', event)
  const files = event.target.files
  console.log('RichResponseEditor: Files selected', {
    fileCount: files?.length || 0,
    files: files ? Array.from(files).map(f => ({ name: f.name, size: f.size, type: f.type })) : []
  })
  
  if (!files || !files.length) {
    console.warn('RichResponseEditor: No files selected in image input')
    return
  }

  const [file] = files
  console.log('RichResponseEditor: Processing image file', {
    name: file.name,
    size: file.size,
    type: file.type
  })
  
  event.target.value = ''

  try {
    await uploadFile(file, { type: 'image' })
  } catch (error) {
    console.error('RichResponseEditor: Error in handleImageSelection', error)
  }
}

const handleFileSelection = async (event) => {
  console.log('RichResponseEditor: handleFileSelection called', event)
  const files = event.target.files
  console.log('RichResponseEditor: Files selected', {
    fileCount: files?.length || 0,
    files: files ? Array.from(files).map(f => ({ name: f.name, size: f.size, type: f.type })) : []
  })
  
  if (!files || !files.length) {
    console.warn('RichResponseEditor: No files selected in file input')
    return
  }

  const uploads = Array.from(files).map((file) => {
    console.log('RichResponseEditor: Queuing file upload', {
      name: file.name,
      size: file.size,
      type: file.type
    })
    return uploadFile(file, { type: 'file' })
  })
  
  event.target.value = ''

  try {
    await Promise.all(uploads)
    console.log('RichResponseEditor: All file uploads completed')
  } catch (error) {
    console.error('RichResponseEditor: Error in handleFileSelection', error)
  }
}

const uploadFile = async (file, options = {}) => {
  if (!props.uploadAttachment || !file) {
    console.warn('RichResponseEditor: Cannot upload - missing uploadAttachment prop or file')
    return
  }

  console.log('RichResponseEditor: Starting file upload', {
    fileName: file.name,
    fileSize: file.size,
    fileType: file.type,
    options
  })

  uploading.value = true
  try {
    const attachment = await props.uploadAttachment(file, options)
    console.log('RichResponseEditor: Upload response received', attachment)
    
    if (!attachment || !attachment.url) {
      throw new Error('Upload did not return a valid attachment URL')
    }

    console.log('RichResponseEditor: Adding attachment to editor', attachment)
    addAttachment(attachment)

    if (options.type === 'image' && attachment.url && editor.value) {
      console.log('RichResponseEditor: Inserting image into editor', attachment.url)
      editor.value
        .chain()
        .focus()
        .setImage({
          src: attachment.url,
          alt: attachment.originalFilename || attachment.fileName || file.name
        })
        .run()
    } else if (options.type === 'file' && editor.value) {
      console.log('RichResponseEditor: Inserting file link into editor', attachment.url)
      // Insert a reference link where the cursor is positioned
      editor.value
        .chain()
        .focus()
        .extendMarkRange('link')
        .setLink({
          href: attachment.url,
          target: '_blank',
          rel: 'noopener noreferrer'
        })
        .insertContent(attachment.originalFilename || attachment.fileName || file.name)
        .setTextSelection(editor.value.state.selection.to)
        .unsetLink()
        .run()
    }
    
    console.log('RichResponseEditor: Upload completed successfully', {
      attachment,
      currentAttachments: attachments.value.length
    })
  } catch (error) {
    console.error('RichResponseEditor: Attachment upload failed', error)
    emit('error', error)
  } finally {
    uploading.value = false
  }
}

const downloadAttachment = (attachment) => {
  if (!attachment || !attachment.url) return
  window.open(attachment.url, '_blank', 'noopener')
}

const formatSize = (size) => {
  if (!size || Number.isNaN(Number(size))) return '—'
  const bytes = Number(size)
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

onMounted(() => {
  console.log('RichResponseEditor: Component mounted', {
    hasUploadAttachment: !!props.uploadAttachment,
    uploadAttachmentType: typeof props.uploadAttachment,
    isFunction: typeof props.uploadAttachment === 'function',
    disabled: props.disabled,
    hasModelValue: !!props.modelValue,
    hasEditor: !!editor.value,
    editorType: typeof editor.value
  })
  
  if (!props.uploadAttachment) {
    console.error('RichResponseEditor: CRITICAL - uploadAttachment prop is missing on mount!')
  } else if (typeof props.uploadAttachment !== 'function') {
    console.error('RichResponseEditor: CRITICAL - uploadAttachment prop is not a function!', {
      type: typeof props.uploadAttachment,
      value: props.uploadAttachment
    })
  } else {
    console.log('RichResponseEditor: uploadAttachment prop is valid function')
  }
  
  // Check if editor is initialized
  if (!editor.value) {
    console.error('RichResponseEditor: CRITICAL - Editor not initialized!')
  } else {
    console.log('RichResponseEditor: Editor initialized successfully', {
      isEditable: editor.value.isEditable,
      isEmpty: editor.value.isEmpty,
      contentLength: editor.value.getHTML().length
    })
  }
})

onBeforeUnmount(() => {
  if (editor.value) {
    editor.value.destroy()
  }
})
</script>

<style scoped>
.rich-response-editor {
  border: 1px solid #d1d5db;
  border-radius: 0.75rem;
  background-color: #ffffff;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.rich-response-editor:is(:focus-within) {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.rich-response-editor.is-disabled {
  background-color: #f9fafb;
  border-color: #e5e7eb;
  cursor: not-allowed;
  opacity: 0.85;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
}

.toolbar-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 0.5rem;
  border: none;
  background-color: transparent;
  color: #475569;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.15s ease;
}

.toolbar-button:hover {
  background-color: #e2e8f0;
  color: #1e293b;
}

.toolbar-button:active {
  transform: translateY(1px);
}

.toolbar-button.active {
  background-color: #2563eb;
  color: #ffffff;
}

.toolbar-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background-color: #cbd5f5;
  margin: 0 0.5rem;
}

.icon {
  width: 16px;
  height: 16px;
}

.editor-content {
  padding: 1rem 1.25rem;
  min-height: 200px;
  line-height: 1.6;
  font-size: 0.95rem;
  color: #0f172a;
}

.editor-content :deep(.ProseMirror) {
  outline: none;
  min-height: 200px;
  padding: 0.5rem;
}

.editor-content :deep(.ProseMirror:focus) {
  outline: none;
}

.editor-content :deep(.ProseMirror p) {
  margin: 0.5rem 0;
}

.editor-content :deep(.ProseMirror p:first-child) {
  margin-top: 0;
}

.editor-content :deep(.ProseMirror p:last-child) {
  margin-bottom: 0;
}

.editor-content :deep(p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  color: #94a3b8;
  float: left;
  height: 0;
  pointer-events: none;
}

.editor-content :deep(ul) {
  list-style: disc;
  margin-left: 1.25rem;
  padding-left: 0.75rem;
}

.editor-content :deep(ol) {
  list-style: decimal;
  margin-left: 1.25rem;
  padding-left: 0.75rem;
}

.editor-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  font-size: 0.9rem;
}

.editor-content :deep(th),
.editor-content :deep(td) {
  border: 1px solid #cbd5f5;
  padding: 0.5rem;
  text-align: left;
}

.editor-content :deep(.editor-link) {
  color: #2563eb;
  text-decoration: underline;
}

.editor-content :deep(.editor-image) {
  max-width: 100%;
  border-radius: 0.75rem;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
  margin: 1rem auto;
  display: block;
}

.attachment-list {
  border-top: 1px solid #e2e8f0;
  padding: 0.75rem 1.25rem;
  background-color: #f8fafc;
  display: grid;
  gap: 0.75rem;
}

.attachment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
  gap: 1rem;
}

.attachment-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.attachment-icon {
  color: #2563eb;
}

.attachment-name {
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.attachment-meta {
  font-size: 0.8rem;
  color: #64748b;
  margin: 0.125rem 0 0 0;
}

.attachment-actions {
  display: flex;
  gap: 0.5rem;
}

.attachment-button {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.35rem 0.7rem;
  border-radius: 0.6rem;
  border: 1px solid transparent;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
  background-color: #eef2ff;
  color: #3730a3;
}

.attachment-button .icon {
  width: 14px;
  height: 14px;
}

.attachment-button:hover {
  background-color: #4338ca;
  color: #ffffff;
}

.attachment-button.destructive {
  background-color: #fee2e2;
  color: #b91c1c;
}

.attachment-button.destructive:hover {
  background-color: #dc2626;
  color: #ffffff;
}

.upload-indicator {
  padding: 0.5rem 1.25rem 1rem 1.25rem;
  font-size: 0.85rem;
  color: #2563eb;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.hidden-input {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

@media (max-width: 640px) {
  .attachment-item {
    flex-direction: column;
    align-items: stretch;
  }

  .attachment-actions {
    justify-content: flex-end;
  }
}

/* Table styles for TipTap */
.ProseMirror table {
  border-collapse: collapse;
  table-layout: fixed;
  width: 100%;
  margin: 1rem 0;
  overflow: hidden;
}

.ProseMirror table td,
.ProseMirror table th {
  min-width: 1em;
  border: 1px solid #cbd5e1;
  padding: 0.5rem 0.75rem;
  vertical-align: top;
  box-sizing: border-box;
  position: relative;
}

.ProseMirror table th {
  font-weight: 600;
  text-align: left;
  background-color: #f1f5f9;
}

.ProseMirror table .selectedCell:after {
  z-index: 2;
  position: absolute;
  content: "";
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: rgba(200, 200, 255, 0.4);
  pointer-events: none;
}

.ProseMirror table .column-resize-handle {
  position: absolute;
  right: -2px;
  top: 0;
  bottom: -2px;
  width: 4px;
  background-color: #3b82f6;
  pointer-events: none;
}
</style>

