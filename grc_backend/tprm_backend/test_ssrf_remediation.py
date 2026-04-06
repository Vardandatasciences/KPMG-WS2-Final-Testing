import os
import sys
import io

# Add the project root and tprm_backend to sys.path
# Based on the workspace path: c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\tprm_backend
project_root = r"c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend\tprm_backend"
sys.path.append(project_root)

# Import the sanitization function
try:
    from utils.pdf_security import sanitize_for_pdf
    print("Successfully imported sanitize_for_pdf")
except ImportError as e:
    print(f"ImportError: {e}")
    # Try alternate path if needed
    sys.path.append(os.path.join(project_root, ".."))
    from tprm_backend.utils.pdf_security import sanitize_for_pdf
    print("Successfully imported sanitize_for_pdf (alternate path)")

def test_sanitization():
    test_cases = [
        ("Normal text", "Normal text"),
        ("Text with <bold> tags", "Text with &lt;bold&gt; tags"),
        ("<img src='http://attacker.com/leak' />", "&lt;img src='http://attacker.com/leak' /&gt;"),
        ("<script>alert(1)</script>", "&lt;script&gt;alert(1)&lt;/script&gt;"),
        ("Multiple <tags> and & signs", "Multiple &lt;tags&gt; and &amp; signs"),
    ]
    
    print("\nRunning test cases:")
    for input_text, expected_output in test_cases:
        actual_output = sanitize_for_pdf(input_text)
        if actual_output == expected_output:
            print(f"  [PASS] Input: {input_text}")
            print(f"         Output: {actual_output}")
        else:
            print(f"  [FAIL] Input: {input_text}")
            print(f"         Expected: {expected_output}")
            print(f"         Actual: {actual_output}")

    # Test reportlab rendering if available
    try:
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        
        styles = getSampleStyleSheet()
        payload = "<img src='http://attacker.com/leak' />"
        sanitized = sanitize_for_pdf(payload)
        
        print("\nTesting ReportLab Paragraph rendering:")
        try:
            # If unsanitized, this might work if the URL is valid, or fail if tags are malformed
            # BUT the goal is that it's rendered as literal text
            p = Paragraph(sanitized, styles['Normal'])
            print(f"  ReportLab successfully created Paragraph from sanitized input: {sanitized}")
            
            # Note: We can't easily check for outgoing requests here without a listener,
            # but we can verify it doesn't fail parsing.
        except Exception as e:
            print(f"  ReportLab FAILED to parse sanitized input: {e}")
            
    except ImportError:
        print("\nReportLab not found in this environment, skipping rendering test.")

if __name__ == "__main__":
    test_sanitization()
