# ==========================================
# EMAIL UTILITIES
# ==========================================

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

def send_notification_email(subject, message, recipients):
    """
    Send email notification to multiple recipients
    """
    if not recipients:
        print("⚠️ No recipients provided")
        return False
    
    print(f"📧 Sending to {len(recipients)} recipients...")
    
    try:
        # Connect to Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(Config.GMAIL_EMAIL, Config.GMAIL_APP_PASSWORD)
        
        # Send to each recipient individually
        success_count = 0
        for i, email in enumerate(recipients):
            try:
                # Create a NEW message for each recipient
                msg = MIMEMultipart()
                msg["From"] = Config.GMAIL_EMAIL
                msg["To"] = email
                msg["Subject"] = subject
                msg.attach(MIMEText(message, "html"))
                
                server.sendmail(Config.GMAIL_EMAIL, email, msg.as_string())
                success_count += 1
                print(f"  ✅ Sent to: {email}")
                
                # Small delay between emails
                if i < len(recipients) - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"  ❌ Failed to send to {email}: {e}")
        
        server.quit()
        print(f"✅ Emails sent successfully to {success_count} of {len(recipients)} recipients")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def format_notification_email(subject, message, sender_name, sender_role):
    """
    Format notification email as HTML
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: #6366f1; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
            .content {{ padding: 20px; }}
            .footer {{ margin-top: 20px; color: #666; font-size: 12px; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📢 {subject}</h2>
            </div>
            <div class="content">
                <p><strong>From:</strong> {sender_name} ({sender_role})</p>
                <hr>
                <p>{message}</p>
                <hr>
                <p><small>This is an automated notification from the Student Monitoring System.</small></p>
            </div>
            <div class="footer">
                <p>© 2026 Student Monitoring System</p>
            </div>
        </div>
    </body>
    </html>
    """