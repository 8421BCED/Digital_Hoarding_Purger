#!/usr/bin/env python3
"""
Professional Monthly Report Email Script
Send a clean, professional monthly report email
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Email Configuration (from your .env)
#here some data will be come and its in te w

# Recipient email
DEMO_EMAIL = "longlivequeen25@gmail.com"
DEMO_NAME = "User"

# Sample cleanup stats for demo
stats = {
    'total_uploaded': 15,
    'flagged_blur': 1,
    'flagged_meme': 1,
    'flagged_screenshot': 3,
    'flagged_nsfw': 5,
    'deleted': 4,
    'recovered': 1,
    'remaining': 11
}

# Calculate cleanup rate
total_flagged = stats['flagged_blur'] + stats['flagged_meme'] + stats['flagged_screenshot'] + stats['flagged_nsfw']
cleanup_rate = (stats['deleted'] / total_flagged * 100) if total_flagged > 0 else 0

def send_monthly_report_email():
    """Send a professional monthly report email"""
    
    subject = f"Digital Hoarding Report - {datetime.now().strftime('%B %Y')}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Digital Hoarding Report</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                overflow: hidden;
            }}
            .header {{
                background: #1a1a2e;
                padding: 32px;
                text-align: center;
                border-bottom: 3px solid #667eea;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                color: #ffffff;
                font-weight: 600;
                letter-spacing: -0.3px;
            }}
            .header p {{
                margin: 8px 0 0;
                color: #a0a0a0;
                font-size: 13px;
            }}
            .content {{
                padding: 32px;
            }}
            .greeting {{
                font-size: 18px;
                margin-bottom: 24px;
                color: #1a1a2e;
                font-weight: 500;
            }}
            .greeting strong {{
                color: #667eea;
            }}
            .stats-container {{
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                margin: 24px 0;
                border: 1px solid #e9ecef;
            }}
            .stat-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 0;
                border-bottom: 1px solid #e9ecef;
            }}
            .stat-row:last-child {{
                border-bottom: none;
            }}
            .stat-label {{
                font-size: 14px;
                color: #6c757d;
                font-weight: 500;
            }}
            .stat-value {{
                font-size: 20px;
                font-weight: 700;
                color: #1a1a2e;
            }}
            .stat-value.primary {{
                color: #667eea;
            }}
            .category-breakdown {{
                margin: 24px 0;
                background: #ffffff;
                border-radius: 8px;
                border: 1px solid #e9ecef;
                overflow: hidden;
            }}
            .category-header {{
                background: #f8f9fa;
                padding: 12px 20px;
                font-weight: 600;
                color: #1a1a2e;
                border-bottom: 1px solid #e9ecef;
            }}
            .category-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 20px;
                border-bottom: 1px solid #f0f0f0;
            }}
            .category-item:last-child {{
                border-bottom: none;
            }}
            .category-name {{
                font-size: 14px;
                color: #495057;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .category-badge {{
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 2px;
                margin-right: 8px;
            }}
            .badge-blur {{ background-color: #ff9800; }}
            .badge-meme {{ background-color: #9c27b0; }}
            .badge-screenshot {{ background-color: #2196f3; }}
            .badge-nsfw {{ background-color: #dc3545; }}
            .category-count {{
                font-weight: 600;
                color: #1a1a2e;
            }}
            .total-flagged {{
                background: #f8f9fa;
                padding: 12px 20px;
                display: flex;
                justify-content: space-between;
                font-weight: 600;
                border-top: 1px solid #e9ecef;
            }}
            .cleanup-rate {{
                background: #667eea;
                color: white;
                padding: 24px;
                border-radius: 8px;
                text-align: center;
                margin: 24px 0;
            }}
            .rate-value {{
                font-size: 42px;
                font-weight: 700;
                display: block;
                margin-bottom: 8px;
            }}
            .progress-bar {{
                background: rgba(255,255,255,0.3);
                border-radius: 20px;
                height: 8px;
                overflow: hidden;
                margin: 16px 0 8px;
            }}
            .progress-fill {{
                background: white;
                width: {cleanup_rate}%;
                height: 100%;
                border-radius: 20px;
            }}
            .message-box {{
                padding: 16px 20px;
                border-radius: 8px;
                margin: 24px 0;
                border-left: 3px solid;
            }}
            .motivation-high {{
                background: #e8f5e9;
                border-left-color: #28a745;
            }}
            .motivation-medium {{
                background: #fff3e0;
                border-left-color: #ff9800;
            }}
            .motivation-low {{
                background: #ffebee;
                border-left-color: #dc3545;
            }}
            .info-box {{
                background: #e3f2fd;
                padding: 16px 20px;
                border-radius: 8px;
                margin: 24px 0;
                border-left: 3px solid #2196f3;
            }}
            .button {{
                display: inline-block;
                padding: 12px 28px;
                background: #1a1a2e;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                margin: 16px 0 8px;
                text-align: center;
                font-weight: 500;
                font-size: 14px;
                transition: background 0.2s;
            }}
            .button:hover {{
                background: #2d2d44;
            }}
            .button-container {{
                text-align: center;
                margin: 24px 0;
            }}
            .footer {{
                text-align: center;
                padding: 24px;
                color: #adb5bd;
                font-size: 12px;
                border-top: 1px solid #e9ecef;
                background: #fafafa;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Digital Hoarding Punger</h1>
                <p>Monthly Cleanup Report</p>
            </div>
            <div class="content">
                <div class="greeting">
                    Dear <strong>{DEMO_NAME}</strong>,
                </div>
                
                <p>Here is your digital cleanup summary for <strong>{datetime.now().strftime('%B %Y')}</strong>.</p>
                
                <div class="stats-container">
                    <div class="stat-row">
                        <div class="stat-label">Total Images Uploaded</div>
                        <div class="stat-value">{stats['total_uploaded']}</div>
                    </div>
                    <div class="stat-row">
                        <div class="stat-label">Images Cleaned</div>
                        <div class="stat-value primary">{stats['deleted']}</div>
                    </div>
                    <div class="stat-row">
                        <div class="stat-label">Images Recovered</div>
                        <div class="stat-value">{stats['recovered']}</div>
                    </div>
                    <div class="stat-row">
                        <div class="stat-label">Currently in Gallery</div>
                        <div class="stat-value">{stats['remaining']}</div>
                    </div>
                </div>
                
                <div class="category-breakdown">
                    <div class="category-header">Flagged Images by Category</div>
                    <div class="category-item">
                        <div class="category-name">
                            <span class="category-badge badge-blur"></span>
                            Blurry Photos
                        </div>
                        <div class="category-count">{stats['flagged_blur']}</div>
                    </div>
                    <div class="category-item">
                        <div class="category-name">
                            <span class="category-badge badge-meme"></span>
                            Memes
                        </div>
                        <div class="category-count">{stats['flagged_meme']}</div>
                    </div>
                    <div class="category-item">
                        <div class="category-name">
                            <span class="category-badge badge-screenshot"></span>
                            Screenshots
                        </div>
                        <div class="category-count">{stats['flagged_screenshot']}</div>
                    </div>
                    <div class="category-item">
                        <div class="category-name">
                            <span class="category-badge badge-nsfw"></span>
                            Offensive Content
                        </div>
                        <div class="category-count">{stats['flagged_nsfw']}</div>
                    </div>
                    <div class="total-flagged">
                        <span>Total Flagged</span>
                        <span style="font-weight: 700;">{total_flagged}</span>
                    </div>
                </div>
                
                <div class="cleanup-rate">
                    <div class="rate-value">{cleanup_rate:.1f}%</div>
                    <div>Cleanup Rate</div>
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <small style="opacity: 0.9;">You cleaned up {stats['deleted']} of {total_flagged} flagged images</small>
                </div>
                
                {get_motivational_message(cleanup_rate, total_flagged, stats)}
                
                <div class="info-box">
                    <strong>Recommendation</strong><br>
                    Regular review of flagged images helps maintain an organized gallery. 
                    Consider reviewing the remaining {total_flagged - stats['deleted']} flagged images this week.
                </div>
                
                <div class="button-container">
                    <a href="http://localhost:5000/dashboard" class="button">
                        Access Dashboard
                    </a>
                </div>
            </div>
            <div class="footer">
                <p>Digital Hoarding Punger — AI-Powered Photo Cleanup Assistant</p>
                <p style="margin-top: 8px;">This report is sent monthly to help you track your digital cleanup progress.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg['To'] = DEMO_EMAIL
        msg.attach(MIMEText(html_content, 'html'))
        
        print(f"\nSending report to {DEMO_EMAIL}...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"Report sent successfully to {DEMO_EMAIL}!")
        print(f"\nReport Summary:")
        print(f"  Total Uploaded: {stats['total_uploaded']}")
        print(f"  Total Flagged: {total_flagged}")
        print(f"  Cleaned: {stats['deleted']}")
        print(f"  Recovered: {stats['recovered']}")
        print(f"  Cleanup Rate: {cleanup_rate:.1f}%")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Failed: {e}")
        print("Check your SMTP credentials")
        return False
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def get_motivational_message(cleanup_rate, total_flagged, stats):
    """Generate professional motivational message"""
    remaining = total_flagged - stats['deleted']
    
    if cleanup_rate >= 80:
        return f"""
        <div class="message-box motivation-high">
            <strong>Excellent Progress</strong><br>
            You have cleaned up {cleanup_rate:.0f}% of flagged images this month. 
            Your digital space is well-maintained. Continue this momentum.
        </div>
        """
    elif cleanup_rate >= 50:
        return f"""
        <div class="message-box motivation-medium">
            <strong>Good Progress</strong><br>
            You have cleaned up {cleanup_rate:.0f}% of flagged images. 
            Review the remaining {remaining} images to complete your cleanup.
        </div>
        """
    elif cleanup_rate >= 20:
        return f"""
        <div class="message-box motivation-medium">
            <strong>Getting Started</strong><br>
            You have cleaned up {cleanup_rate:.0f}% of flagged images. 
            {remaining} images remain flagged for review. A few minutes of cleanup can make a difference.
        </div>
        """
    elif total_flagged > 0:
        return f"""
        <div class="message-box motivation-low">
            <strong>Action Required</strong><br>
            {total_flagged} images are currently flagged for review. 
            Regular cleanup helps maintain an organized gallery. Please review these images.
        </div>
        """
    else:
        return f"""
        <div class="message-box motivation-high">
            <strong>Clean Gallery</strong><br>
            No flagged images this month. Your gallery is well-organized.
        </div>
        """

if __name__ == "__main__":
    print("="*60)
    print("DIGITAL HOARDING PUNGER - MONTHLY REPORT")
    print("="*60)
    
    print(f"\nSending to: {DEMO_EMAIL}")
    print(f"Report Month: {datetime.now().strftime('%B %Y')}")
    print(f"\nData Summary:")
    print(f"  Total Uploaded: {stats['total_uploaded']}")
    print(f"  Blurry: {stats['flagged_blur']}")
    print(f"  Memes: {stats['flagged_meme']}")
    print(f"  Screenshots: {stats['flagged_screenshot']}")
    print(f"  Offensive: {stats['flagged_nsfw']}")
    print(f"  Cleaned: {stats['deleted']}")
    print(f"  Recovered: {stats['recovered']}")
    
    success = send_monthly_report_email()
    
    if success:
        print("\nEmail sent successfully. Check inbox and spam folder.")
    else:
        print("\nFailed to send email. Check SMTP credentials.")