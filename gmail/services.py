"""
Gmail service for fetching and processing emails
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import base64
import re

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from accounts.models import GoogleAccount
from accounts.utils import refresh_google_tokens
from gmail.models import Email
from applications.models import Application


class GmailService:
    """Service for interacting with Gmail API"""
    
    def __init__(self, user):
        self.user = user
        self.google_account = user.google_account
        self.service = self._get_gmail_service()
    
    def _get_gmail_service(self):
        """Get authenticated Gmail service instance"""
        # Create credentials from stored tokens
        credentials = Credentials(
            token=self.google_account.access_token,
            refresh_token=self.google_account.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        
        # Refresh token if expired
        if self.google_account.token_expiry <= timezone.now():
            refresh_google_tokens(self.google_account)
            # Re-create credentials with new token
            credentials = Credentials(
                token=self.google_account.access_token,
                refresh_token=self.google_account.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
            )
        
        # Build Gmail service
        return build('gmail', 'v1', credentials=credentials)
    
    def fetch_recent_emails(self, days_back: int = 7, max_results: int = 100) -> List[Dict]:
        """
        Fetch recent emails from Gmail
        
        Args:
            days_back: Number of days to look back
            max_results: Maximum number of emails to fetch
            
        Returns:
            List of email dictionaries
        """
        # Calculate date for query
        after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        
        # Build query - look for job-related keywords
        job_keywords = [
            'job', 'position', 'opportunity', 'hiring', 'recruitment',
            'application', 'interview', 'offer', 'reject', 'candidate'
        ]
        query_parts = [f'"{keyword}"' for keyword in job_keywords]
        query = f"({' OR '.join(query_parts)}) after:{after_date}"
        
        try:
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = self._fetch_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            return []
    
    def _fetch_email_details(self, message_id: str) -> Optional[Dict]:
        """Fetch detailed information for a single email"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()
            
            # Extract headers
            headers = message['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            # Parse email data
            email_data = {
                'gmail_id': message['id'],
                'thread_id': message['threadId'],
                'subject': header_dict.get('Subject', ''),
                'sender': header_dict.get('From', ''),
                'recipient': header_dict.get('To', ''),
                'date': header_dict.get('Date', ''),
                'body_text': body.get('text', ''),
                'body_html': body.get('html', ''),
                'labels': message.get('labelIds', []),
                'snippet': message.get('snippet', ''),
            }
            
            # Extract sender email
            sender_match = re.search(r'<(.+?)>', email_data['sender'])
            if sender_match:
                email_data['sender_email'] = sender_match.group(1)
            else:
                email_data['sender_email'] = email_data['sender']
            
            return email_data
            
        except Exception as e:
            print(f"Error fetching email details for {message_id}: {str(e)}")
            return None
    
    def _extract_body(self, payload: Dict) -> Dict[str, str]:
        """Extract text and HTML body from email payload"""
        body = {'text': '', 'html': ''}
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body['text'] = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    body['html'] = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif 'parts' in part:
                    # Recursive call for nested parts
                    nested_body = self._extract_body(part)
                    body['text'] = body['text'] or nested_body['text']
                    body['html'] = body['html'] or nested_body['html']
        else:
            # Simple message
            if payload['body'].get('data'):
                data = payload['body']['data']
                if payload['mimeType'] == 'text/plain':
                    body['text'] = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif payload['mimeType'] == 'text/html':
                    body['html'] = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body
    
    @transaction.atomic
    def save_emails_to_db(self, emails: List[Dict]) -> int:
        """
        Save fetched emails to database
        
        Returns:
            Number of new emails saved
        """
        saved_count = 0
        
        for email_data in emails:
            # Check if email already exists
            if Email.objects.filter(
                user=self.user,
                gmail_id=email_data['gmail_id']
            ).exists():
                continue
            
            # Create email record
            email = Email.objects.create(
                user=self.user,
                gmail_id=email_data['gmail_id'],
                thread_id=email_data['thread_id'],
                subject=email_data['subject'],
                sender=email_data['sender'],
                sender_email=email_data['sender_email'],
                recipient=email_data['recipient'],
                date_received=self._parse_date(email_data['date']),
                body_text=email_data['body_text'],
                body_html=email_data['body_html'],
                raw_data={'labels': email_data['labels'], 'snippet': email_data['snippet']}
            )
            
            saved_count += 1
        
        return saved_count
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date string to datetime"""
        from email.utils import parsedate_to_datetime
        try:
            return parsedate_to_datetime(date_str)
        except:
            return timezone.now()
    
    def mark_as_read(self, message_id: str):
        """Mark an email as read in Gmail"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except Exception as e:
            print(f"Error marking email as read: {str(e)}")
    
    def add_label(self, message_id: str, label_name: str):
        """Add a label to an email in Gmail"""
        try:
            # First, get or create the label
            label_id = self._get_or_create_label(label_name)
            
            # Then add it to the message
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()
        except Exception as e:
            print(f"Error adding label: {str(e)}")
    
    def _get_or_create_label(self, label_name: str) -> str:
        """Get label ID, creating it if necessary"""
        try:
            # List all labels
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Check if label exists
            for label in labels:
                if label['name'] == label_name:
                    return label['id']
            
            # Create new label
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            created_label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            
            return created_label['id']
            
        except Exception as e:
            print(f"Error with label: {str(e)}")
            return None