"""
Mail Services Package
"""

from .email_service import EmailService, ManagementEmailService
from .imap_service import ImapService

__all__ = ['EmailService', 'ManagementEmailService', 'ImapService']
