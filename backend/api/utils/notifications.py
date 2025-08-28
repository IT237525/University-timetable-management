from django.core.mail import send_mail
from django.conf import settings


def send_email_notification(subject: str, message: str, recipient_list: list) -> None:
    """Send best-effort email notification. Swallows exceptions.

    Args:
        subject: Email subject
        message: Plain text body
        recipient_list: List of recipient email addresses
    """
    if not recipient_list:
        return
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@northernuni.local',
            recipient_list=recipient_list,
            fail_silently=True,
        )
    except Exception:
        # Best-effort; ignore failures
        pass


