from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.mail import send_mail
from django.conf import settings
from .models import Invitation, TenantUser

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3
)
def send_invite_email(self, token_link, email, tenant_name):
    try:

        message = (
            f"Hello, \n\n"
            f"You have invited to join the {tenant_name} workspace. \n\n"
            f"Here is your {token_link} to join"
        )

        send_mail(
            subject='Workspace Invitation',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email,],
            fail_silently=False
        )

        logger.info(f'Email sent successfully')
        return 'Email Sent Successfully'

    except ConnectionError as exc:
        logger.warning(f"Temporary email provider failure: retrying task_id = %s",
                       self.request.id,)
        raise self.retry(exc=exc, countdown=5)

    except ValueError as exc:
        logger.info('Permanent failure: Inviation failed, no tas_id=%s, error=%s',
                    self.request.id,
                    exc,
                    )

        raise
