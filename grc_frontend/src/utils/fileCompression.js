/**
 * File Compression Utilities
 * 
 * Compresses files on the client-side before upload to reduce bandwidth usage.
 * Uses pako library for gzip compression in the browser.
 */

// Import pako for gzip compression (will fallback gracefully if not available)
import pako from 'pako';

/**
 * Determines if a file should be compressed before upload.
 * 
 * @param {File} file - The file to check
 * @returns {boolean} True if file should be compressed
 */
export const shouldCompressFile = (file) => {
  // Skip compression for small files (overhead not worth it)
  if (file.size < 100 * 1024) return false; // 100KB threshold

  // Skip already compressed formats
  const compressedFormats = ['.zip', '.gz', '.jpg', '.jpeg', '.png', '.gif'];
  const fileName = file.name.toLowerCase();
  
  if (compressedFormats.some(ext => fileName.endsWith(ext))) {
    return false;
  }

  // Compress PDFs, DOCX, TXT, CSV, XLSX (compress very well)
  const compressibleFormats = ['.pdf', '.docx', '.doc', '.txt', '.csv', '.xlsx', '.xls'];
  return compressibleFormats.some(ext => fileName.endsWith(ext));
};

/**
 * Compresses a file using gzip compression.
 * 
 * @param {File} file - The file to compress
 * @returns {Promise<Object>} Object containing compressedFile, originalSize, compressedSize, compressionRatio
 */
export const compressFile = async (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const arrayBuffer = e.target.result;
        const uint8Array = new Uint8Array(arrayBuffer);

        // Check if pako is available
        if (!pako) {
          console.warn('⚠️  pako library not available. File compression disabled.');
          // Return original file if pako is not available
          resolve({
            compressedFile: file,
            originalSize: arrayBuffer.byteLength,
            compressedSize: arrayBuffer.byteLength,
            compressionRatio: 0
          });
          return;
        }

        // Compress using gzip level 6 (balanced performance/compression)
        const compressed = pako.gzip(uint8Array, { level: 6 });

        // Create new File object with .gz extension
        const compressedFile = new File(
          [compressed],
          `${file.name}.gz`,
          { type: 'application/gzip' }
        );

        const compressionRatio = ((1 - compressed.length / arrayBuffer.byteLength) * 100).toFixed(1);

        console.log(`✅ Compressed ${file.name}: ${compressionRatio}% reduction`);
        console.log(`   Original: ${(arrayBuffer.byteLength / 1024).toFixed(1)} KB`);
        console.log(`   Compressed: ${(compressed.length / 1024).toFixed(1)} KB`);

        resolve({
          compressedFile,
          originalSize: arrayBuffer.byteLength,
          compressedSize: compressed.length,
          compressionRatio: parseFloat(compressionRatio)
        });
      } catch (error) {
        console.error('❌ Compression error:', error);
        reject(error);
      }
    };

    reader.onerror = (error) => {
      console.error('❌ FileReader error:', error);
      reject(error);
    };

    reader.readAsArrayBuffer(file);
  });
};

