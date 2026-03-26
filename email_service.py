# email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Force load .env file
load_dotenv(override=True)

class EmailService:
    def __init__(self):
        # Debug: Print what we're loading
        print("🔧 Loading SMTP Configuration...")
        
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@digitalhoarding.com")
        self.from_name = os.getenv("SMTP_FROM_NAME", "Digital Hoarding Punger")
        
        # Debug: Check if config is loaded
        if self.smtp_host and self.smtp_user and self.smtp_password:
            print(f"✅ SMTP Configured: {self.smtp_host}:{self.smtp_port}")
            print(f"   User: {self.smtp_user}")
            print(f"   From: {self.from_name} <{self.from_email}>")
        else:
            print("⚠️ SMTP NOT Configured - Missing credentials")
            print(f"   HOST: {self.smtp_host}")
            print(f"   USER: {self.smtp_user}")
            print(f"   PASSWORD: {'SET' if self.smtp_password else 'MISSING'}")
    
    def send_email(self, to_email, subject, html_content):
        """Send email using SMTP (Brevo)"""
        try:
            # Check if SMTP is configured
            if not self.smtp_host or not self.smtp_user or not self.smtp_password:
                print(f"\n⚠️ SMTP not configured. Would send email to: {to_email}")
                print(f"Subject: {subject}")
                print(f"Content preview: {html_content[:200]}...")
                print("To enable email, add SMTP credentials to .env file\n")
                return True
            
            print(f"\n📧 Attempting to send email to {to_email}...")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication Failed: {e}")
            print("   Check your SMTP_USER and SMTP_PASSWORD in .env file")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def send_verification_email(self, to_email, name, otp):
        """Send email verification OTP"""
        subject = "Verify Your Email - Digital Hoarding Punger"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px;
                    text-align: center;
                    color: white;
                    border-radius: 12px 12px 0 0;
                    margin: -20px -20px 0 -20px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    padding: 30px 20px;
                }}
                .greeting {{
                    font-size: 18px;
                    margin-bottom: 20px;
                    color: #333;
                }}
                .otp-code {{
                    font-size: 40px;
                    font-weight: bold;
                    text-align: center;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 12px;
                    letter-spacing: 8px;
                    margin: 20px 0;
                    font-family: monospace;
                }}
                .message {{
                    color: #666;
                    line-height: 1.6;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #999;
                    font-size: 12px;
                    border-top: 1px solid #eee;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📸 Digital Hoarding Punger</h1>
                </div>
                <div class="content">
                    <div class="greeting">Hello <strong>{name}</strong>!</div>
                    <div class="message">
                        Thank you for signing up! Please verify your email address by entering the code below:
                    </div>
                    <div class="otp-code">
                        {otp}
                    </div>
                    <div class="message">
                        This code is valid for <strong>10 minutes</strong>.<br>
                        If you didn't request this, please ignore this email.
                    </div>
                </div>
                <div class="footer">
                    <p>Digital Hoarding Punger - Clean up your digital life with AI</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_welcome_email(self, to_email, name):
        """Send welcome email after verification"""
        subject = "Welcome to Digital Hoarding Punger! 🎉"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Welcome!</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 12px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px;
                    text-align: center;
                    color: white;
                    border-radius: 12px 12px 0 0;
                    margin: -20px -20px 0 -20px;
                }}
                .content {{
                    padding: 30px 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .feature-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }}
                .feature {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #999;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome Aboard!</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{name}</strong>!</p>
                    <p>Your email has been verified successfully. You're now ready to start cleaning up your digital clutter!</p>
                    <div class="feature-grid">
                        <div class="feature">📸 Upload Photos</div>
                        <div class="feature">🤖 AI Analysis</div>
                        <div class="feature">🗑️ Smart Cleanup</div>
                        <div class="feature">📊 Track Progress</div>
                    </div>
                    <div style="text-align: center;">
                        <a href="http://localhost:5000/dashboard" class="button">Go to Dashboard</a>
                    </div>
                </div>
                <div class="footer">
                    <p>Digital Hoarding Punger - Clean up your digital life</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_monthly_report(self, to_email, name, stats):
        """Send monthly cleanup report email"""
        subject = "📊 Your Monthly Digital Hoarding Report"
        
        # Calculate cleanup rate
        cleanup_rate = (stats['deleted'] / stats['total_uploaded'] * 100) if stats['total_uploaded'] > 0 else 0
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Monthly Report</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px;
                    text-align: center;
                    color: white;
                    border-radius: 12px 12px 0 0;
                    margin: -20px -20px 0 -20px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .header p {{
                    margin: 10px 0 0;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 30px 20px;
                }}
                .greeting {{
                    font-size: 18px;
                    margin-bottom: 20px;
                    color: #333;
                }}
                .stats-container {{
                    background: #f8f9fa;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .stat-row {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 0;
                    border-bottom: 1px solid #e0e0e0;
                }}
                .stat-row:last-child {{
                    border-bottom: none;
                }}
                .stat-label {{
                    font-size: 14px;
                    color: #666;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .stat-value {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #667eea;
                }}
                .cleanup-rate {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 20px 0;
                }}
                .cleanup-rate .rate-value {{
                    font-size: 36px;
                    font-weight: bold;
                    display: block;
                }}
                .message-box {{
                    background: #e8f5e9;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #4caf50;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .button-container {{
                    text-align: center;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #999;
                    font-size: 12px;
                    border-top: 1px solid #eee;
                }}
                .emoji {{
                    font-size: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📸 Digital Hoarding Punger</h1>
                    <p>Your Monthly Cleanup Report</p>
                </div>
                <div class="content">
                    <div class="greeting">
                        Hello <strong>{name}</strong>! 
                    </div>
                    
                    <p>Here's your digital cleanup summary for this month:</p>
                    
                    <div class="stats-container">
                        <div class="stat-row">
                            <div class="stat-label">
                                <span class="emoji">📸</span> Total Images Uploaded
                            </div>
                            <div class="stat-value">{stats['total_uploaded']}</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">
                                <span class="emoji">⚠️</span> Flagged for Cleanup
                            </div>
                            <div class="stat-value">{stats['flagged']}</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">
                                <span class="emoji">🗑️</span> Images Deleted
                            </div>
                            <div class="stat-value">{stats['deleted']}</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">
                                <span class="emoji">🔄</span> Images Recovered
                            </div>
                            <div class="stat-value">{stats['recovered']}</div>
                        </div>
                        <div class="stat-row">
                            <div class="stat-label">
                                <span class="emoji">✨</span> Still in Gallery
                            </div>
                            <div class="stat-value">{stats['remaining']}</div>
                        </div>
                    </div>
                    
                    <div class="cleanup-rate">
                        <span class="rate-value">{cleanup_rate:.1f}%</span>
                        Cleanup Rate This Month
                    </div>
                    
                    {self._get_motivational_message(cleanup_rate, stats['flagged'])}
                    
                    <div class="button-container">
                        <a href="http://localhost:5000/dashboard" class="button">
                            🚀 Go to Dashboard & Clean Up More
                        </a>
                    </div>
                    
                    <div class="message-box">
                        <strong>💡 Pro Tip:</strong> Regular cleanup helps you find your best photos faster! 
                        Try to review flagged images weekly to keep your gallery organized.
                    </div>
                </div>
                <div class="footer">
                    <p>You're receiving this monthly report because you're a Digital Hoarding Punger user.</p>
                    <p>Keep your digital life clean! 🧹</p>
                    <p>&copy; 2024 Digital Hoarding Punger</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def _get_motivational_message(self, cleanup_rate, flagged_count):
        """Generate motivational message based on user's cleanup activity"""
        if cleanup_rate >= 80:
            return """
            <div class="message-box" style="background: #fff3e0; border-left-color: #ff9800;">
                <strong>🏆 Outstanding!</strong> You've cleaned up over 80% of your flagged images this month! 
                You're a digital hoarding champion! Keep up the amazing work!
            </div>
            """
        elif cleanup_rate >= 50:
            return """
            <div class="message-box" style="background: #e3f2fd; border-left-color: #2196f3;">
                <strong>👍 Great Progress!</strong> You've cleaned up more than half of your flagged images. 
                You're on the right track to a clutter-free gallery!
            </div>
            """
        elif cleanup_rate >= 20:
            return """
            <div class="message-box" style="background: #f3e5f5; border-left-color: #9c27b0;">
                <strong>📈 Good Start!</strong> You've begun your cleanup journey. Every deleted image counts! 
                Keep going and you'll see even better results next month.
            </div>
            """
        elif flagged_count > 0:
            return """
            <div class="message-box" style="background: #ffebee; border-left-color: #f44336;">
                <strong>🎯 Time to Clean!</strong> You have {flagged_count} flagged images waiting for review. 
                Take a few minutes to clean them up - your future self will thank you!
            </div>
            """.format(flagged_count=flagged_count)
        else:
            return """
            <div class="message-box" style="background: #e8f5e9; border-left-color: #4caf50;">
                <strong>✨ Clean Gallery!</strong> No flagged images this month! You're doing an excellent job 
                keeping your digital space organized!
            </div>
            """
    
    def send_cleanup_reminder(self, to_email, name, flagged_count):
        """Send a reminder email when user has flagged images waiting"""
        subject = "⏰ Cleanup Reminder - You Have Images Waiting!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Cleanup Reminder</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 12px;
                }}
                .header {{
                    background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
                    padding: 30px;
                    text-align: center;
                    color: white;
                    border-radius: 12px 12px 0 0;
                    margin: -20px -20px 0 -20px;
                }}
                .content {{
                    padding: 30px 20px;
                }}
                .flagged-count {{
                    font-size: 48px;
                    font-weight: bold;
                    text-align: center;
                    color: #ff9800;
                    margin: 20px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #999;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ Time to Clean!</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{name}</strong>!</p>
                    <p>You have <strong>{flagged_count}</strong> images waiting for cleanup:</p>
                    <div class="flagged-count">{flagged_count}</div>
                    <p>These images have been identified as potential clutter (blurry photos, memes, or screenshots). 
                    Taking a few minutes to review them will help keep your gallery organized!</p>
                    <div style="text-align: center;">
                        <a href="http://localhost:5000/dashboard" class="button">
                            🧹 Review & Clean Up Now
                        </a>
                    </div>
                </div>
                <div class="footer">
                    <p>Digital Hoarding Punger - Helping you maintain a clean digital life</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)


# Create a singleton instance
email_service = EmailService()