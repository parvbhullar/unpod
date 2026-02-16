import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unpod.channels.services import GoogleService
# from base import EmailProcessorBase

class Email:
    """Base class to handle email processing tasks."""

    def __init__(self, creds_file):
        self.creds_file = creds_file
        self.google_service = GoogleService(creds_file)

    def create_reply_message(self, to, message_id, body_text):
        """Create an automated reply message."""
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = 'Re: ' + body_text[:50]
        message['In-Reply-To'] = message_id
        message['References'] = message_id

        msg_body = MIMEText('This is an automated response to your email.\n\n' + body_text, 'plain')
        message.attach(msg_body)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return raw_message

    def send_reply(self, message_id, to, body_text):
        """Send a reply to the email."""
        raw_message = self.create_reply_message(to, message_id, body_text)
        try:
            message = self.google_service.service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            print(f"Message sent to {to} with ID: {message['id']}")
        except Exception as error:
            print(f'An error occurred while sending the email: {error}')

    def list_messages(self):
        """List the emails from the Gmail account."""
        print("Fetching email list...")
        try:
            # Fetch user details
            user_info = self.google_service.get_user_info()

            # Fetch email list
            email_list = self.google_service.list_messages()

            # Include user info in the response
            response = {
                "stateCode": 200,
                "user": {
                    "email": user_info['emailAddress'],  # User's email address
                    "name": user_info.get('name', 'N/A')  # User's name, if available
                },
                "emails": email_list
            }

            return response
        except Exception as error:
            print(f'An unexpected error occurred: {error}')
            return {"stateCode": 500, "message": str(error)} 