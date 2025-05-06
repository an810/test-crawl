import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        # This line retrieves the SMTP server address from environment variables, defaulting to 'smtp.gmail.com' if not set.
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        
        # This line retrieves the SMTP server port from environment variables, defaulting to 587, which is typically used for TLS connections.
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # This line retrieves the sender's email address from environment variables. It is required for sending emails.
        self.sender_email = os.getenv('SENDER_EMAIL')
        
        # This line retrieves the sender's email password from environment variables.
        # For Gmail, this must be an App Password, not your regular Gmail password.
        self.sender_password = os.getenv('SENDER_PASSWORD')
        
        # Debug logging
        print("\nEmail Configuration:")
        print(f"SMTP Server: {self.smtp_server}")
        print(f"SMTP Port: {self.smtp_port}")
        print(f"Sender Email: {self.sender_email}")
        print(f"Password configured: {'Yes' if self.sender_password else 'No'}")
        
        if not self.sender_email or not self.sender_password:
            print("\nERROR: Email or password not configured!")
            print("Please create a .env file with the following variables:")
            print("SENDER_EMAIL=your-email@gmail.com")
            print("SENDER_PASSWORD=your-app-password")
            print("\nFor Gmail, you need to use an App Password:")
            print("1. Go to your Google Account settings")
            print("2. Enable 2-Step Verification if not already enabled")
            print("3. Go to Security → App passwords")
            print("4. Generate a new app password for 'Mail'")
            print("5. Use this generated password in your .env file\n")

    def send_emails(self, 
                   recipient_emails: List[str], 
                   subject: str, 
                   body: str, 
                   is_html: bool = False) -> dict:
        """
        Send emails to multiple recipients
        
        Args:
            recipient_emails (List[str]): List of recipient email addresses
            subject (str): Email subject
            body (str): Email body content
            is_html (bool): Whether the body content is HTML
            
        Returns:
            dict: Status of the email sending operation
        """
        try:
            if not self.sender_email or not self.sender_password:
                raise ValueError("Email or password not configured. Please check your .env file.")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['Subject'] = subject

            # Attach body
            content_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, content_type))

            # Connect to SMTP server
            print(f"Connecting to {self.smtp_server}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                print("Starting TLS...")
                server.starttls()
                print("Attempting login...")
                server.login(self.sender_email, self.sender_password)
                print("Login successful!")

                # Send email to each recipient
                for recipient in recipient_emails:
                    msg['To'] = recipient
                    server.send_message(msg)
                    print(f"Email sent successfully to {recipient}")

            return {
                "status": "success",
                "message": f"Emails sent successfully to {len(recipient_emails)} recipients",
                "recipients": recipient_emails
            }

        except smtplib.SMTPAuthenticationError as e:
            error_msg = "Gmail authentication failed. Please make sure you're using an App Password, not your regular Gmail password."
            print(f"\nDetailed error: {error_msg}")
            print("Visit: https://support.google.com/mail/?p=BadCredentials for more information")
            return {
                "status": "error",
                "message": error_msg,
                "recipients": recipient_emails
            }
        except Exception as e:
            error_msg = str(e)
            print(f"\nDetailed error: {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "recipients": recipient_emails
            } 