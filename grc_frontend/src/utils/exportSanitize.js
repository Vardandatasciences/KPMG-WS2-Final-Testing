/**
 * Centralized export sanitization (CSV formula injection, download filenames).
 * Align with grc_backend/grc/utils/csv_security.py where possible.
 */

const ASCII_FORMULA_START = new Set(['=', '+', '-', '@'])
const FULLWIDTH_FORMULA_START = new Set(['\uFF1D', '\uFF0B', '\uFF0D', '\uFF20'])

/**
 * @param {unknown} value
 * @returns {string|number|boolean|unknown}
 */
export function sanitizeExportCellValue (value) {
  if (value === null || value === undefined) return ''
  if (typeof value !== 'string' && typeof value !== 'number' && typeof value !== 'boolean') {
    return value
  }
  let s = String(value)
  s = s.split('\r').join(' ').split('\n').join(' ').split('\x0b').join(' ').split('\f').join(' ')
  s = s.split('\0').join('')
  const trimmed = s.trimStart()
  if (!trimmed) return s
  const first = trimmed[0]
  if (ASCII_FORMULA_START.has(first) || FULLWIDTH_FORMULA_START.has(first)) {
    return "'" + s
  }
  return s
}

/**
 * Safe filename segment for Content-Disposition / export basename (no path, restricted charset).
 * @param {unknown} name
 * @param {{ defaultName?: string }} [opts]
 */
export function sanitizeExportDownloadFileName (name, opts = {}) {
  const defaultName = opts.defaultName || 'download'
  let s = String(name ?? '')
    .split('\r').join('')
    .split('\n').join('')
    .split('\0').join('')
  s = s.replace(/[/\\]/g, '_')
  s = s.replace(/[^a-zA-Z0-9._-]+/g, '_').replace(/^[._-]+|[._-]+$/g, '')
  if (s.length > 200) s = s.slice(0, 200).replace(/[._-]+$/, '')
  return s || defaultName
}
