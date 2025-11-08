import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.smtp_from = settings.smtp_from
    
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False):
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_from
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_processing_complete_notification(self, to_email: str, recording_name: str, score: int):
        """Send notification when recording processing is complete"""
        subject = f"Recording Processing Complete: {recording_name}"
        body = f"""
Your recording "{recording_name}" has been processed successfully.

Overall Score: {score}/100

View the full evaluation results in your dashboard.
"""
        return self.send_email(to_email, subject, body)
    
    def send_processing_failed_notification(self, to_email: str, recording_name: str, error_message: str):
        """Send notification when recording processing fails"""
        subject = f"Recording Processing Failed: {recording_name}"
        body = f"""
Your recording "{recording_name}" failed to process.

Error: {error_message}

Please check the recording file and try again.
"""
        return self.send_email(to_email, subject, body)

