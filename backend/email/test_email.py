import os
from email_service import EmailService
from dotenv import load_dotenv

def test_send_email():
    # Load environment variables
    load_dotenv()
    
    # Initialize email service
    email_service = EmailService()
    
    # Test email configuration
    test_recipients = [
        os.getenv('TEST_RECIPIENT_EMAIL', 'antp9254@gmail.com')  # Replace with your test email
    ]
    test_subject = "Test Email from Python Service"
    test_body = """
    Hello!
    
    This is a test email sent from the Python email service.
    
    If you're receiving this email, the service is working correctly!
    
    Best regards,
    Your Email Service
    """
    
    # Send test email
    print("Sending test email...")
    result = email_service.send_emails(
        recipient_emails=test_recipients,
        subject=test_subject,
        body=test_body,
        is_html=False
    )
    
    # Print result
    print("\nEmail sending result:")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Recipients: {result['recipients']}")

def test_send_html_email():
    # Load environment variables
    load_dotenv()
    
    # Initialize email service
    email_service = EmailService()
    
    # Test email configuration
    test_recipients = [
        os.getenv('TEST_RECIPIENT_EMAIL', 'antp925@gmail.com')  # Replace with your test email
    ]
    test_subject = "Test HTML Email from Python Service"
    test_html_body = """
    <html>
        <body>
            <h1>HUST Real Estate</h1>
            <p>Dear Mr. Hai Do Hong,</p>
            <p>We hope this message finds you well. At HUST Real Estate, we wish you a wonderful day filled with success and happiness.</p>
            <p>Thank you for choosing us for your real estate needs.</p>
            <hr>
            <p><em>Best regards,<br>HUST Real Estate Service</em></p>
        </body>
    </html>
    """
    
    # Send test HTML email
    print("\nSending test HTML email...")
    result = email_service.send_emails(
        recipient_emails=test_recipients,
        subject=test_subject,
        body=test_html_body,
        is_html=True
    )
    
    # Print result
    print("\nHTML Email sending result:")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Recipients: {result['recipients']}")

if __name__ == "__main__":
    print("Starting email tests...")
    print("=" * 50)
    
    try:
        # Test plain text email
        # test_send_email()
        
        # Test HTML email
        test_send_html_email()
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
    
    print("\nEmail tests completed!") 