"""
File Compression Utilities

Handles server-side decompression of files uploaded from the client.
Client compresses files using gzip before upload to reduce bandwidth.
"""
import gzip
import os
from typing import Tuple, Optional, Dict


def decompress_if_needed(file_path: str) -> Tuple[str, bool, Optional[Dict]]:
    """
    Decompress file if it's gzipped.
    
    Args:
        file_path: Path to the file (may have .gz extension)
    
    Returns:
        Tuple of (decompressed_path, was_compressed, compression_stats)
        - decompressed_path: Path to the decompressed file (original path if not compressed)
        - was_compressed: Boolean indicating if file was compressed
        - compression_stats: Dict with compression statistics if compressed, None otherwise
    """
    if not file_path.endswith('.gz'):
        return file_path, False, None

    # Read compressed file
    try:
        with open(file_path, 'rb') as f_in:
            compressed_data = f_in.read()
            compressed_size = len(compressed_data)
    except Exception as e:
        print(f"⚠️  Error reading compressed file {file_path}: {e}")
        return file_path, False, None

    # Decompress
    try:
        decompressed_data = gzip.decompress(compressed_data)
        decompressed_size = len(decompressed_data)
    except gzip.BadGzipFile:
        # Not actually gzipped, return as-is
        print(f"⚠️  File has .gz extension but is not gzipped: {file_path}")
        return file_path, False, None
    except Exception as e:
        print(f"⚠️  Error decompressing file {file_path}: {e}")
        return file_path, False, None

    # Write decompressed file (remove .gz extension)
    decompressed_path = file_path[:-3]  # Remove .gz
    try:
        with open(decompressed_path, 'wb') as f_out:
            f_out.write(decompressed_data)
    except Exception as e:
        print(f"⚠️  Error writing decompressed file {decompressed_path}: {e}")
        return file_path, False, None

    # Calculate stats
    compression_stats = {
        'original_size': decompressed_size,
        'compressed_size': compressed_size,
        'ratio': round((1 - compressed_size / decompressed_size) * 100, 1),
        'bandwidth_saved_kb': round((decompressed_size - compressed_size) / 1024, 1)
    }

    # Clean up compressed file
    try:
        os.remove(file_path)
        print(f"✅ Decompressed upload: {compression_stats['ratio']}% reduction")
        print(f"   Bandwidth saved: {compression_stats['bandwidth_saved_kb']} KB")
    except Exception as e:
        print(f"⚠️  Warning: Could not remove compressed file {file_path}: {e}")

    return decompressed_path, True, compression_stats



