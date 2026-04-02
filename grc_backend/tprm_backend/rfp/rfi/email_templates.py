"""
Email templates for RFI invitations
"""


def generate_rfi_rich_html_email(invitation, rfi_data):
    """
    Generate rich HTML email body for RFI invitation with professional styling
    """
    from django.conf import settings
    from django.utils.html import escape

    deadline = escape(str(rfi_data.get('deadline', 'TBD')))
    vendor_name = escape(invitation.get('vendor_name', 'Contact at ' + invitation.get('company_name', 'Vendor')))
    company_name = escape(invitation.get('company_name', 'Vendor Company'))
    vendor_email = escape(invitation.get('vendor_email', 'contact@vendor.com'))
    invitation_url = escape(invitation.get('invitation_url', ''))
    custom_message = invitation.get('custom_message', '')
    custom_message_escaped = escape(custom_message) if custom_message else ''
    unique_token = invitation.get('unique_token', '')
    
    # Get the backend API base URL
    backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000').rstrip('/')
    
    # Build tracking URLs for acknowledge/decline buttons
    # These will hit the backend endpoints which will redirect to the frontend
    acknowledgment_url = f"{backend_api_url}/api/tprm/v1/rfi-invitations/{unique_token}/acknowledge/"
    decline_url = f"{backend_api_url}/api/tprm/v1/rfi-invitations/{unique_token}/decline/"
    
    # Get the external base URL for proper links
    import re
    external_base_url = getattr(settings, 'EXTERNAL_BASE_URL', 'http://localhost:3000').rstrip('/')
    
    # Replace any ngrok URLs with localhost:3000
    if 'ngrok' in external_base_url.lower():
        external_base_url = 'http://localhost:3000'
    
    # Ensure it's localhost (not 127.0.0.1 or other variations)
    if not external_base_url.startswith('http://localhost') and not external_base_url.startswith('https://localhost'):
        # Extract port if present, otherwise use 3000
        port_match = re.search(r':(\d+)', external_base_url)
        port = port_match.group(1) if port_match else '3000'
        external_base_url = f'http://localhost:{port}'
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RFI Invitation</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 300;
        }}
        .content {{
            padding: 30px;
        }}
        .greeting {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #2c3e50;
        }}
        .section {{
            margin: 25px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #4f46e5;
        }}
        .section h2 {{
            color: #2c3e50;
            margin-top: 0;
            font-size: 20px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 15px 0;
        }}
        .info-item {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e9ecef;
        }}
        .info-label {{
            font-weight: bold;
            color: #495057;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        .info-value {{
            color: #2c3e50;
            font-size: 16px;
        }}
        .cta-buttons {{
            text-align: center;
            margin: 30px 0;
        }}
        .btn {{
            display: inline-block;
            padding: 15px 30px;
            margin: 10px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: 16px;
            transition: all 0.3s ease;
        }}
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        .btn-danger {{
            background: #dc3545;
            color: white;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .timeline {{
            background: #e0e7ff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .timeline-item {{
            display: flex;
            align-items: center;
            margin: 10px 0;
        }}
        .timeline-icon {{
            width: 20px;
            height: 20px;
            background: #4f46e5;
            border-radius: 50%;
            margin-right: 15px;
            flex-shrink: 0;
        }}
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .footer a {{
            color: #74b9ff;
            text-decoration: none;
        }}
        .security-notice {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .emoji {{
            font-size: 20px;
            margin-right: 8px;
        }}
        @media (max-width: 600px) {{
            .info-grid {{
                grid-template-columns: 1fr;
            }}
            .btn {{
                display: block;
                margin: 10px 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 RFI Invitation</h1>
            <p>Request for Information - Third-Party Risk Management System</p>
        </div>
        
        <div class="content">
            <div class="greeting">
                Dear {vendor_name},
            </div>
            
            <p>We are pleased to extend a formal invitation for you to participate in our Request for Information (RFI) process. Your organization's expertise and capabilities make you an ideal candidate for this information gathering phase.</p>
            
            <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color: white; padding: 25px; border-radius: 10px; margin: 25px 0; text-align: center;">
                <h2 style="margin: 0 0 15px 0; color: white; font-size: 24px;">🚀 Quick Access to Vendor Portal</h2>
                <p style="margin: 0 0 20px 0; font-size: 16px; opacity: 0.9;">Click the button below to access your personalized vendor portal immediately</p>
                <a href="{invitation_url}" style="display: inline-block; background: white; color: #4f46e5; padding: 15px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 18px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: all 0.3s ease;">Access Vendor Portal</a>
                <p style="margin: 15px 0 0 0; font-size: 14px; opacity: 0.8;">Direct link: <span style="word-break: break-all;">{invitation_url}</span></p>
            </div>
            
            <div class="section">
                <h2><span class="emoji">💼</span>Why You Were Selected</h2>
                <ul>
                    <li>Your organization demonstrates exceptional expertise in the required domain</li>
                    <li>Proven track record of successful project delivery and client satisfaction</li>
                    <li>Strong alignment with our company values and business objectives</li>
                    <li>Competitive offerings and innovative solutions approach</li>
                </ul>
            </div>
            
            <div class="section">
                <h2><span class="emoji">📋</span>RFI Information</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Title</div>
                        <div class="info-value">{escape(str(rfi_data.get('rfi_title', 'Untitled RFI')))}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">RFI Number</div>
                        <div class="info-value">{escape(str(rfi_data.get('rfi_number', 'N/A')))}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Deadline</div>
                        <div class="info-value">{deadline}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Company</div>
                        <div class="info-value">{company_name}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Contact</div>
                        <div class="info-value">{vendor_name} ({vendor_email})</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Type</div>
                        <div class="info-value">{escape(str(rfi_data.get('rfi_type', 'General')))}</div>
                    </div>
                </div>
            </div>
            
            {f'<div class="section"><h2><span class="emoji">📝</span>Additional Message</h2><p>{custom_message_escaped}</p></div>' if custom_message_escaped else ''}
            
            <div class="section">
                <h2><span class="emoji">📋</span>Information Required</h2>
                <div class="timeline">
                    <div class="timeline-item">
                        <div class="timeline-icon"></div>
                        <div><strong>Company Information & Background</strong></div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-icon"></div>
                        <div><strong>Product & Service Capabilities</strong></div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-icon"></div>
                        <div><strong>Technology Stack & Integration</strong></div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-icon"></div>
                        <div><strong>Risk & Compliance Information</strong></div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-icon"></div>
                        <div><strong>Legal Terms & Conditions</strong></div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2><span class="emoji">⏰</span>Timeline</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Information submission</div>
                        <div class="info-value">{deadline}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Review period</div>
                        <div class="info-value">1-2 weeks</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Vendor clarifications</div>
                        <div class="info-value">TBD</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Next steps</div>
                        <div class="info-value">TBD</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2><span class="emoji">🔗</span>Your Unique Invitation Link</h2>
                <div style="background: #e0e7ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4f46e5;">
                    <p style="margin: 0 0 15px 0; font-weight: bold; color: #4338ca;">Access your personalized vendor portal:</p>
                    <div style="background: white; padding: 15px; border-radius: 6px; border: 1px solid #c7d2fe; word-break: break-all;">
                        <a href="{invitation_url}" style="color: #4338ca; text-decoration: none; font-weight: bold; font-size: 16px;">{invitation_url}</a>
                    </div>
                    <p style="margin: 15px 0 0 0; font-size: 14px; color: #666;">This link is unique to your company and will pre-fill your information. Click to access the vendor portal directly.</p>
                </div>
            </div>
            
            <div class="section">
                <h2><span class="emoji">📧</span>Response Required</h2>
                <p>Please respond to this invitation by selecting one of the options below. Your response will be automatically tracked in our system to ensure proper follow-up and communication.</p>
                
                <div class="cta-buttons" style="text-align: center; margin: 30px 0;">
                    <a href="{acknowledgment_url}" class="btn btn-success" style="display: inline-block; padding: 15px 30px; margin: 10px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; background: #28a745; color: white; transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">✅ Acknowledge</a>
                    <a href="{decline_url}" class="btn btn-danger" style="display: inline-block; padding: 15px 30px; margin: 10px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; background: #dc3545; color: white; transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">❌ Decline</a>
                </div>
                
                <p><strong>Response Tracking:</strong> Your response will be automatically tracked in our system. If you acknowledge, you'll receive immediate access to the vendor portal with detailed RFI requirements and submission guidelines.</p>
            </div>
            
            <div class="section">
                <h2><span class="emoji">🎯</span>What Happens Next?</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <h3>If You Accept:</h3>
                        <ul>
                            <li>Immediate portal access</li>
                            <li>Detailed RFI questionnaire</li>
                            <li>Submission guidelines</li>
                            <li>Direct communication channel</li>
                        </ul>
                    </div>
                    <div class="info-item">
                        <h3>If You Decline:</h3>
                        <ul>
                            <li>No further communication</li>
                            <li>Future opportunity notifications</li>
                            <li>Relationship maintained</li>
                            <li>Feedback welcome</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2><span class="emoji">📞</span>Support & Contact Information</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <h3>🆘 Technical Support</h3>
                        <p>Email: support@company.com<br>
                        Phone: +1 (555) 123-4567<br>
                        Hours: 24/7 availability<br>
                        Portal: Live chat support</p>
                    </div>
                    <div class="info-item">
                        <h3>👥 Project Team</h3>
                        <p>Project Manager: John Smith<br>
                        Technical Lead: Jane Doe<br>
                        Procurement: Mike Johnson<br>
                        Email: rfi@company.com</p>
                    </div>
                </div>
            </div>
            
            <div class="security-notice">
                <h3><span class="emoji">🔒</span>Security & Confidentiality</h3>
                <p>All submitted information is treated as confidential and proprietary. Secure data transmission using industry-standard encryption. Access controls and audit trails for all system interactions. Compliance with GDPR, SOC 2, and other security standards.</p>
            </div>
        </div>
        
        <div class="footer">
            <h3>TPRM Management System</h3>
            <p>Thank you for your interest in partnering with us.</p>
            <p>We look forward to your response and potential collaboration.</p>
            
            <p>
                <span class="emoji">📧</span> Email: rfi@company.com |
                <span class="emoji">🌐</span> Website: www.company.com |
                <span class="emoji">📱</span> Portal: {external_base_url}
            </p>
            
            <p><em>This is an automated message. Please do not reply to this email.<br>
            For support, contact us through the vendor portal or your designated account manager.</em></p>
            
            <p><strong>Company Information:</strong><br>
            Third-Party Risk Management System | Enterprise Solutions Division<br>
            Address: 123 Business Street, Suite 100, City, State 12345<br>
            Phone: +1 (555) 123-4567 | Fax: +1 (555) 123-4568</p>
        </div>
    </div>
</body>
</html>
    """.strip()
