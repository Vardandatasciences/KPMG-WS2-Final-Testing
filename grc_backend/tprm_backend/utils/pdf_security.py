import html

def sanitize_for_pdf(text):
    """
    Sanitize text to prevent SSRF and other tag-based vulnerabilities in reportlab.
    Escapes HTML special characters to prevent rendering of tags like <img>.
    
    Args:
        text (str): The text to sanitize.
        
    Returns:
        str: The sanitized text.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    
    # Escape HTML tags (<, >, &, ", ') to prevent SSRF via <img> tags or other malicious input
    # reportlab.platypus.Paragraph supports XML entities like &lt; and &gt;
    return html.escape(text)
